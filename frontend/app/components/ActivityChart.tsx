"use client";

import { useMemo } from "react";
import type { AuthEvent } from "../../lib/api";

// Honest, data-derived mini chart: buckets the currently loaded events by
// hour and shows accepted vs rejected counts. It reflects the events in
// view (the latest page), not the entire database — labelled as such.

interface Bucket {
  label: string;
  accept: number;
  reject: number;
}

function bucketByHour(events: AuthEvent[]): Bucket[] {
  const map = new Map<string, Bucket>();
  for (const event of events) {
    const date = new Date(event.timestamp);
    if (Number.isNaN(date.getTime())) continue;
    const key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}`;
    const label = date.toLocaleTimeString([], { hour: "2-digit" });
    const bucket = map.get(key) ?? { label, accept: 0, reject: 0 };
    if (event.result === "accept") bucket.accept += 1;
    else bucket.reject += 1;
    map.set(key, bucket);
  }
  // Oldest -> newest, cap to the most recent 12 buckets.
  return Array.from(map.values()).reverse().slice(-12);
}

export function ActivityChart({ events }: { events: AuthEvent[] }) {
  const buckets = useMemo(() => bucketByHour(events), [events]);
  const max = useMemo(
    () => Math.max(1, ...buckets.map((b) => b.accept + b.reject)),
    [buckets],
  );

  if (!buckets.length) {
    return (
      <p className="px-6 py-10 text-center text-xs text-slate-400">
        No events to chart yet.
      </p>
    );
  }

  return (
    <div className="px-6 py-6">
      <div className="flex h-40 items-end gap-2">
        {buckets.map((bucket, i) => {
          const total = bucket.accept + bucket.reject;
          const acceptH = (bucket.accept / max) * 100;
          const rejectH = (bucket.reject / max) * 100;
          return (
            <div key={i} className="flex flex-1 flex-col items-center gap-2">
              <div
                className="flex w-full flex-col justify-end"
                style={{ height: "100%" }}
                title={`${total} events — ${bucket.accept} accepted, ${bucket.reject} rejected`}
              >
                {rejectH > 0 && (
                  <div
                    className="w-full rounded-t bg-rose-400"
                    style={{ height: `${rejectH}%` }}
                  />
                )}
                {acceptH > 0 && (
                  <div
                    className={`w-full bg-emerald-400 ${rejectH > 0 ? "" : "rounded-t"}`}
                    style={{ height: `${acceptH}%` }}
                  />
                )}
              </div>
              <span className="text-[10px] text-slate-400">{bucket.label}</span>
            </div>
          );
        })}
      </div>
      <div className="mt-4 flex items-center gap-4 text-[11px] text-slate-500">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          Accepted
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-rose-400" />
          Rejected
        </span>
        <span className="ml-auto text-slate-400">Loaded events, grouped by hour</span>
      </div>
    </div>
  );
}
