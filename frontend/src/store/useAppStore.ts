import { create } from "zustand";
import { User, Conversation, Citation, EligibilityProfile, EligibilityCheckResponse } from "../types";

interface AppState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  conversations: Conversation[];
  activeConversationId: string | null;
  isEligibilityModalOpen: boolean;
  activeCitation: Citation | null;
  activeSchemeName: string | null;
  eligibilityProfile: EligibilityProfile | null;
  eligibilityResults: EligibilityCheckResponse | null;
  
  setUser: (user: User | null) => void;
  setAuth: (token: string | null, refreshToken: string | null) => void;
  logout: () => void;
  setConversations: (conversations: Conversation[]) => void;
  setActiveConversationId: (id: string | null) => void;
  setEligibilityModalOpen: (isOpen: boolean) => void;
  setActiveCitation: (citation: Citation | null, schemeName: string | null) => void;
  setEligibilityProfile: (profile: EligibilityProfile | null) => void;
  setEligibilityResults: (results: EligibilityCheckResponse | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("token") : null,
  refreshToken: typeof window !== "undefined" ? localStorage.getItem("refreshToken") : null,
  conversations: [],
  activeConversationId: null,
  isEligibilityModalOpen: false,
  activeCitation: null,
  activeSchemeName: null,
  eligibilityProfile: null,
  eligibilityResults: null,

  setUser: (user) => set({ user }),
  setAuth: (token, refreshToken) => {
    if (token && refreshToken) {
      localStorage.setItem("token", token);
      localStorage.setItem("refreshToken", refreshToken);
    } else {
      localStorage.removeItem("token");
      localStorage.removeItem("refreshToken");
    }
    set({ token, refreshToken });
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    set({ user: null, token: null, refreshToken: null, conversations: [], activeConversationId: null, eligibilityProfile: null, eligibilityResults: null });
  },
  setConversations: (conversations) => set({ conversations }),
  setActiveConversationId: (activeConversationId) => set({ activeConversationId }),
  setEligibilityModalOpen: (isEligibilityModalOpen) => set({ isEligibilityModalOpen }),
  setActiveCitation: (activeCitation, activeSchemeName) => set({ activeCitation, activeSchemeName }),
  setEligibilityProfile: (eligibilityProfile) => set({ eligibilityProfile }),
  setEligibilityResults: (eligibilityResults) => set({ eligibilityResults }),
}));
