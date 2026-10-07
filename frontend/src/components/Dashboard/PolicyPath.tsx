"use client";

import React, { useState } from "react";
import { useAppStore } from "../../store/useAppStore";
import { 
  UserCheck, ClipboardList, CheckSquare, Square, 
  MapPin, HelpCircle, AlertTriangle, ExternalLink 
} from "lucide-react";

export default function PolicyPath() {
  const { eligibilityProfile, eligibilityResults, setEligibilityModalOpen } = useAppStore();
  const [checkedDocs, setCheckedDocs] = useState<Record<string, boolean>>({});

  const toggleDoc = (docName: string) => {
    setCheckedDocs((prev) => ({
      ...prev,
      [docName]: !prev[docName]
    }));
  };

  // Compile all required documents across eligible schemes
  const allRequiredDocs = React.useMemo(() => {
    if (!eligibilityResults) return [];
    const docsSet = new Set<string>();
    
    // Fallbacks if structured required documents list is empty
    eligibilityResults.eligible_schemes.forEach((scheme) => {
      // Gather standard fallback files
      docsSet.add("Aadhaar Card");
      docsSet.add("Income Certificate");
      docsSet.add("Residence Proof / Domicile");
      
      // Look for conditions
      scheme.highlighted_conditions.forEach((cond) => {
        if (cond.toLowerCase().includes("land")) docsSet.add("Agricultural Land Registry papers");
        if (cond.toLowerCase().includes("category") || cond.toLowerCase().includes("caste")) docsSet.add("Caste Certificate (if SC/ST/OBC)");
        if (cond.toLowerCase().includes("disability")) docsSet.add("UDID Disability Certificate");
      });
    });
    
    return Array.from(docsSet);
  }, [eligibilityResults]);

  if (!eligibilityProfile || !eligibilityResults) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-100">
        <div className="h-12 w-12 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-center text-slate-400 mb-4">
          <UserCheck className="h-6 w-6" />
        </div>
        <h4 className="text-sm font-bold text-white mb-1.5">No Active Policy Path</h4>
        <p className="text-xs text-slate-400 max-w-[240px] leading-relaxed mb-5">
          Provide your profile metrics to build a tailored welfare timeline, document checklists, and application guides.
        </p>
        <button
          onClick={() => setEligibilityModalOpen(true)}
          className="bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 px-4 rounded-lg text-xs transition-colors cursor-pointer shadow-lg shadow-blue-600/10"
        >
          Check Scheme Eligibility
        </button>
      </div>
    );
  }

  const { eligible_schemes, more_info_schemes, profile_summary } = eligibilityResults;

  return (
    <div className="h-full flex flex-col gap-6 p-5 text-slate-100 overflow-y-auto custom-scrollbar">
      {/* 1. Profile Summary Card */}
      <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-4">
        <div className="flex justify-between items-center mb-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Citizen Profile</h4>
          <button
            onClick={() => setEligibilityModalOpen(true)}
            className="text-[10px] text-blue-400 hover:text-blue-300 font-bold transition-colors cursor-pointer"
          >
            Edit Profile
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2.5 text-xs">
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-bold">Age / Gender</span>
            <span className="text-slate-200">{profile_summary["Age"]} Years • {profile_summary["Gender"]}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-bold">State</span>
            <span className="text-slate-200 truncate block">{profile_summary["State"]}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-bold">Occupation</span>
            <span className="text-slate-200">{profile_summary["Occupation"]}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-bold">Annual Income</span>
            <span className="text-slate-200">{profile_summary["Annual Income"]}</span>
          </div>
        </div>
      </div>

      {/* 2. Eligible Schemes Panel */}
      <div className="flex flex-col gap-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-1">
          <UserCheck className="h-4 w-4 text-emerald-400" />
          Eligible Schemes ({eligible_schemes.length})
        </h4>
        {eligible_schemes.length === 0 ? (
          <p className="text-xs text-slate-500 italic bg-slate-950/20 border border-slate-800/50 p-3 rounded-lg text-center">
            No matches found based on profile filters.
          </p>
        ) : (
          <div className="space-y-3">
            {eligible_schemes.map((scheme) => (
              <div key={scheme.scheme_id} className="bg-slate-900/60 border border-slate-800/70 rounded-xl p-3.5 hover:border-slate-700/70 transition-all">
                <div className="flex justify-between items-start mb-1.5">
                  <h5 className="text-xs font-bold text-slate-200 leading-snug">{scheme.scheme_name}</h5>
                  <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-bold">
                    Eligible
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed mb-2.5">
                  {scheme.reason}
                </p>
                <div className="border-t border-slate-800/30 pt-2 text-[10px]">
                  <span className="text-slate-500 block font-bold uppercase mb-1">Key Criteria</span>
                  <ul className="space-y-1">
                    {scheme.highlighted_conditions.slice(0, 2).map((cond, idx) => (
                      <li key={idx} className="text-slate-300 leading-normal flex items-start gap-1">
                        <span>•</span>
                        <span>{cond}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3. Document Checklist */}
      {allRequiredDocs.length > 0 && (
        <div className="flex flex-col gap-2 border-t border-slate-800/60 pt-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-1">
            <ClipboardList className="h-4 w-4 text-blue-400" />
            Unified Checklist
          </h4>
          <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-3 space-y-2">
            {allRequiredDocs.map((doc) => (
              <button
                key={doc}
                onClick={() => toggleDoc(doc)}
                className="w-full flex items-start gap-2.5 text-left text-xs py-1 text-slate-300 hover:text-white transition-colors focus:outline-none cursor-pointer"
              >
                <span className="mt-0.5 text-slate-500 hover:text-blue-400 transition-colors">
                  {checkedDocs[doc] ? (
                    <CheckSquare className="h-4 w-4 text-blue-500" />
                  ) : (
                    <Square className="h-4 w-4" />
                  )}
                </span>
                <span className={checkedDocs[doc] ? "line-through text-slate-500" : ""}>
                  {doc}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 4. More Info Schemes */}
      {more_info_schemes.length > 0 && (
        <div className="flex flex-col gap-2 border-t border-slate-800/60 pt-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-1">
            <HelpCircle className="h-4 w-4 text-amber-400" />
            Needs Verification ({more_info_schemes.length})
          </h4>
          <div className="space-y-3">
            {more_info_schemes.map((scheme) => (
              <div key={scheme.scheme_id} className="bg-slate-900/40 border border-slate-800/60 rounded-xl p-3 hover:border-slate-700/60 transition-all">
                <div className="flex justify-between items-start mb-1.5">
                  <h5 className="text-xs font-bold text-slate-200 leading-snug">{scheme.scheme_name}</h5>
                  <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full font-bold whitespace-nowrap">
                    More Info
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed mb-2">
                  {scheme.reason}
                </p>
                {scheme.missing_information.length > 0 && (
                  <div className="border-t border-slate-800/30 pt-1.5 text-[10px]">
                    <span className="text-amber-500 font-bold block mb-1">Upload required:</span>
                    <ul className="list-disc pl-3 text-slate-300 space-y-0.5">
                      {scheme.missing_information.map((m, idx) => (
                        <li key={idx}>{m}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
