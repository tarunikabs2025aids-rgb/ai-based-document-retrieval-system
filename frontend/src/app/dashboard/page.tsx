"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAppStore } from "../../store/useAppStore";
import Sidebar from "../../components/Dashboard/Sidebar";
import ChatWindow from "../../components/Dashboard/ChatWindow";
import PolicyPath from "../../components/Dashboard/PolicyPath";
import ProofBox from "../../components/Dashboard/ProofBox";
import EligibilityForm from "../../components/Dashboard/EligibilityForm";

export default function DashboardPage() {
  const router = useRouter();
  const token = useAppStore((state) => state.token);

  useEffect(() => {
    // If not authenticated, redirect to login page
    if (!token) {
      router.push("/login");
    }
  }, [token, router]);

  if (!token) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 text-sm">
        Authenticating session...
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 font-sans">
      {/* 1. Left Navigation Sidebar */}
      <Sidebar />

      {/* 2. Main Chat Window Panel */}
      <main className="flex-grow flex flex-col min-w-0 border-r border-slate-900">
        <ChatWindow />
      </main>

      {/* 3. Right Policy Path Panel */}
      <aside className="w-80 shrink-0 bg-slate-950/70 hidden lg:block">
        <PolicyPath />
      </aside>

      {/* 4. Global Floating Citations proof Drawer */}
      <ProofBox />

      {/* 5. Global Profile wizard modal */}
      <EligibilityForm />
    </div>
  );
}
