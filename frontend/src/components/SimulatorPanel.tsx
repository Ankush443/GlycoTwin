import { useCallback, useMemo, useState } from "react";
import { api, ApiError } from "../api/client";
import type { PatientDetail, ScenarioFields, SimulationResponse } from "../api/types";
import { EmptyState, ErrorState, LoadingState } from "./states";

interface FieldSpec {
  name: keyof ScenarioFields;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
}

/** Matches the API's validated ranges for each supported scenario field. */
const FIELDS: FieldSpec[] = [
  { name: "steps_14d_mean", label: "Mean daily steps (14d)", unit: "steps/day", min: 0, max: 30_000, step: 500 },
  { name: "active_minutes_14d_mean", label: "Mean active minutes (14d)", unit: "min/day", min: 0, max: 300, step: 5 },
  {
    name: "resting_heart_rate_14d_mean",
    label: "Mean resting heart rate (14d)",
    unit: "bpm",
    min: 30,
    max: 120,
    step: 1,
  },
  { name: "sleep_duration_14d_mean", label: "Mean sleep duration (14d)", unit: "hours/night", min: 0, max: 14, step: 0.5 },
  { name: "sleep_consistency_14d_mean", label: "Mean sleep consistency (14d)", unit: "%", min: 0, max: 100, step: 1 },
];

/** Observed 14-day means from the patient's synthetic wearable rows. */
function observedMeans(detail: PatientDetail): Record<string, number> {
  const days = detail.wearable_daily;
  const n = days.length || 1;
  const sum = (pick: (row: (typeof days)[number]) => number) => days.reduce((acc, row) => acc + pick(row), 0);
  return {
    steps_14d_mean: sum((row) => row.steps) / n,
    active_minutes_14d_mean: sum((row) => row.active_minutes) / n,
    resting_heart_rate_14d_mean: sum((row) => row.resting_heart_rate_bpm) / n,
    sleep_duration_14d_mean: sum((row) => row.sleep_duration_hours) / n,
    sleep_consistency_14d_mean: sum((row) => row.sleep_consistency_percent) / n,
  };
}

/**
 * What-if scenario simulator. Each control starts at the patient's observed
 * synthetic 14-day mean; only changed fields are sent. The result compares the
 * model's baseline estimate with the scenario estimate and is labelled an
 * exploratory model response, not a treatment outcome.
 */
