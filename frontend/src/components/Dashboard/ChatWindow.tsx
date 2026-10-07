"use client";

import React, { useState, useEffect, useRef } from "react";
import { useAppStore } from "../../store/useAppStore";
import { api } from "../../services/api";
import { 
  Send, Sparkles, AlertTriangle, ShieldCheck, Download, 
  Copy, Check, ThumbsUp, ThumbsDown, Loader2, RefreshCw 
} from "lucide-react";

export default function ChatWindow() {
  const { 
    activeConversationId, setActiveConversationId, 
    setActiveCitation, setEligibilityResults, setEligibilityProfile 
  } = useAppStore();

  const [messages, setMessages] = useState<any[]>([]);
  const [inputText, setInputText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [ratedMessages, setRatedMessages] = useState<Record<number, number>>({});
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat messages when active conversation changes
  const loadConversation = async () => {
    if (!activeConversationId) {
      setMessages([]);
      return;
    }
    try {
      const response = await api.get(`/history/${activeConversationId}`);
      setMessages(response.data.messages || []);
      
      // Look for latest action plan in the conversation to sync with PolicyPath
      const assistantMessages = (response.data.messages || []).filter((m: any) => m.role === "assistant" && m.action_plan);
      if (assistantMessages.length > 0) {
        const latestPlan = assistantMessages[assistantMessages.length - 1].action_plan;
        
        // Formulate dummy profile from latest plan for dashboard sync
        setEligibilityProfile({
          age: 25,
          gender: "Male",
          state: latestPlan.where_to_apply.includes("Tamil Nadu") ? "Tamil Nadu" : "All India",
          occupation: "Farmer",
          income: 150000,
          category: "General",
          education: "Secondary",
          disability: false,
          farmer: true,
          student: false,
          business: false,
          veteran: false,
          widow: false,
          minority: false
        });
        
        setEligibilityResults({
          profile_summary: { State: "Synched from Chat" },
          eligible_schemes: [{
            scheme_id: "active",
            scheme_name: latestPlan.where_to_apply.includes("Tamil Nadu") ? "State Scheme" : "Central Scheme",
            status: "ELIGIBLE",
            reason: "Retrieved from recent active chatbot action guidelines.",
            highlighted_conditions: latestPlan.checklist || [],
            missing_information: []
          }],
          not_eligible_schemes: [],
          more_info_schemes: []
        });
      }
    } catch (err) {
      console.error("Failed to load conversation details:", err);
    }
  };

  useEffect(() => {
    loadConversation();
  }, [activeConversationId]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text || isStreaming) return;

    if (!textToSend) setInputText("");
    setIsStreaming(true);

    // Append user message instantly
    const userMsg = {
      id: Date.now(),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // Create assistant message placeholder
    const assistantMsgId = Date.now() + 1;
    const placeholderMsg = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      confidence: 0,
      citations: [],
      action_plan: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, placeholderMsg]);

    try {
      const token = useAppStore.getState().token;
      const response = await fetch("http://localhost:8000/api/chat/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          message: text,
          conversation_id: activeConversationId || undefined,
        }),
      });

      if (!response.body) throw new Error("Null response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      let streamingText = "";
      let finalMsgId = assistantMsgId;
      let finalCitations: any[] = [];
      let finalActionPlan: any = null;
      let finalConfidence = 85;
      let finalConvId = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // keep incomplete line in buffer

        for (const line of lines) {
          const cleanLine = line.trim();
          if (!cleanLine.startsWith("data: ")) continue;

          const dataStr = cleanLine.substring(6).trim();
          if (dataStr === "[DONE]") {
            break;
          }

          try {
            const data = JSON.parse(dataStr);
            if (data.type === "delta") {
              streamingText += data.content;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, content: streamingText } : m
                )
              );
            } else if (data.type === "msg_info") {
              finalMsgId = data.message_id;
              finalConfidence = data.confidence;
              finalConvId = data.conversation_id;
              if (!activeConversationId && finalConvId) {
                setActiveConversationId(finalConvId);
              }
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, id: finalMsgId, confidence: finalConfidence } : m
                )
              );
            } else if (data.type === "citations") {
              finalCitations = data.content;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === finalMsgId || m.id === assistantMsgId
                    ? { ...m, citations: finalCitations }
                    : m
                )
              );
            } else if (data.type === "action_plan") {
              finalActionPlan = data.content;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === finalMsgId || m.id === assistantMsgId
                    ? { ...m, action_plan: finalActionPlan }
                    : m
                )
              );
              
              // Sync loaded action plan to Policy Path layout
              setEligibilityProfile({
                age: 25,
                gender: "Male",
                state: finalActionPlan.where_to_apply.includes("Tamil Nadu") ? "Tamil Nadu" : "All India",
                occupation: "Farmer",
                income: 180000,
                category: "General",
                education: "Secondary",
                disability: false,
                farmer: true,
                student: false,
                business: false,
                veteran: false,
                widow: false,
                minority: false
              });
              setEligibilityResults({
                profile_summary: { State: "Syncing..." },
                eligible_schemes: [{
                  scheme_id: "active",
                  scheme_name: finalActionPlan.where_to_apply.includes("Tamil Nadu") ? "State Scheme" : "Central Scheme",
                  status: "ELIGIBLE",
                  reason: "Fetched from active query timeline.",
                  highlighted_conditions: finalActionPlan.checklist || [],
                  missing_information: []
                }],
                not_eligible_schemes: [],
                more_info_schemes: []
              });
            }
          } catch (e) {
            console.error("Error parsing SSE line:", e);
          }
        }
      }
    } catch (err) {
      console.error("Streaming failed:", err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: "Error: Failed to connect to welfare assistant server. Please retry." }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  const handleCopyText = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleFeedback = async (msgId: number, rating: number) => {
    try {
      await api.post("/feedback", {
        message_id: msgId,
        rating: rating,
      });
      setRatedMessages((prev) => ({
        ...prev,
        [msgId]: rating,
      }));
    } catch (err) {
      console.error(err);
    }
  };

  const handleDownloadPDF = (msgId: number) => {
    // Navigate directly to browser attachment endpoint
    const token = useAppStore.getState().token;
    window.open(`http://localhost:8000/api/pdf-export/export/${msgId}?token=${token}`, "_blank");
  };

  // Simple Markdown Parsing Helper
  const parseMarkdown = (text: string, citations: any[] = []) => {
    if (!text) return "";
    
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Headings
    html = html.replace(/^### (.*$)/gim, '<h4 class="text-sm font-bold text-white mt-4 mb-2">$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3 class="text-base font-bold text-white mt-5 mb-2">$1</h3>');
    html = html.replace(/^\* (.*$)/gim, '<li class="ml-4 list-disc text-slate-300 py-0.5">$1</li>');
    html = html.replace(/^- (.*$)/gim, '<li class="ml-4 list-disc text-slate-300 py-0.5">$1</li>');

    // Bold tags
    html = html.replace(/\*\*(.*?)\*\*/g, '<b class="font-bold text-slate-200">$1</b>');
    html = html.replace(/__(.*?)__/g, '<b class="font-bold text-slate-200">$1</b>');

    // Lines break
    html = html.replace(/\n/g, "<br />");

    // Inject citation badges click handlers
    if (citations && citations.length > 0) {
      citations.forEach((cit, index) => {
        const badgeHtml = `<button class="inline-flex items-center justify-center px-1.5 py-0.5 ml-1 text-[9px] font-bold text-blue-400 bg-blue-500/10 border border-blue-500/20 rounded hover:bg-blue-500/20 transition-colors select-none cursor-pointer" onclick="window.__openCitation(${index})">[${index + 1}]</button>`;
        // Find reference keyword or number match in content and replace
        html = html.replace(new RegExp(`\\[${index + 1}\\]`, "g"), badgeHtml);
      });
    }

    return html;
  };

  // Expose global callback for badge clicks
  useEffect(() => {
    if (typeof window !== "undefined") {
      (window as any).__openCitation = (index: number) => {
        // Retrieve latest assistant message citations
        const latestAssistant = [...messages].reverse().find((m) => m.role === "assistant");
        if (latestAssistant && latestAssistant.citations && latestAssistant.citations[index]) {
          const cit = latestAssistant.citations[index];
          setActiveCitation(cit, latestAssistant.content.substring(0, 40) + "...");
        }
      };
    }
  }, [messages, setActiveCitation]);

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100">
      {/* Top Navbar Header */}
      <div className="h-16 border-b border-slate-900 px-6 flex items-center justify-between bg-slate-950/40 backdrop-blur-md sticky top-0 z-20">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-blue-500 animate-pulse" />
          <div>
            <h2 className="text-sm font-bold text-white">GovAssist AI Schemes Chat</h2>
            <p className="text-[10px] text-slate-500">Retrieval Grounded Policy Advisory</p>
          </div>
        </div>
      </div>

      {/* Messages Window Scroll Panel */}
      <div className="flex-grow overflow-y-auto px-6 py-6 space-y-6 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto">
            <ShieldCheck className="h-12 w-12 text-blue-500 mb-4 animate-bounce" />
            <h3 className="text-base font-bold text-white mb-2">How can I assist you with government schemes today?</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Ask naturally. Try typing: <br />
              <span className="text-blue-400">"I'm a farmer from Tamil Nadu. What schemes can help me?"</span> or <br />
              <span className="text-blue-400">"I want a business loan to start a food manufacturing startup."</span>
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
              <button
                onClick={() => handleSendMessage("I am a farmer from Tamil Nadu. What schemes can help me?")}
                className="text-left bg-slate-900/50 border border-slate-800 hover:border-slate-700 p-3 rounded-xl text-xs text-slate-300 transition-all focus:outline-none cursor-pointer"
              >
                🌾 "I am a farmer in Tamil Nadu. Show me agricultural benefits."
              </button>
              <button
                onClick={() => handleSendMessage("I am a college student. Show me scholarship schemes.")}
                className="text-left bg-slate-900/50 border border-slate-800 hover:border-slate-700 p-3 rounded-xl text-xs text-slate-300 transition-all focus:outline-none cursor-pointer"
              >
                🎓 "Show scholarships for college students."
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6 max-w-4xl mx-auto">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                {msg.role === "assistant" && (
                  <div className="h-8 w-8 rounded-full bg-blue-600/10 border border-blue-500/20 flex items-center justify-center shrink-0">
                    <Sparkles className="h-4 w-4 text-blue-400" />
                  </div>
                )}
                
                <div className={`flex flex-col gap-1.5 max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <div
                    className={`px-4 py-3 rounded-2xl text-sm leading-relaxed border ${
                      msg.role === "user"
                        ? "bg-blue-600 border-blue-500 text-white rounded-tr-none"
                        : "bg-slate-900/40 border-slate-800 text-slate-100 rounded-tl-none"
                    }`}
                  >
                    {msg.role === "user" ? (
                      msg.content
                    ) : (
                      <div 
                        dangerouslySetInnerHTML={{ __html: parseMarkdown(msg.content, msg.citations) }}
                        className="space-y-2 prose prose-invert prose-sm"
                      />
                    )}
                  </div>

                  {/* Actions bar for Assistant response */}
                  {msg.role === "assistant" && msg.content && (
                    <div className="flex items-center gap-4 text-xs text-slate-500 px-1 mt-0.5">
                      {msg.confidence !== undefined && msg.confidence > 0 && (
                        <span className="text-[10px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                          Confidence: {msg.confidence}%
                        </span>
                      )}

                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleCopyText(msg.content, msg.id)}
                          className="p-1 rounded hover:bg-slate-900 hover:text-white transition-colors cursor-pointer"
                          title="Copy Answer"
                        >
                          {copiedId === msg.id ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                        </button>
                        
                        {msg.action_plan && (
                          <button
                            onClick={() => handleDownloadPDF(msg.id)}
                            className="p-1 rounded hover:bg-slate-900 hover:text-white transition-colors cursor-pointer flex items-center gap-0.5"
                            title="Download Action Plan PDF"
                          >
                            <Download className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>

                      {/* Feedback rating buttons */}
                      <div className="flex items-center gap-1.5 border-l border-slate-800 pl-4">
                        <button
                          onClick={() => handleFeedback(msg.id, 1)}
                          className={`p-1 rounded hover:bg-slate-900 transition-colors cursor-pointer ${
                            ratedMessages[msg.id] === 1 ? "text-emerald-400" : "hover:text-emerald-400"
                          }`}
                          title="Upvote response"
                        >
                          <ThumbsUp className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleFeedback(msg.id, -1)}
                          className={`p-1 rounded hover:bg-slate-900 transition-colors cursor-pointer ${
                            ratedMessages[msg.id] === -1 ? "text-red-400" : "hover:text-red-400"
                          }`}
                          title="Downvote response"
                        >
                          <ThumbsDown className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isStreaming && (
              <div className="flex gap-4 justify-start">
                <div className="h-8 w-8 rounded-full bg-blue-600/10 border border-blue-500/20 flex items-center justify-center shrink-0">
                  <Sparkles className="h-4 w-4 text-blue-400" />
                </div>
                <div className="flex items-center gap-2 bg-slate-900/20 border border-slate-800/50 px-4 py-2.5 rounded-2xl rounded-tl-none text-slate-400 text-xs">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Generating grounded answer...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* Message input bar */}
      <div className="p-4 border-t border-slate-900 bg-slate-950/60 sticky bottom-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center gap-2 bg-slate-900/50 border border-slate-850 rounded-xl px-4 py-2">
          <input
            type="text"
            placeholder={isStreaming ? "Generating..." : "Ask GovAssist AI about government schemes..."}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !isStreaming) {
                handleSendMessage();
              }
            }}
            disabled={isStreaming}
            className="flex-grow bg-transparent text-sm focus:outline-none text-white placeholder-slate-500 disabled:cursor-not-allowed py-1.5"
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={isStreaming || !inputText.trim()}
            className="p-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed shrink-0"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
