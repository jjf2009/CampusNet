// Typed API client for the CampusNet backend.
// All metrics shown in the UI come from these calls — never hardcoded.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export type Result = "accept" | "reject";
export type IngestionState = "waiting" | "ready" | "degraded";
export type RadiusState = "active" | "inactive" | "failed" | "unknown";

export interface AuthEvent {
  id: number;
  event_id: string;
  timestamp: string;
  username: string;
  result: Result;
  nas_ip: string | null;
  nas_port: number | null;
  calling_station_id: string | null;
  called_station_id: string | null;
  auth_method: string | null;
  source: string;
}

export interface EventPage {
  items: AuthEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface Stats {
  total_attempts: number;
  accepted_attempts: number;
  rejected_attempts: number;
  acceptance_rate: number;
  window_hours: number;
  window_total: number;
  window_accepted: number;
  window_rejected: number;
}

export interface RadiusStatus {
  status: RadiusState;
  service: string;
}

export interface SystemOverview {
  api: string;
  database: string;
  radius: RadiusStatus;
  ingestion: IngestionState;
  event_total: number;
  latest_event_time: string | null;
}

export interface UserActivity {
  username: string;
  attempts: number;
  accepted: number;
  rejected: number;
  last_seen: string | null;
}

export interface EventFilters {
  result?: Result | "";
  username?: string;
  limit?: number;
}

async function getJSON<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store", signal });
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

export function fetchStats(signal?: AbortSignal) {
  return getJSON<Stats>("/api/stats", signal);
}

export function fetchOverview(signal?: AbortSignal) {
  return getJSON<SystemOverview>("/api/system/overview", signal);
}

export function fetchUsers(signal?: AbortSignal) {
  return getJSON<UserActivity[]>("/api/users", signal);
}

export function fetchEvents(filters: EventFilters = {}, signal?: AbortSignal) {
  const params = new URLSearchParams({ limit: String(filters.limit ?? 50) });
  if (filters.username) params.set("username", filters.username);
  if (filters.result) params.set("result", filters.result);
  return getJSON<EventPage>(`/api/events?${params.toString()}`, signal);
}