export function SimulatorPanel({ detail }: { detail: PatientDetail }) {
  const observed = useMemo(() => observedMeans(detail), [detail]);
  const [overrides, setOverrides] = useState<Partial<Record<keyof ScenarioFields, number>>>({});
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const changedFields = Object.keys(overrides).filter(
    (name) => overrides[name as keyof ScenarioFields] !== undefined,
  ).length;

  const setField = (name: keyof ScenarioFields, value: string) => {
    const numeric = Number(value);
    setOverrides((current) => ({ ...current, [name]: Number.isFinite(numeric) ? numeric : undefined }));
  };

  const reset = () => {
    setOverrides({});
    setResult(null);
    setError(null);
  };

  const run = useCallback(() => {
    setError(null);
    setLoading(true);
    setResult(null);
    const payload: ScenarioFields = {};
    for (const [name, value] of Object.entries(overrides)) {
      if (value !== undefined) payload[name as keyof ScenarioFields] = value;
    }
    api
      .simulate(detail.patient_id, payload)
      .then(setResult)
      .catch((caught: unknown) => setError(caught instanceof ApiError ? caught.message : String(caught)))
      .finally(() => setLoading(false));
  }, [detail.patient_id, overrides]);

  if (FIELDS.length === 0) {
    return <EmptyState>The selected model does not support scenario inputs.</EmptyState>;
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4" aria-labelledby="simulator-heading">
      <h2 id="simulator-heading" className="text-sm font-semibold uppercase tracking-wide text-slate-600">
        What-if scenario simulator
      </h2>
      <p className="mt-2 text-xs text-slate-500">
        Adjust supported synthetic wearable aggregates and re-run the same saved pipeline. Outputs are exploratory
        model scenarios — not guaranteed treatment outcomes. Clinical inputs (HbA1c, glucose, BMI) cannot be simulated.
      </p>

      <div className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-2">
        {FIELDS.map((field) => {
          const current = overrides[field.name] ?? observed[field.name];
          const changed = overrides[field.name] !== undefined;
          return (
            <label key={field.name} className="block text-xs">
              <span className="flex items-baseline justify-between">
                <span className="font-medium text-slate-700">{field.label}</span>
                {changed && (
                  <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-blue-700">
                    changed
                  </span>
                )}
              </span>
              <span className="mt-1 flex items-center gap-2">
                <input
                  type="range"
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  value={current}
                  onChange={(event) => setField(field.name, event.target.value)}
                  className="flex-1 accent-slate-700"
                />
                <input
                  type="number"
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  value={current}
                  onChange={(event) => setField(field.name, event.target.value)}
                  className="w-24 rounded border border-slate-300 px-2 py-1 text-right tabular-nums focus:border-slate-500 focus:outline-none"
                />
              </span>
              <span className="mt-0.5 block text-[10px] text-slate-400">
                observed {observed[field.name].toFixed(1)} {field.unit}
              </span>
            </label>
          );
        })}
      </div>

      <div className="mt-4 flex items-center gap-3">
        <button
          type="button"
          onClick={run}
          disabled={loading || changedFields === 0}
          className="rounded bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {loading ? "Simulating…" : "Run scenario"}
        </button>
        <button
          type="button"
          onClick={reset}
          className="rounded border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
        >
          Reset
        </button>
        {changedFields === 0 && <span className="text-xs text-slate-400">Change at least one input to simulate.</span>}
      </div>

      <div className="mt-4">
        {loading ? (
          <LoadingState label="Re-running the saved pipeline…" />
        ) : error ? (
          <ErrorState title="Simulation failed" message={error} onRetry={run} />
        ) : result ? (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-6 text-sm">
              <p>
                <span className="block text-xs text-slate-500">Baseline estimate</span>
                <span className="text-xl font-semibold tabular-nums text-slate-700">
                  {result.baseline_estimated_hba1c_percent.toFixed(2)}%
                </span>
              </p>
              <span aria-hidden className="text-slate-300">
                →
              </span>
              <p>
                <span className="block text-xs text-slate-500">Scenario estimate</span>
                <span className="text-xl font-semibold tabular-nums text-slate-900">
                  {result.scenario_estimated_hba1c_percent.toFixed(2)}%
                </span>
              </p>
              <p className="rounded bg-slate-100 px-2.5 py-1.5">
                <span className="block text-xs text-slate-500">Difference</span>
                <span
                  className={`text-xl font-semibold tabular-nums ${
                    result.scenario_minus_baseline <= 0 ? "text-emerald-700" : "text-rose-700"
                  }`}
                >
                  {result.scenario_minus_baseline >= 0 ? "+" : ""}
                  {result.scenario_minus_baseline.toFixed(3)}
                </span>
              </p>
            </div>

            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-left uppercase tracking-wide text-slate-400">
                  <th scope="col" className="py-1 font-semibold">
                    Feature
                  </th>
                  <th scope="col" className="py-1 text-right font-semibold">
                    Observed
                  </th>
                  <th scope="col" className="py-1 text-right font-semibold">
                    Scenario
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.modifications).map(([name, mod]) => (
                  <tr key={name} className="border-b border-slate-100 last:border-0">
                    <td className="py-1 text-slate-600">{name}</td>
                    <td className="py-1 text-right tabular-nums">{mod.observed_synthetic_feature_value.toFixed(1)}</td>
                    <td className="py-1 text-right tabular-nums font-semibold">{mod.scenario_feature_value.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {result.warnings.map((warning) => (
              <p key={warning} className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                {warning}
              </p>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
