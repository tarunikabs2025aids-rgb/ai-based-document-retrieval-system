export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_admin: boolean;
}

export interface Citation {
  source: string;
  page?: number;
  chunk: string;
  official_website?: string;
  confidence: number;
  row_index?: number;
}

export interface ActionTimelineItem {
  step: number;
  title: string;
  description: string;
  timeline: string;
  status: "pending" | "completed" | "current";
}

export interface ActionPlan {
  required_documents: string[];
  application_form_url?: string;
  where_to_apply: string;
  office_address?: string;
  processing_time: string;
  application_fees: string;
  checklist: string[];
  timeline: ActionTimelineItem[];
  warnings: string[];
  notes: string[];
}

export interface Message {
  id: number;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  original_content?: string;
  language: string;
  citations?: Citation[];
  action_plan?: ActionPlan;
  confidence?: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface EligibilityProfile {
  age: number;
  gender: string;
  state: string;
  occupation: string;
  income: number;
  category: string;
  education: string;
  disability: boolean;
  farmer: boolean;
  student: boolean;
  business: boolean;
  veteran: boolean;
  widow: boolean;
  minority: boolean;
}

export interface SchemeEligibilityMatch {
  scheme_id: string;
  scheme_name: string;
  status: "ELIGIBLE" | "NOT_ELIGIBLE" | "MORE_INFO";
  reason: string;
  highlighted_conditions: string[];
  missing_information: string[];
}

export interface EligibilityCheckResponse {
  profile_summary: Record<string, string>;
  eligible_schemes: SchemeEligibilityMatch[];
  not_eligible_schemes: SchemeEligibilityMatch[];
  more_info_schemes: SchemeEligibilityMatch[];
}
