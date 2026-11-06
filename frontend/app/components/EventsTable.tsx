import type { AuthEvent, Result } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import { EmptyState } from "./Cards";
import { Icon } from "./Icon";

export function ResultBadge({ result }: { result: Result }) {
  const accepted = result === "accept";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold ${
        accepted ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          accepted ? "bg-emerald-500" : "bg-rose-500"
        }`}
      />
      {accepted ? "Accepted" : "Rejected"}
    </span>
  );
}

export function Filters({
  username,
  result,
  onUsername,
  onResult,
}: {
  username: string;
  result: Result | "";
  onUsername: (value: string) => void;
  onResult: (value: Result | "") => void;
}) {
  return (
    <div className="flex flex-col gap-3 border-b border-slate-100 bg-slate-50/70 p-4 sm:flex-row">
      <div className="relative flex-1">
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
          <Icon name="search" />
        </span>
        <input
          aria-label="Search by username"
          placeholder="Search by username"
          value={username}
          onChange={(e) => onUsername(e.target.value)}
          className="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm outline-none focus:border-[#16736d]"
        />
      </div>
      <select
        aria-label="Filter by result"
        value={result}
        onChange={(e) => onResult(e.target.value as Result | "")}
        className="rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-[#16736d]"
      >
        <option value="">All outcomes</option>
        <option value="accept">Accepted</option>
        <option value="reject">Rejected</option>
      </select>
    </div>
  );
}

export function EventsTable({
  events,
  loading,
}: {
  events: AuthEvent[];
  loading: boolean;
}) {
  if (loading && !events.length) {
    return <EmptyState title="Loading activity" body="Waiting for events from the backend…" />;
  }
  if (!events.length) {
    return (
      <EmptyState
        title="No activity found"
        body="No authentication events match the current filters."
      />
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[680px] text-left text-sm">
        <thead className="text-[10px] font-bold uppercase tracking-[.14em] text-slate-400">
          <tr>
            <th className="px-6 py-4">Time</th>
            <th className="px-4 py-4">User</th>
            <th className="px-4 py-4">Outcome</th>
            <th className="px-4 py-4">Access point</th>
            <th className="px-4 py-4">Client</th>
            <th className="px-6 py-4">Method</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr
              key={event.event_id}
              className="border-t border-slate-100 hover:bg-slate-50"
            >
              <td className="whitespace-nowrap px-6 py-4 text-xs text-slate-500">
                {formatDateTime(event.timestamp)}
              </td>
              <td className="px-4 py-4 font-semibold text-slate-700">
                {event.username}
              </td>
              <td className="px-4 py-4">
                <ResultBadge result={event.result} />
              </td>
              <td className="px-4 py-4 text-xs text-slate-500">
                {event.called_station_id || event.nas_ip || "Local RADIUS"}
              </td>
              <td className="px-4 py-4 text-xs text-slate-500">
                {event.calling_station_id || "—"}
              </td>
              <td className="px-6 py-4 text-xs text-slate-500">
                {event.auth_method || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
