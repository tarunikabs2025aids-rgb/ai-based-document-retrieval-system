import os
import hashlib
import logging
import csv
import math
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import DocumentMetadata

logger = logging.getLogger(__name__)

# Check for FAISS and SentenceTransformers imports with fallbacks
HAS_VECTOR_LIBS = False
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    HAS_VECTOR_LIBS = True
    logger.info("Successfully imported FAISS and LangChain vector libraries.")
except ImportError as e:
    logger.warning(f"Vector search libraries not available: {e}. Engaging pure-Python search fallback.")
    # Standard dummy Document class for local search
    class Document:
        def __init__(self, page_content: str, metadata: Dict[str, Any]):
            self.page_content = page_content
            self.metadata = metadata

# Check for Pandas import with fallback
HAS_PANDAS = False
try:
    import pandas as pd
    HAS_PANDAS = True
    logger.info("Successfully imported Pandas.")
except ImportError:
    logger.warning("Pandas not available. Engaging standard library CSV module fallback.")

_embeddings = None

def get_embeddings():
    global _embeddings
    if not HAS_VECTOR_LIBS:
        return None
    if _embeddings is None:
        logger.info(f"Loading local SentenceTransformer model: {settings.EMBEDDING_MODEL_NAME}...")
        try:
            _embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL_NAME,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}. Disabling vector embeddings.")
            return None
    return _embeddings

# Pure Python Search Fallback Index (BM25-inspired keyword matching)
class PurePythonSearchIndex:
    def __init__(self):
        self.documents: List[Document] = []
        
    def add_documents(self, docs: List[Document]):
        self.documents.extend(docs)
        
    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[tuple]:
        query_words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 1]
        
        # Simple TF-IDF scoring in pure Python
        scored_docs = []
        
        # Calculate Term Frequency & Inverse Document Frequency
        total_docs = len(self.documents)
        df_counts = {}
        for w in query_words:
            df_counts[w] = sum(1 for d in self.documents if w in d.page_content.lower())
            
        for doc in self.documents:
            # Apply metadata filters if present
            if filters:
                match = True
                for fk, fv in filters.items():
                    if fv and doc.metadata.get(fk) != fv:
                        match = False
                        break
                if not match:
                    continue
            
            content_lower = doc.page_content.lower()
            score = 0.0
            
            for w in query_words:
                tf = content_lower.count(w)
                if tf > 0:
                    idf = math.log((total_docs + 1) / (df_counts[w] + 1)) + 1.0
                    score += tf * idf
                    
            # Normalize confidence: scale based on how many keywords were matched
            # Basic fallback: match ratio + absolute tf score
            match_ratio = sum(1 for w in query_words if w in content_lower) / max(1, len(query_words))
            confidence = 0.0
            if match_ratio > 0:
                confidence = min(0.98, 0.3 + (match_ratio * 0.5) + min(0.18, score / 100.0))
                scored_docs.append((doc, confidence))
                
        # Sort descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:top_k]

# Persistent memory index for offline pure-python fallback
_python_fallback_index = PurePythonSearchIndex()

