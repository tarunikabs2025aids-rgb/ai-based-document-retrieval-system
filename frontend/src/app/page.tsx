"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ShieldCheck, Sparkles, Languages, CheckCircle, Search, ClipboardList, HelpCircle, FileText, ArrowRight } from "lucide-react";

export default function LandingPage() {
  const [activeFaq, setActiveFaq] = useState<number | null>(null);

  const faqs = [
    {
      q: "How does GovAssist AI know about the welfare schemes?",
      a: "Our system combines a structured database of over 4,670 Central and State schemes with verified PDFs uploaded by government administrators. We use RAG (Retrieval Augmented Generation) to ground all chatbot answers in official documentation.",
    },
    {
      q: "Can I ask questions in regional languages?",
      a: "Yes! GovAssist AI supports 11 Indian languages (Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Punjabi, Bengali, Odia, and English). The system automatically detects your language, translates and searches the database, and outputs the reply in your tongue.",
    },
    {
      q: "What is the ProofBox feature?",
      a: "Trust is our primary goal. The ProofBox is a floating panel that shows the exact paragraph, page number, and source document that the chatbot used to answer your question. You can click on any citation badge to view this verified proof.",
    },
    {
      q: "How does the Eligibility Checker work?",
      a: "By entering simple criteria (age, state, occupation, income), our hybrid rules and AI evaluation engine automatically checks which schemes you qualify for, explaining the specific conditions and highlighting what files you need to submit.",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col relative overflow-hidden">
      {/* Dynamic Gradients */}
      <div className="absolute top-[-30%] left-[-20%] w-[80%] h-[80%] rounded-full bg-blue-900/10 blur-[130px] animate-pulse" />
      <div className="absolute bottom-[-30%] right-[-20%] w-[80%] h-[80%] rounded-full bg-violet-900/10 blur-[130px] animate-pulse" />

      {/* Navigation Header */}
      <header className="border-b border-slate-900 bg-slate-950/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <ShieldCheck className="h-8 w-8 text-blue-500 group-hover:rotate-6 transition-transform" />
            <span className="text-xl font-bold tracking-tight text-white">
              GovAssist <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">AI</span>
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
              Sign In
            </Link>
            <Link
              href="/register"
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-md shadow-blue-600/15 flex items-center gap-1 cursor-pointer"
            >
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-grow z-10">
        <section className="py-20 md:py-28 px-4 max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-blue-500/20 bg-blue-500/5 text-xs text-blue-400 font-medium mb-6">
            <Sparkles className="h-3.5 w-3.5" />
            Empowering Citizens with Grounded AI Retrieval
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white leading-tight max-w-4xl mx-auto">
            Discover and Apply for Government Schemes{" "}
            <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-violet-400 bg-clip-text text-transparent">
              in Your Language
            </span>
          </h1>
          <p className="mt-6 text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Discover verified welfare benefits, check your eligibility instantly, and generate structured next-step checklists. Grounded in official policy documents.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row justify-center items-center gap-4">
            <Link
              href="/register"
              className="w-full sm:w-auto bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white px-8 py-4 rounded-xl text-base font-bold transition-all shadow-xl shadow-blue-500/10 flex items-center justify-center gap-2 cursor-pointer"
            >
              Launch Chat Assistant
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="/login"
              className="w-full sm:w-auto border border-slate-800 bg-slate-900/55 hover:bg-slate-900 text-slate-300 hover:text-white px-8 py-4 rounded-xl text-base font-bold transition-colors flex items-center justify-center"
            >
              Sign In
            </Link>
          </div>

          {/* Feature Matrix Grid */}
          <div className="mt-24 grid md:grid-cols-3 gap-8">
            <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl p-6 hover:border-slate-700/80 transition-all text-left">
              <div className="h-10 w-10 bg-blue-500/10 border border-blue-500/20 rounded-lg flex items-center justify-center text-blue-400 mb-4">
                <Languages className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Multilingual RAG Engine</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Supports 11 major Indian languages. Auto-detects input query, translates to search schemas in English, and translates grounded answers back.
              </p>
            </div>

            <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl p-6 hover:border-slate-700/80 transition-all text-left">
              <div className="h-10 w-10 bg-indigo-500/10 border border-indigo-500/20 rounded-lg flex items-center justify-center text-indigo-400 mb-4">
                <CheckCircle className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Eligibility Checker</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Rule-based and LLM evaluation parameters match Age, Gender, Income, and Occupation criteria to verify scheme compliance, highlighting missing info.
              </p>
            </div>

            <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl p-6 hover:border-slate-700/80 transition-all text-left">
              <div className="h-10 w-10 bg-violet-500/10 border border-violet-500/20 rounded-lg flex items-center justify-center text-violet-400 mb-4">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white">ProofBox Citations</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Zero hallucination design. Click on any chatbot advice to slide open the exact reference text, confidence scoring, and document page citation.
              </p>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="border-y border-slate-900 bg-slate-950/30 backdrop-blur-sm py-16 px-4">
          <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl md:text-5xl font-black text-white bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">4,670+</div>
              <div className="text-xs md:text-sm text-slate-400 mt-2 font-medium uppercase tracking-wider">Government Schemes</div>
            </div>
            <div>
              <div className="text-3xl md:text-5xl font-black text-white bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">11+</div>
              <div className="text-xs md:text-sm text-slate-400 mt-2 font-medium uppercase tracking-wider">Indian Languages</div>
            </div>
            <div>
              <div className="text-3xl md:text-5xl font-black text-white bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">100%</div>
              <div className="text-xs md:text-sm text-slate-400 mt-2 font-medium uppercase tracking-wider">Grounded Responses</div>
            </div>
            <div>
              <div className="text-3xl md:text-5xl font-black text-white bg-gradient-to-r from-fuchsia-400 to-blue-400 bg-clip-text text-transparent">&lt; 2.5s</div>
              <div className="text-xs md:text-sm text-slate-400 mt-2 font-medium uppercase tracking-wider">Retrieval Latency</div>
            </div>
          </div>
        </section>

        {/* FAQs */}
        <section className="py-20 px-4 max-w-4xl mx-auto">
          <h2 className="text-3xl font-extrabold text-center text-white mb-10 flex items-center justify-center gap-2">
            <HelpCircle className="h-7 w-7 text-blue-500" />
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {faqs.map((faq, idx) => (
              <div key={idx} className="bg-slate-900/35 border border-slate-800 rounded-xl overflow-hidden transition-all duration-300">
                <button
                  onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                  className="w-full py-5 px-6 text-left font-bold text-white flex justify-between items-center focus:outline-none cursor-pointer"
                >
                  <span>{faq.q}</span>
                  <span className="text-blue-500 font-extrabold text-lg select-none">
                    {activeFaq === idx ? "−" : "+"}
                  </span>
                </button>
                {activeFaq === idx && (
                  <div className="pb-5 px-6 text-sm text-slate-400 leading-relaxed border-t border-slate-800/40 pt-3">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-8 bg-slate-950 text-center text-xs text-slate-600 z-10">
        <p>&copy; {new Date().getFullYear()} GovAssist AI. Developed for Indian Welfare Schemes Grounded Discovery. All Rights Reserved.</p>
      </footer>
    </div>
  );
}
