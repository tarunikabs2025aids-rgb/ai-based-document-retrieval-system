"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAppStore } from "../../../store/useAppStore";
import { api } from "../../../services/api";
import Sidebar from "../../../components/Dashboard/Sidebar";
import { Search, MapPin, Grid, ExternalLink, MessageSquare, Loader2, Compass } from "lucide-react";

export default function SearchPage() {
  const router = useRouter();
  const token = useAppStore((state) => state.token);
  const setActiveConversationId = useAppStore((state) => state.setActiveConversationId);

  const [query, setQuery] = useState("");
  const [selectedState, setSelectedState] = useState("Any");
  const [selectedCategory, setSelectedCategory] = useState("Any");
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const states = [
    "Any", "All India", "Andhra Pradesh", "Assam", "Bihar", "Gujarat", "Haryana",
    "Himachal Pradesh", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
    "Odisha", "Punjab", "Rajasthan", "Tamil Nadu", "Telangana", "Uttar Pradesh",
    "West Bengal", "Delhi"
  ];

  const categories = [
    "Any", "Farmers", "Students", "Business", "Women", "Senior Citizens",
    "Disabled", "Minorities", "Unemployed"
  ];

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    try {
      const stateParam = selectedState !== "Any" ? `&state=${encodeURIComponent(selectedState)}` : "";
      const catParam = selectedCategory !== "Any" ? `&category=${encodeURIComponent(selectedCategory)}` : "";
      const response = await api.get(`/search/?q=${encodeURIComponent(query || "scheme")}${stateParam}${catParam}`);
      setResults(response.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      handleSearch();
    } else {
      router.push("/login");
    }
  }, [token, selectedState, selectedCategory]);

  const handleAskAIAboutScheme = (schemeName: string) => {
    setActiveConversationId(null); // start new chat
    // Save to local storage for chat input capture on mount
    localStorage.setItem("pendingChatPrompt", `Tell me details, eligibility, and application process for: ${schemeName}`);
    router.push("/dashboard");
  };

  if (!token) return null;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      <Sidebar />

      <div className="flex-grow flex flex-col min-w-0">
        {/* Top Navbar Header */}
        <header className="h-16 border-b border-slate-900 px-6 flex items-center justify-between bg-slate-950/40 backdrop-blur-md sticky top-0 z-20">
          <div className="flex items-center gap-2">
            <Compass className="h-5 w-5 text-blue-500" />
            <div>
              <h2 className="text-sm font-bold text-white">Smart Schemes Discovery</h2>
              <p className="text-[10px] text-slate-500">Semantic Vector Matching & Filters</p>
            </div>
          </div>
        </header>

        {/* Scrollable Panel */}
        <div className="flex-grow overflow-y-auto px-6 py-6 custom-scrollbar">
          <div className="max-w-5xl mx-auto space-y-6">
            
            {/* Search inputs bar */}
            <form onSubmit={handleSearch} className="bg-slate-900/40 border border-slate-800 p-4 rounded-2xl flex flex-col md:flex-row gap-4 items-end shadow-xl">
              <div className="flex-grow w-full">
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Search Keywords</label>
                <div className="relative">
                  <Search className="absolute inset-y-0 left-3 h-5 w-5 text-slate-500 flex items-center pointer-events-none mt-2.5" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter keywords e.g. 'loan subsidy', 'scholarship', 'pension'..."
                    className="w-full bg-slate-950 border border-slate-850 rounded-xl pl-10 pr-3 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="w-full md:w-[180px] shrink-0">
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">State Filter</label>
                <select
                  value={selectedState}
                  onChange={(e) => setSelectedState(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 rounded-xl px-3 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-blue-500"
                >
                  {states.map((st) => (
                    <option key={st} value={st}>{st}</option>
                  ))}
                </select>
              </div>

              <div className="w-full md:w-[180px] shrink-0">
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Category Filter</label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 rounded-xl px-3 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-blue-500"
                >
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full md:w-auto bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white font-semibold py-2.5 px-6 rounded-xl text-sm transition-colors flex items-center justify-center gap-1.5 cursor-pointer shrink-0"
              >
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
              </button>
            </form>

            {/* Results Grid layout */}
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-20 text-slate-500 gap-2">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                <span className="text-xs">Searching scheme registry databases...</span>
              </div>
            ) : results.length === 0 ? (
              <div className="text-center py-20 border border-dashed border-slate-800/80 rounded-2xl bg-slate-900/10">
                <Search className="h-10 w-10 text-slate-600 mx-auto mb-3" />
                <h4 className="text-sm font-bold text-white mb-1">No Welfare Schemes Found</h4>
                <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
                  Try clearing your state/category filters or typing a broader search term.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {results.map((res, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-900/30 border border-slate-800 hover:border-slate-750 p-5 rounded-2xl transition-all flex flex-col justify-between shadow-lg"
                  >
                    <div>
                      <div className="flex justify-between items-start gap-3 mb-2.5">
                        <h4 className="text-sm font-bold text-slate-200 leading-snug truncate max-w-[280px]" title={res.title}>
                          {res.title}
                        </h4>
                        <span className="shrink-0 text-[9px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-bold">
                          {res.confidence}% Match
                        </span>
                      </div>
                      
                      {/* State & Category Badges */}
                      <div className="flex items-center gap-2 mb-3.5">
                        <span className="flex items-center gap-0.5 text-[10px] text-slate-400 font-medium">
                          <MapPin className="h-3.5 w-3.5 text-slate-500" />
                          {res.state}
                        </span>
                        <span className="flex items-center gap-0.5 text-[10px] text-slate-400 font-medium">
                          <Grid className="h-3.5 w-3.5 text-slate-500" />
                          {res.category}
                        </span>
                      </div>

                      {/* Content summary */}
                      <div className="text-xs text-slate-400 leading-relaxed max-h-[90px] overflow-hidden line-clamp-4 mask-gradient mb-4">
                        {res.content.split("\n").filter((l: string) => !l.startsWith("Scheme Name:") && !l.startsWith("State:") && !l.startsWith("Category:")).join(" ")}
                      </div>
                    </div>

                    <div className="flex gap-2.5 pt-3 border-t border-slate-800/40 mt-3 text-xs font-bold">
                      {res.official_website && (
                        <a
                          href={res.official_website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-grow flex items-center justify-center gap-1 border border-slate-800 hover:bg-slate-900 py-2 rounded-xl transition-colors text-[11px]"
                        >
                          Visit Portal
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      )}
                      <button
                        onClick={() => handleAskAIAboutScheme(res.title)}
                        className="flex-grow flex items-center justify-center gap-1 bg-blue-600 hover:bg-blue-500 py-2 rounded-xl text-white transition-colors cursor-pointer text-[11px]"
                      >
                        Ask Assistant
                        <MessageSquare className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