def compute_file_hash(filepath: str) -> str:
    """Compute MD5 hash of a file to check for updates."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def extract_pdf_chunks(filepath: str) -> List[Document]:
    """Extract text from a PDF page-by-page and chunk it."""
    documents = []
    filename = os.path.basename(filepath)
    
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                page_text = text.strip()
                chunk_size = 700
                overlap = 100
                
                start = 0
                chunk_idx = 0
                while start < len(page_text):
                    end = start + chunk_size
                    chunk_text = page_text[start:end]
                    
                    doc = Document(
                        page_content=chunk_text,
                        metadata={
                            "source": filename,
                            "page": page_idx + 1,
                            "chunk_id": f"{filename}_p{page_idx + 1}_c{chunk_idx}",
                            "type": "pdf",
                            "official_website": None
                        }
                    )
                    documents.append(doc)
                    chunk_idx += 1
                    start += chunk_size - overlap
    except Exception as e:
        logger.error(f"Error extracting PDF {filename}: {e}. Trying simple pypdf reader.")
        try:
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text:
                    continue
                doc = Document(
                    page_content=text.strip(),
                    metadata={
                        "source": filename,
                        "page": page_idx + 1,
                        "chunk_id": f"{filename}_p{page_idx + 1}_c0",
                        "type": "pdf",
                        "official_website": None
                    }
                )
                documents.append(doc)
        except Exception as e2:
            logger.error(f"PDF extraction completely failed: {e2}")
            
    return documents

def extract_csv_chunks(filepath: str) -> List[Document]:
    """Parse government scheme dataset rows and format into semantic text representations."""
    documents = []
    filename = os.path.basename(filepath)
    
    # 1. Try reading with Pandas if available
    if HAS_PANDAS:
        try:
            df = pd.read_csv(filepath)
            df.columns = [col.strip() for col in df.columns]
            for idx, row in df.iterrows():
                row_dict = {str(k): (str(v).strip() if pd.notna(v) else "") for k, v in row.items()}
                doc = compile_row_document(row_dict, idx, filename)
                documents.append(doc)
            return documents
        except Exception as e:
            logger.error(f"Pandas extraction failed, trying built-in csv reader: {e}")

    # 2. Fallback to standard library csv module
    try:
        with open(filepath, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                # Clean keys and values
                row_cleaned = {k.strip(): v.strip() for k, v in row.items() if k is not None}
                doc = compile_row_document(row_cleaned, idx, filename)
                documents.append(doc)
    except Exception as e:
        logger.error(f"Standard csv reader failed for dataset {filename}: {e}")
        
    return documents

def compile_row_document(row_dict: Dict[str, str], idx: int, filename: str) -> Document:
    """Helper to convert a scheme key-value row into a standardized text representation Document."""
    scheme_name = row_dict.get("Scheme Name", row_dict.get("scheme_name", row_dict.get("title", f"Scheme {idx}")))
    description = row_dict.get("Description", row_dict.get("description", ""))
    eligibility = row_dict.get("Eligibility", row_dict.get("Eligibility Criteria", row_dict.get("eligibility_criteria", "")))
    benefits = row_dict.get("Benefits", row_dict.get("benefits", ""))
    state = row_dict.get("State", row_dict.get("state", "All India"))
    category = row_dict.get("Category", row_dict.get("category", "General"))
    required_docs = row_dict.get("Required Documents", row_dict.get("documents", ""))
    application_process = row_dict.get("Application Process", row_dict.get("how_to_apply", ""))
    website = row_dict.get("Official Website", row_dict.get("official_website", row_dict.get("website", "")) or "")
    fees = row_dict.get("Application Fees", row_dict.get("fees", "Free"))
    timeline = row_dict.get("Processing Time", row_dict.get("timeline", ""))
    
    text_repr = (
        f"Scheme Name: {scheme_name}\n"
        f"State: {state}\n"
        f"Category: {category}\n"
        f"Description: {description}\n"
        f"Eligibility Criteria: {eligibility}\n"
        f"Benefits Provided: {benefits}\n"
        f"Required Documents: {required_docs}\n"
        f"Application Process: {application_process}\n"
        f"Official Website: {website}\n"
        f"Fees: {fees}\n"
        f"Processing Time: {timeline}"
    )
    
    return Document(
        page_content=text_repr,
        metadata={
            "source": filename,
            "scheme_name": scheme_name,
            "state": state,
            "category": category,
            "row_index": idx,
            "type": "csv",
            "official_website": website or None
        }
    )

def scan_and_rebuild_index() -> Dict[str, Any]:
    """
    Checks documents/ and datasets/ folders. Rebuilds indices and caches
    in either FAISS (if available) or the memory fallback index.
    """
    db_session = SessionLocal()
    try:
        pdf_dir = Path(settings.PDF_FOLDER)
        csv_dir = Path(settings.DATASET_FOLDER)
        
        pdf_dir.mkdir(parents=True, exist_ok=True)
        csv_dir.mkdir(parents=True, exist_ok=True)
        
        all_files = []
        for f in pdf_dir.glob("*.pdf"):
            all_files.append((str(f), "pdf"))
        for f in csv_dir.glob("*.csv"):
            all_files.append((str(f), "csv"))
            
        if not all_files:
            logger.info("No documents or datasets found to index.")
            return {"status": "empty", "total_chunks": 0, "processed_files": 0}
            
        # Check hashes
        db_records = db_session.query(DocumentMetadata).all()
        db_hashes = {rec.filename: rec.file_hash for rec in db_records}
        
        rebuild_needed = False
        current_files = set()
        
        for filepath, file_type in all_files:
            filename = os.path.basename(filepath)
            current_files.add(filename)
            file_hash = compute_file_hash(filepath)
            
            if filename not in db_hashes or db_hashes[filename] != file_hash:
                rebuild_needed = True
                break
                
        for filename in db_hashes:
            if filename not in current_files:
                rebuild_needed = True
                break
                
        # Rebuild check for FAISS
        if HAS_VECTOR_LIBS:
            index_path = Path(settings.VECTOR_DB_PATH) / "index.faiss"
            if not index_path.exists():
                rebuild_needed = True
        else:
            # Memory index rebuild
            if not _python_fallback_index.documents:
                rebuild_needed = True
                
        if not rebuild_needed:
            logger.info("Database files are unchanged. Skipping re-indexing.")
            total_chunks = len(_python_fallback_index.documents)
            if HAS_VECTOR_LIBS:
                try:
                    temp_db = FAISS.load_local(
                        settings.VECTOR_DB_PATH, 
                        get_embeddings(), 
                        allow_dangerous_deserialization=True
                    )
                    total_chunks = temp_db.index.ntotal
                except Exception:
                    pass
            return {"status": "skipped", "total_chunks": total_chunks, "processed_files": len(all_files)}
            
        logger.info("Regenerating scheme chunk indices...")
        all_documents = []
        file_metadata_to_save = []
        
        for filepath, file_type in all_files:
            filename = os.path.basename(filepath)
            file_hash = compute_file_hash(filepath)
            
            if file_type == "pdf":
                chunks = extract_pdf_chunks(filepath)
            else:
                chunks = extract_csv_chunks(filepath)
                
            all_documents.extend(chunks)
            file_metadata_to_save.append({
                "filename": filename,
                "file_type": file_type,
                "file_hash": file_hash,
                "chunk_count": len(chunks)
            })
            
        if not all_documents:
            logger.warning("No text chunks processed.")
            return {"status": "empty", "total_chunks": 0, "processed_files": 0}
            
        # Re-populate local python fallback index
        _python_fallback_index.documents = []
        _python_fallback_index.add_documents(all_documents)
        
        # Rebuild FAISS if available
        if HAS_VECTOR_LIBS:
            try:
                embeddings = get_embeddings()
                if embeddings:
                    vector_db = FAISS.from_documents(all_documents, embeddings)
                    vector_db.save_local(settings.VECTOR_DB_PATH)
                    logger.info("Saved vector index locally.")
            except Exception as e:
                logger.error(f"Failed to generate FAISS store: {e}. Falling back to pure Python searches.")
        
        # Save file info to Database
        db_session.query(DocumentMetadata).delete()
        for meta in file_metadata_to_save:
            db_rec = DocumentMetadata(
                filename=meta["filename"],
                file_type=meta["file_type"],
                file_hash=meta["file_hash"],
                chunk_count=meta["chunk_count"],
                indexed_at=datetime.now(timezone.utc)
            )
            db_session.add(db_rec)
        db_session.commit()
        
        logger.info(f"Indexing completed. Chunks created: {len(all_documents)}")
        return {"status": "rebuilt", "total_chunks": len(all_documents), "processed_files": len(all_files)}
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Scanning files failed: {e}")
        raise e
    finally:
        db_session.close()

def query_vector_db(query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Search vector index. Integrates FAISS similarity score retrieval and falls back
    to pure-Python keyword-matching search if vector libraries are not active.
    """
    # Fallback path if FAISS is not imported/initialized
    index_path = Path(settings.VECTOR_DB_PATH) / "index.faiss"
    
    if not HAS_VECTOR_LIBS or not index_path.exists() or get_embeddings() is None:
        logger.debug("Executing search query using pure-Python keyword index...")
        # Populate fallback index if empty and records exist
        if not _python_fallback_index.documents:
            logger.info("Fallback index is empty. Performing quick re-scan...")
            try:
                scan_and_rebuild_index()
            except Exception:
                pass
                
        results = _python_fallback_index.search(query, top_k=top_k, filters=filters)
        
        matched_chunks = []
        for doc, score in results:
            matched_chunks.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata,
                "confidence": score
            })
        return matched_chunks

    # Standard FAISS pathway
    try:
        embeddings = get_embeddings()
        vector_db = FAISS.load_local(
            settings.VECTOR_DB_PATH, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        results = vector_db.similarity_search_with_score(query, k=top_k * 2)
        
        matched_chunks = []
        seen_contents = set()
        
        for doc, score in results:
            content = doc.page_content.strip()
            if content in seen_contents:
                continue
            seen_contents.add(content)
            
            if filters:
                match = True
                for fk, fv in filters.items():
                    if fv and doc.metadata.get(fk) != fv:
                        match = False
                        break
                if not match:
                    continue
            
            distance = float(score)
            confidence = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
            
            matched_chunks.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata,
                "confidence": confidence
            })
            
            if len(matched_chunks) >= top_k:
                break
                
        return matched_chunks
    except Exception as e:
        logger.error(f"Error querying FAISS: {e}. Swapping to memory fallback search.")
        # Try fallback
        results = _python_fallback_index.search(query, top_k=top_k, filters=filters)
        matched_chunks = []
        for doc, score in results:
            matched_chunks.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata,
                "confidence": score
            })
        return matched_chunks
