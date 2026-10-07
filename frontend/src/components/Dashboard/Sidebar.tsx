"use client";

import React, { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAppStore } from "../../store/useAppStore";
import { api } from "../../services/api";
import { 
  ShieldCheck, MessageSquare, Plus, Search, 
  Trash2, Edit2, LogOut, Check, Settings, Languages, BarChart2 
} from "lucide-react";

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const { 
    user, conversations, activeConversationId, 
    setConversations, setActiveConversationId, logout, setEligibilityModalOpen 
  } = useAppStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  
  // Refresh conversations list
  const refreshHistory = async () => {
    try {
      const response = await api.get("/history");
      setConversations(response.data);
    } catch (err) {
      console.error("Failed to load chat history:", err);
    }
  };

  useEffect(() => {
    if (user) {
      refreshHistory();
    }
  }, [user]);

  const handleNewChat = () => {
    setActiveConversationId(null);
    if (pathname !== "/dashboard") {
      router.push("/dashboard");
    }
  };

  const handleDeleteChat = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat session?")) return;
    try {
      await api.delete(`/history/${id}`);
      if (activeConversationId === id) {
        setActiveConversationId(null);
      }
      refreshHistory();
    } catch (err) {
      console.error(err);
    }
  };

  const handleStartRename = (id: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(id);
    setEditTitle(currentTitle);
  };

  const handleSaveRename = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!editTitle.trim()) return;
    try {
      await api.put(`/history/${id}/rename?title=${encodeURIComponent(editTitle)}`);
      setEditingId(null);
      refreshHistory();
    } catch (err) {
      console.error(err);
    }
  };

  const handleTogglePin = async (id: string, currentPin: boolean, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.put(`/history/${id}/pin?is_pinned=${!currentPin}`);
      refreshHistory();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const pinnedConversations = filteredConversations.filter((c) => c.is_pinned);
  const recentConversations = filteredConversations.filter((c) => !c.is_pinned);

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-900 flex flex-col h-full text-slate-300">
      {/* Sidebar logo */}
      <div className="h-16 px-4 flex items-center border-b border-slate-900 justify-between">
        <Link href="/" className="flex items-center gap-1.5 font-bold text-white text-base">
          <ShieldCheck className="h-6 w-6 text-blue-500" />
          <span>GovAssist <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">AI</span></span>
        </Link>
      </div>

      {/* Initialize New Session */}
      <div className="p-3">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 px-3 rounded-lg text-xs transition-colors shadow-lg shadow-blue-600/10 cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          New Assistant Chat
        </button>
      </div>

      {/* Search filtering */}
      <div className="px-3 mb-3">
        <div className="relative">
          <Search className="absolute inset-y-0 left-2.5 h-4.5 w-4.5 text-slate-500 flex items-center pointer-events-none mt-2" />
          <input
            type="text"
            placeholder="Search history..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-slate-700 focus:ring-0"
          />
        </div>
      </div>

      {/* Main menu links */}
      <div className="px-2 space-y-0.5 mb-4">
        <Link
          href="/dashboard"
          className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
            pathname === "/dashboard" && !activeConversationId
              ? "bg-slate-900 text-white border-l-2 border-blue-500 rounded-l-none"
              : "hover:bg-slate-900/60 hover:text-white"
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          Welfare Chatbot
        </Link>
        <Link
          href="/dashboard/search"
          className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
            pathname === "/dashboard/search"
              ? "bg-slate-900 text-white border-l-2 border-blue-500 rounded-l-none"
              : "hover:bg-slate-900/60 hover:text-white"
          }`}
        >
          <Search className="h-4 w-4" />
          Semantic Search
        </Link>
        <button
          onClick={() => setEligibilityModalOpen(true)}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold hover:bg-slate-900/60 hover:text-white transition-colors text-left cursor-pointer"
        >
          <Settings className="h-4 w-4" />
          Eligibility Profiler
        </button>
      </div>

      {/* Session History Scroll Section */}
      <div className="flex-grow overflow-y-auto px-2 space-y-4 custom-scrollbar mb-4">
        {/* Pinned Session Links */}
        {pinnedConversations.length > 0 && (
          <div>
            <div className="px-3 text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">
              Pinned Conversations
            </div>
            <div className="space-y-0.5">
              {pinnedConversations.map((c) => renderConversationItem(c))}
            </div>
          </div>
        )}

        {/* Recent Session Links */}
        <div>
          <div className="px-3 text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">
            Recent Chats
          </div>
          {recentConversations.length === 0 ? (
            <div className="px-3 py-2 text-xs text-slate-600 italic">No conversations yet</div>
          ) : (
            <div className="space-y-0.5">
              {recentConversations.map((c) => renderConversationItem(c))}
            </div>
          )}
        </div>
      </div>

      {/* Footer / User Profile block */}
      <div className="border-t border-slate-900 p-3 bg-slate-950 flex flex-col gap-2.5">
        {user?.is_admin && (
          <Link
            href="/admin"
            className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs font-bold text-blue-400 justify-center transition-colors"
          >
            <BarChart2 className="h-4 w-4" />
            Admin Panel Console
          </Link>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="h-8 w-8 rounded-full bg-gradient-to-r from-blue-600 to-violet-600 flex items-center justify-center text-white font-bold text-xs shrink-0 uppercase">
              {user?.full_name ? user.full_name[0] : user?.email[0] || "U"}
            </div>
            <div className="overflow-hidden text-left">
              <div className="text-xs font-bold text-slate-200 truncate">{user?.full_name || "Citizen User"}</div>
              <div className="text-[10px] text-slate-500 truncate">{user?.email}</div>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              router.push("/login");
            }}
            title="Log Out"
            className="p-1.5 rounded-lg hover:bg-slate-900 text-slate-500 hover:text-white transition-colors cursor-pointer"
          >
            <LogOut className="h-4.5 w-4.5" />
          </button>
        </div>
      </div>
    </aside>
  );

  function renderConversationItem(c: any) {
    const isActive = activeConversationId === c.id;
    const isEditing = editingId === c.id;

    return (
      <div
        key={c.id}
        onClick={() => {
          if (!isEditing) {
            setActiveConversationId(c.id);
            router.push("/dashboard");
          }
        }}
        className={`group relative flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium cursor-pointer transition-colors ${
          isActive 
            ? "bg-slate-900 text-white border-l-2 border-blue-500 rounded-l-none" 
            : "hover:bg-slate-900/40 text-slate-400 hover:text-slate-200"
        }`}
      >
        <div className="flex items-center gap-2 overflow-hidden flex-grow mr-2">
          <MessageSquare className="h-3.5 w-3.5 shrink-0 text-slate-500" />
          {isEditing ? (
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onClick={(e) => e.stopPropagation()}
              className="bg-slate-950 border border-slate-800 text-white rounded px-1.5 py-0.5 text-xs focus:outline-none w-full"
            />
          ) : (
            <span className="truncate leading-normal">{c.title}</span>
          )}
        </div>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10 shrink-0">
          {isEditing ? (
            <button
              onClick={(e) => handleSaveRename(c.id, e)}
              className="p-0.5 rounded hover:bg-slate-800 text-emerald-400"
            >
              <Check className="h-3 w-3" />
            </button>
          ) : (
            <>
              <button
                onClick={(e) => handleTogglePin(c.id, c.is_pinned, e)}
                title={c.is_pinned ? "Unpin" : "Pin"}
                className={`p-0.5 rounded hover:bg-slate-800 ${c.is_pinned ? "text-blue-400" : "text-slate-500 hover:text-slate-300"}`}
              >
                <Plus className={`h-3 w-3 ${c.is_pinned ? "rotate-45" : ""}`} />
              </button>
              <button
                onClick={(e) => handleStartRename(c.id, c.title, e)}
                className="p-0.5 rounded hover:bg-slate-800 text-slate-500 hover:text-slate-300"
              >
                <Edit2 className="h-3 w-3" />
              </button>
              <button
                onClick={(e) => handleDeleteChat(c.id, e)}
                className="p-0.5 rounded hover:bg-slate-800 text-slate-500 hover:text-red-400"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </>
          )}
        </div>
      </div>
    );
  }
}
