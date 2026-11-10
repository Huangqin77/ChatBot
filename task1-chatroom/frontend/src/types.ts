export interface User { id: string; nickname: string; token: string }
export interface Room { id: string; name: string; description: string; created_at: string }
export interface Bot { id: string; name: string; role: string; system_prompt: string; tools: string[] }
export interface Message {
  id: string; room_id: string; kind: 'user' | 'bot' | 'system'; sender_id: string;
  sender_name: string; content: string; created_at: string; task_id: string | null; mode: string | null; client_id: string | null;
}
export interface Task {
  id: string; room_id: string; bot_id: string; bot_name: string; parent_id: string | null;
  root_id: string; depth: number; status: 'running' | 'completed' | 'failed';
  mode: string; input: string; output: string; error: string | null; created_at: string; completed_at: string | null;
}
export interface ToolCall {
  id: string; task_id: string; root_id: string; name: string; input: Record<string, unknown>;
  output: string; status: 'running' | 'completed' | 'failed'; child_task_id: string | null; created_at: string;
}
export interface Snapshot { room: Room; bots: Bot[]; messages: Message[]; tasks: Task[]; tool_calls: ToolCall[]; has_more: boolean }
export interface Health { mode: 'demo' | 'live'; model: string | null }
