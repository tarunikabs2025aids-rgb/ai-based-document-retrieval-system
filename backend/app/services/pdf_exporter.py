import io
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generate_pdf_report(chat_data: Dict[str, Any], scheme_name: str = "Government Welfare Scheme") -> io.BytesIO:
    """
    Generates a structured PDF report containing scheme answers, eligibility guidelines,
    required documents, timelines, and citations.
    """
    buffer = io.BytesIO()
    
    # Page setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles for premium SaaS look
    primary_color = colors.HexColor("#0f172a") # Slate 900
    accent_color = colors.HexColor("#2563eb") # Blue 600
    text_color = colors.HexColor("#334155") # Slate 700
    bg_light = colors.HexColor("#f8fafc") # Slate 50
    border_color = colors.HexColor("#e2e8f0") # Slate 200
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=accent_color,
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_color,
        spaceAfter=10
    )
    
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b")
    )
    
    warning_style = ParagraphStyle(
        'WarningText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#b45309") # Amber 700
    )
    
    story = []
    
    # 1. Header Title
    story.append(Paragraph(f"GovAssist AI - Citizen Action Plan", title_style))
    story.append(Paragraph(f"<b>Scheme:</b> {scheme_name}", h2_style))
    story.append(Paragraph(f"Generated on: <i>{chat_data.get('date', 'Today')}</i>", meta_style))
    story.append(Spacer(1, 15))
    
    # 2. Main Guidance / Answer
    story.append(Paragraph("Detailed Information", h2_style))
    answer_text = chat_data.get("answer", "No description available.")
    # Replace markdown headers and line breaks with basic html paragraphs
    cleaned_answer = answer_text.replace("\n", "<br/>").replace("### ", "<b>").replace("## ", "<b>").replace("**", "<b>")
    story.append(Paragraph(cleaned_answer, body_style))
    story.append(Spacer(1, 10))
    
    action_plan = chat_data.get("action_plan")
    
    if action_plan:
        # 3. Required Documents Table
        docs = action_plan.get("required_documents", [])
        if docs:
            story.append(Paragraph("Required Documents Checklist", h2_style))
            doc_data = [[Paragraph(f"• {doc}", body_style)] for doc in docs]
            doc_table = Table(doc_data, colWidths=[5 * inch])
            doc_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), bg_light),
                ('BOX', (0,0), (-1,-1), 1, border_color),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(doc_table)
            story.append(Spacer(1, 10))
            
        # 4. Details / Timeline Checklist
        timeline = action_plan.get("timeline", [])
        if timeline:
            story.append(Paragraph("Step-by-Step Application Timeline", h2_style))
            timeline_data = [["Step", "Activity Description", "Timeline"]]
            for item in timeline:
                timeline_data.append([
                    str(item.get("step", "")),
                    Paragraph(f"<b>{item.get('title', '')}</b><br/>{item.get('description', '')}", body_style),
                    item.get("timeline", "")
                ])
                
            t_table = Table(timeline_data, colWidths=[0.6 * inch, 3.4 * inch, 1.0 * inch])
            t_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#cbd5e1")), # Slate 300
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), 0.5, border_color),
                ('PADDING', (0,0), (-1,-1), 6),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 9),
            ]))
            story.append(t_table)
            story.append(Spacer(1, 10))
            
        # 5. Core Actions & Fees Table
        meta_details = [
            ["Where to Apply:", action_plan.get("where_to_apply", "N/A")],
            ["Application Fees:", action_plan.get("application_fees", "Free")],
            ["Processing Time:", action_plan.get("processing_time", "N/A")]
        ]
        if action_plan.get("application_form_url"):
            meta_details.append(["Official Website:", action_plan.get("application_form_url")])
            
        story.append(Paragraph("Submission Guidelines", h2_style))
        meta_table = Table(meta_details, colWidths=[2.0 * inch, 3.0 * inch])
        meta_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (0,0), (0,-1), bg_light),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))
        
        # 6. Warnings
        warnings = action_plan.get("warnings", [])
        if warnings:
            story.append(Paragraph("⚠️ Important Warnings & Restrictions", h2_style))
            for w in warnings:
                story.append(Paragraph(f"• {w}", warning_style))
            story.append(Spacer(1, 10))
            
    # 7. Citations & References
    citations = chat_data.get("citations", [])
    if citations:
        story.append(Paragraph("Source Citations & Evidentiary Chunks", h2_style))
        for idx, cit in enumerate(citations):
            source_info = f"{idx+1}. {cit.get('source', 'Welfare Guideline')}"
            if cit.get('page'):
                source_info += f" (Page {cit.get('page')})"
            if cit.get('confidence'):
                source_info += f" - Match Score: {int(cit.get('confidence') * 100)}%"
                
            story.append(Paragraph(f"<b>{source_info}</b>", meta_style))
            chunk_text = cit.get('chunk', '')[:250] + "..." if len(cit.get('chunk', '')) > 250 else cit.get('chunk', '')
            story.append(Paragraph(f"<i>\"{chunk_text}\"</i>", ParagraphStyle('ChunkText', parent=meta_style, leftIndent=15, spaceAfter=8)))
            
    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer
