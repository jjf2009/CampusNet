"use client";
import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
type Event = { event_id: string; timestamp: string; username: string; result: "accept" | "reject"; called_station_id?: string; calling_station_id?: string };
type Stats = { total_attempts: number; accepted_attempts: number; rejected_attempts: number; acceptance_rate: number };
type Overview = { api: string; radius: { status: string }; ingestion: string; latest_event_time?: string; event_total: number };

async function get<T>(path: string): Promise<T> { const response = await fetch(`${API}${path}`, { cache: "no-store" }); if (!response.ok) throw new Error(`Request failed (${response.status})`); return response.json(); }
function formatTime(value?: string) { return value ? new Date(value).toLocaleString() : "—"; }

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [username, setUsername] = useState("");
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => { setLoading(true); try { const query = new URLSearchParams({ limit: "50" }); if (username) query.set("username", username); if (result) query.set("result", result); const [nextStats, nextOverview, nextEvents] = await Promise.all([get<Stats>("/api/stats"), get<Overview>("/api/system/overview"), get<{items: Event[]}>(`/api/events?${query}`)]); setStats(nextStats); setOverview(nextOverview); setEvents(nextEvents.items); setError(""); } catch (cause) { setError(cause instanceof Error ? cause.message : "Backend unavailable"); } finally { setLoading(false); } }, [username, result]);
  useEffect(() => { void load(); const timer = setInterval(() => void load(), 7000); return () => clearInterval(timer); }, [load]);
  return <main className="shell"><header><div><p className="eyebrow">CAMPUS NETWORK OPERATIONS</p><h1>CampusNet</h1></div><span className="environment">LOCAL DEMO</span><button onClick={() => void load()}>Refresh</button></header>
    {error && <div className="alert">Unable to reach CampusNet API. {error}</div>}
    <section className="status-grid"><Status label="API" value={overview?.api || (loading ? "Checking" : "Unavailable")} good={overview?.api === "healthy"} /><Status label="RADIUS" value={overview?.radius.status || "Unknown"} good={overview?.radius.status === "active"} /><Status label="INGESTION" value={overview?.ingestion || "Waiting"} good={overview?.ingestion === "ready"} /></section>
    <section className="metrics"><Metric label="Total attempts" value={stats?.total_attempts ?? "—"} /><Metric label="Accepted" value={stats?.accepted_attempts ?? "—"} tone="good" /><Metric label="Rejected" value={stats?.rejected_attempts ?? "—"} tone="bad" /><Metric label="Acceptance rate" value={stats ? `${stats.acceptance_rate}%` : "—"} /></section>
    <section className="panel"><div className="panel-head"><div><p className="eyebrow">AUTHENTICATION ACTIVITY</p><h2>Recent events</h2></div><p className="muted">Last event: {formatTime(overview?.latest_event_time)}</p></div><div className="filters"><input aria-label="Search username" placeholder="Search username" value={username} onChange={e => setUsername(e.target.value)} /><select aria-label="Filter result" value={result} onChange={e => setResult(e.target.value)}><option value="">All results</option><option value="accept">Accepted</option><option value="reject">Rejected</option></select></div>{loading && !events.length ? <p className="empty">Loading events…</p> : !events.length ? <p className="empty">No authentication events match these filters.</p> : <div className="table-wrap"><table><thead><tr><th>Time</th><th>Username</th><th>Result</th><th>AP / NAS</th><th>Client</th></tr></thead><tbody>{events.map(item => <tr key={item.event_id}><td>{formatTime(item.timestamp)}</td><td>{item.username}</td><td><span className={`badge ${item.result}`}>{item.result}</span></td><td>{item.called_station_id || "—"}</td><td>{item.calling_station_id || "—"}</td></tr>)}</tbody></table></div>}</section><footer>Data refreshes every 7 seconds · Local prototype · Backend status is independently verified</footer></main>;
}
function Status({ label, value, good }: { label: string; value: string; good?: boolean }) { return <div className="status-card"><span className={`dot ${good ? "good" : ""}`} /><div><p className="eyebrow">{label}</p><strong>{value}</strong></div></div>; }
function Metric({ label, value, tone }: { label: string; value: string | number; tone?: string }) { return <div className="metric"><p>{label}</p><strong className={tone || ""}>{value}</strong></div>; }

