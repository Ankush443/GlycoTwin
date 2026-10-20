import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { WearableDay } from "../api/types";
import { EmptyState } from "./states";

interface SeriesSpec {
  key: keyof WearableDay;
  label: string;
  unit: string;
  color: string;
  integer?: boolean;
}

/**
 * Wearable-like daily series. Charts label units explicitly and use the
 * recorded synthetic dates on the x-axis.
 */
const SERIES: SeriesSpec[] = [
  { key: "steps", label: "Steps", unit: "steps/day", color: "#2563eb", integer: true },
  { key: "resting_heart_rate_bpm", label: "Resting heart rate", unit: "bpm", color: "#dc2626" },
  { key: "sleep_duration_hours", label: "Sleep duration", unit: "hours/night", color: "#7c3aed" },
  { key: "active_minutes", label: "Active minutes", unit: "min/day", color: "#059669" },
  { key: "sleep_consistency_percent", label: "Sleep consistency", unit: "%", color: "#d97706" },
];

function TrendChart({ days, spec }: { days: WearableDay[]; spec: SeriesSpec }) {
  const data = days.map((day) => ({
    date: day.recorded_on.slice(5), // MM-DD keeps the axis readable
    value: day[spec.key] as number,
  }));

  return (
    <figure className="rounded-lg border border-slate-200 bg-white p-3">
      <figcaption className="text-xs font-semibold text-slate-600">
        {spec.label} <span className="font-normal text-slate-400">({spec.unit})</span>
      </figcaption>
      <div className="mt-2 h-36">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 10 }} tickLine={false} width={54} />
            <Tooltip
              formatter={(value) => [`${value} ${spec.unit}`, spec.label]}
              labelFormatter={(label) => `Recorded 2026-${label}`}
              contentStyle={{ fontSize: 12 }}
            />
            <Area type="monotone" dataKey="value" stroke={spec.color} fill={spec.color} fillOpacity={0.12} strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
}

export function WearableTrends({ days }: { days: WearableDay[] }) {
  if (days.length === 0) {
    return <EmptyState>No wearable-like observations for this synthetic patient.</EmptyState>;
  }
  const sorted = [...days].sort((a, b) => a.recorded_on.localeCompare(b.recorded_on));
  const first = sorted[0].recorded_on;
  const last = sorted.at(-1)!.recorded_on;

  return (
    <section aria-labelledby="wearable-heading">
      <div className="flex items-baseline justify-between">
        <h2 id="wearable-heading" className="text-sm font-semibold uppercase tracking-wide text-slate-600">
          Wearable-like daily trends
        </h2>
        <p className="text-xs text-slate-400">
          {sorted.length} synthetic days · {first} → {last}
        </p>
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {SERIES.map((spec) => (
          <TrendChart key={spec.key} days={sorted} spec={spec} />
        ))}
      </div>
    </section>
  );
}
