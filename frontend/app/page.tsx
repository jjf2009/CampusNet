"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useDashboard } from "../lib/useDashboard";
import { formatDateTime, formatTime } from "../lib/format";
import { EmptyState, MetricCard, StatusCard } from "./components/Cards";
import { Icon } from "./components/Icon";
import { ActivityChart } from "./components/ActivityChart";
import { EventsTable, Filters } from "./components/EventsTable";

export default function Dashboard() {
  const d = useDashboard();
  const apiHealthy = d.overview?.api === "healthy" && !d.error;
  const radiusState = d.overview?.radius.status ?? "unknown";
  const ingestion = d.overview?.ingestion ?? "waiting";
  const uniqueUsers = useMemo(
    () => new Set(d.events.map((e) => e.username)).size,
    [d.events],
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">
        <div className="flex h-20 items-center gap-3 border-b border-slate-100 px-7">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#123f5a] text-white">
            <Icon name="shield" />
          </div>
          <div>
            <p className="text-sm font-bold">CampusNet</p>
            <p className="text-[10px] uppercase tracking-[.18em] text-slate-400">
              Network Ops
            </p>
          </div>
        </div>
        <nav className="flex-1 px-4 py-7">
          <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[.18em] text-slate-400">
            Workspace
          </p>
          <NavItem icon="grid" label="Overview" active />
          <NavItem icon="activity" label="Authentication" />
          <NavItem icon="users" label="Users & devices" />
          <p className="mb-3 mt-9 px-3 text-[10px] font-bold uppercase tracking-[.18em] text-slate-400">
            System
          </p>
          <NavItem icon="settings" label="Settings" />
        </nav>
        <div className="m-4 rounded-2xl bg-slate-50 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold">
            <span
              className={`h-2 w-2 rounded-full ${
                apiHealthy ? "bg-emerald-500" : "bg-amber-500"
              }`}
            />
            Local demo environment
          </div>
          <p className="mt-2 text-[11px] leading-5 text-slate-500">
            Prototype data stays on this machine. RADIUS auth is real; AP /
            802.1X and Google Workspace are not yet connected.
          </p>
        </div>
      </aside>

      {/* Main */}
      <main className="lg:pl-64">
        <header className="flex min-h-20 items-center justify-between border-b border-slate-200 bg-white px-5 py-4 sm:px-8">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#16736d]">
              Network operations
            </p>
            <h1 className="mt-1 text-xl font-bold tracking-tight sm:text-2xl">
              Authentication overview
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="hidden text-xs font-semibold text-slate-500 hover:text-[#123f5a] sm:block"
            >
              Student portal
            </Link>
            <button
              onClick={d.refresh}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold shadow-sm hover:border-[#16736d] hover:text-[#16736d]"
            >
              <Icon name="refresh" className={d.loading ? "animate-spin" : ""} />
              Refresh
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-[1500px] p-5 sm:p-8">
          <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-sm text-slate-500">Welcome back, administrator.</p>
              <p className="mt-1 text-xs text-slate-400">
                Monitoring access attempts from the local FreeRADIUS pipeline.
              </p>
            </div>
            <p className="text-right text-[11px] text-slate-400">
              {d.lastUpdated
                ? `Updated ${formatTime(d.lastUpdated.toISOString())}`
                : "Connecting to API…"}
            </p>
          </div>

          {d.error && (
            <div
              role="alert"
              className="mb-5 flex gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
            >
              <Icon name="x" />
              <div>
                <p className="font-semibold">Dashboard is disconnected</p>
                <p className="mt-1 text-xs">
                  Could not reach the backend. Start it with{" "}
                  <code>uvicorn app.main:app --port 8000</code> and refresh.{" "}
                  {d.error}
                </p>
              </div>
            </div>
          )}

          {/* Metrics */}
          <section className="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Total login attempts"
              value={d.stats?.total_attempts ?? "—"}
              detail="All recorded requests"
              icon="activity"
            />
            <MetricCard
              label="Unique users in view"
              value={uniqueUsers || (d.loading ? "—" : 0)}
              detail="Distinct usernames in the current page"
              icon="users"
              tone="slate"
            />
            <MetricCard
              label="Successful logins"
              value={d.stats?.accepted_attempts ?? "—"}
              detail="Access-Accept responses"
              icon="check"
              tone="green"
            />
            <MetricCard
              label="Failed logins"
              value={d.stats?.rejected_attempts ?? "—"}
              detail="Access-Reject responses"
              icon="x"
              tone="red"
            />
          </section>

          {/* Service status */}
          <section className="mb-5 grid gap-4 md:grid-cols-3">
            <StatusCard
              label="CampusNet API"
              value={d.overview?.api || (d.loading ? "checking" : "unavailable")}
              healthy={apiHealthy}
              icon="server"
            />
            <StatusCard
              label="FreeRADIUS"
              value={radiusState}
              healthy={radiusState === "active"}
              icon="wifi"
              note={d.overview?.radius.service}
            />
            <StatusCard
              label="Event ingestion"
              value={ingestion}
              healthy={ingestion === "ready"}
              icon="refresh"
            />
          </section>

          {/* Feed + side panels */}
          <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
            <div className="space-y-5">
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#16736d]">
                      Trend
                    </p>
                    <h2 className="mt-1 text-lg font-bold">Authentication activity</h2>
                  </div>
                </div>
                <ActivityChart events={d.events} />
              </div>

              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-6 py-5">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#16736d]">
                      Live feed
                    </p>
                    <h2 className="mt-1 text-lg font-bold">Recent activity</h2>
                  </div>
                  <p className="text-xs text-slate-400">
                    Last event: {formatDateTime(d.overview?.latest_event_time)}
                  </p>
                </div>
                <Filters
                  username={d.username}
                  result={d.result}
                  onUsername={d.setUsername}
                  onResult={d.setResult}
                />
                <EventsTable events={d.events} loading={d.loading} />
              </div>
            </div>

            <div className="space-y-5">
              <div className="rounded-2xl bg-[#123f5a] p-5 text-white shadow-sm">
                <div className="flex items-center gap-2 text-[#a8e0d5]">
                  <Icon name="shield" />
                  <span className="text-[10px] font-bold uppercase tracking-[.18em]">
                    Acceptance rate
                  </span>
                </div>
                <p className="mt-4 text-4xl font-bold">
                  {d.stats ? `${d.stats.acceptance_rate}%` : "—"}
                </p>
                <p className="mt-2 text-xs leading-5 text-slate-300">
                  Successful attempts compared with all recorded requests.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-100 px-5 py-5">
                  <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#16736d]">
                    Directory snapshot
                  </p>
                  <h2 className="mt-1 text-lg font-bold">User activity</h2>
                  <p className="mt-1 text-xs text-slate-400">
                    Accounts seen in events — not a full student directory.
                  </p>
                </div>
                {d.users.length ? (
                  <div className="divide-y divide-slate-100">
                    {d.users.slice(0, 6).map((user) => (
                      <div
                        key={user.username}
                        className="flex items-center justify-between px-5 py-4"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-700">
                            {user.username}
                          </p>
                          <p className="mt-1 text-[11px] text-slate-400">
                            {user.accepted} ok · {user.rejected} failed
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-bold">{user.attempts}</p>
                          <p className="text-[10px] text-slate-400">attempts</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="No users yet"
                    body="User activity appears after events arrive."
                    compact
                  />
                )}
              </div>
            </div>
          </section>

          <footer className="mt-6 flex flex-wrap justify-between gap-2 text-[11px] text-slate-400">
            <span>CampusNet local prototype · refreshes every 7 seconds</span>
            <span>Latest event: {formatDateTime(d.overview?.latest_event_time)}</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

function NavItem({
  icon,
  label,
  active = false,
}: {
  icon: "grid" | "activity" | "users" | "settings";
  label: string;
  active?: boolean;
}) {
  return (
    <div
      className={`mb-1 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold ${
        active ? "bg-[#e7f3f1] text-[#126d68]" : "text-slate-500"
      }`}
    >
      <Icon name={icon} />
      {label}
    </div>
  );
}
