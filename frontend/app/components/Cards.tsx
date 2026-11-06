import { Icon, type IconName } from "./Icon";

type Tone = "blue" | "green" | "red" | "slate";

const TONE_CLASSES: Record<Tone, string> = {
  blue: "bg-blue-50 text-blue-700",
  green: "bg-emerald-50 text-emerald-700",
  red: "bg-rose-50 text-rose-700",
  slate: "bg-slate-100 text-slate-600",
};

export function MetricCard({
  label,
  value,
  detail,
  icon,
  tone = "blue",
}: {
  label: string;
  value: string | number;
  detail: string;
  icon: IconName;
  tone?: Tone;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500">{label}</p>
          <p className="mt-3 text-3xl font-bold tracking-tight">{value}</p>
        </div>
        <div className={`rounded-xl p-2.5 ${TONE_CLASSES[tone]}`}>
          <Icon name={icon} />
        </div>
      </div>
      <p className="mt-4 text-[11px] text-slate-400">{detail}</p>
    </div>
  );
}

export function StatusCard({
  label,
  value,
  healthy,
  icon,
  note,
}: {
  label: string;
  value: string;
  healthy: boolean;
  icon: IconName;
  note?: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-slate-100 p-2.5 text-slate-600">
          <Icon name={icon} />
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500">{label}</p>
          <p className="mt-0.5 text-sm font-bold capitalize">{value}</p>
          {note && <p className="text-[10px] text-slate-400">{note}</p>}
        </div>
      </div>
      <span
        className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase ${
          healthy ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
        }`}
      >
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            healthy ? "bg-emerald-500" : "bg-amber-500"
          }`}
        />
        {healthy ? "Healthy" : "Check"}
      </span>
    </div>
  );
}

export function EmptyState({
  title,
  body,
  compact = false,
}: {
  title: string;
  body: string;
  compact?: boolean;
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center px-6 text-center ${
        compact ? "py-10" : "py-20"
      }`}
    >
      <div className="mb-3 rounded-full bg-slate-100 p-3 text-slate-400">
        <Icon name="activity" />
      </div>
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-1 text-xs text-slate-400">{body}</p>
    </div>
  );
}
