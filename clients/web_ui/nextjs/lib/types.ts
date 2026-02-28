export interface Session {
  id: string;
  title: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface Message {
  id: number;
  role: "user" | "agent" | "system";
  content: string;
  timestamp: string | null;
}

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface SessionWithMessages {
  session: Session;
  messages: Message[];
  tokens: TokenUsage;
}

export interface SSEMessage {
  type: "message" | "planning" | "action" | "final" | "error" | "done" | "cancelled";
  role?: "user" | "agent";
  content?: string;
  step_type?: string;
  step_number?: number;
  plan?: string;
  model_output?: string;
  code_action?: string;
  observations?: string;
  error?: string;
  output?: string;
  output_type?: "text" | "image";
  url?: string | null;
  mime_type?: string | null;
  is_final_answer?: boolean;
  token_usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
}

export interface CreateSessionResponse {
  session_id: string;
  redirect_url: string;
}

export interface DeleteSessionResponse {
  success: boolean;
  redirect_url: string;
}

export interface UpdateSessionResponse {
  success: boolean;
}

export interface ErrorResponse {
  error: string;
}
