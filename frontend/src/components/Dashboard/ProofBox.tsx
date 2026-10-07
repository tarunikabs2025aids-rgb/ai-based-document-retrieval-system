"use client";

import React from "react";
import { useAppStore } from "../../store/useAppStore";
import { X, ExternalLink, ShieldCheck, Download } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function ProofBox() {
  const { activeCitation, activeSchemeName, setActiveCitation } = useAppStore();

  if (!activeCitation) return null;

  const confidencePercent = Math.round(activeCitation.confidence * 100);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 100, opacity: 0 }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed bottom-6 right-6 left-6 md:left-auto md:w-[480px] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-5 z-50 text-slate-100 flex flex-col gap-4 backdrop-blur-xl bg-slate-900/90"
      >
        {/* Header */}
        <div className="flex justify-between items-start border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-blue-500" />
            <div>
              <h4 className="text-sm font-bold text-white">Grounded Citation Proof</h4>
              <p className="text-[11px] text-slate-400">Verified from official source document</p>
            </div>
          </div>
          <button
            onClick={() => setActiveCitation(null, null)}
            className="p-1 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Confidence rating card */}
        <div className="flex items-center justify-between bg-slate-950/60 border border-slate-800/80 px-3 py-2 rounded-lg text-xs">
          <span className="text-slate-400 font-medium">Verification Confidence</span>
          <span
            className={`font-bold px-2 py-0.5 rounded-full ${
              confidencePercent > 80
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : confidencePercent > 50
                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                : "bg-red-500/10 text-red-400 border border-red-500/20"
            }`}
          >
            {confidencePercent}% Match
          </span>
        </div>

        {/* Extracted block quote */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold">Extracted Text</span>
          <div className="bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/50 text-xs leading-relaxed italic text-slate-300 max-h-[160px] overflow-y-auto custom-scrollbar">
            "{activeCitation.chunk}"
          </div>
        </div>

        {/* Source metadata details */}
        <div className="grid grid-cols-2 gap-3 text-xs bg-slate-950/30 p-3 rounded-xl border border-slate-800/40">
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-bold">Document Source</span>
            <span className="text-slate-200 font-medium truncate block max-w-[200px]" title={activeCitation.source}>
              {activeCitation.source}
            </span>
          </div>
          {activeCitation.page && (
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold">Page Number</span>
              <span className="text-slate-200 font-medium">Page {activeCitation.page}</span>
            </div>
          )}
          {activeCitation.row_index !== undefined && (
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold">Dataset Record</span>
              <span className="text-slate-200 font-medium">Row #{activeCitation.row_index}</span>
            </div>
          )}
          {activeSchemeName && (
            <div className="col-span-2 mt-1 border-t border-slate-800/30 pt-1.5">
              <span className="text-slate-500 block text-[10px] uppercase font-bold">Identified Scheme</span>
              <span className="text-slate-200 font-semibold truncate block">{activeSchemeName}</span>
            </div>
          )}
        </div>

        {/* Action button triggers */}
        {activeCitation.official_website && (
          <a
            href={activeCitation.official_website}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex justify-center items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 px-4 rounded-xl text-xs transition-colors shadow-lg shadow-blue-600/10 cursor-pointer"
          >
            Visit Official Application Portal
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
