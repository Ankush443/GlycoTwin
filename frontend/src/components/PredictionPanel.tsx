import { useCallback, useState } from "react";
import { api, ApiError } from "../api/client";
import type { PredictionResponse } from "../api/types";
import { ErrorState, LoadingState } from "./states";

interface ContributionRow {
  feature: string;
  observed_value: number;
  contribution: number;
}

function prettyFeature(name: string): string {
  return name
    .replace(/_14d_mean$/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

/**
 * Horizontal bar chart of exact linear model contributions. Positive pushes
 * the estimate up, negative pulls it down; bars are model arithmetic, not
 * clinical causation (stated in the panel).
 */
function ContributionChart({ prediction }: { prediction: PredictionResponse }) {
  const explanation = prediction.explanation;
  if (!explanation?.available) {
    return (
      <p className="text-xs text-slate-500">
        Feature contributions unavailable: {explanation?.reason ?? "no explanation returned by the model."}
      </p>
    );
  }
  const rows: ContributionRow[] = explanation.features;
  const maxAbs = Math.max(...rows.map((row) => Math.abs(row.contribution)), 1e-9);

  return (
    <div>
      <p className="text-xs text-slate-500">
        Method: <code className="rounded bg-slate-100 px-1">{explanation.method}</code> — how the synthetic linear
        model produced its number (not clinical causation).
      </p>
      <ul className="mt-2 space-y-1.5">
        {rows.map((row) => {
          const width = (Math.abs(row.contribution) / maxAbs) * 100;
          const positive = row.contribution >= 0;
          return (
            <li key={row.feature} className="grid grid-cols-[10rem_1fr_4.5rem] items-center gap-2 text-xs">
              <span className="truncate text-slate-600" title={`${row.feature} = ${row.observed_value}`}>
                {prettyFeature(row.feature)}
              </span>
              <span className="relative flex h-3 justify-center bg-slate-100" aria-hidden>
                <span
                  className={positive ? "absolute left-1/2 bg-emerald-500" : "absolute right-1/2 bg-rose-500"}
                  style={{ width: `${width / 2}%`, height: "100%" }}
                />
                <span className="absolute left-1/2 top-0 h-full w-px bg-slate-300" />
              </span>
              <span className={`text-right tabular-nums ${positive ? "text-emerald-700" : "text-rose-700"}`}>
                {row.contribution >= 0 ? "+" : ""}
                {row.contribution.toFixed(3)}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/**
 * Runs the saved synthetic pipeline for the selected patient and shows the
 * estimate, uncertainty/risk availability, warnings, and the exact linear
 * explanation. Previous results are cleared before each request so a failure
 * never displays a stale estimate.
 */
export function PredictionPanel({ patientId }: { patientId: string }) {
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(() => {
    setPrediction(null);
    setError(null);
    setLoading(true);
    api
      .predict(patientId)
      .then(setPrediction)
      .catch((caught: unknown) => setError(caught instanceof ApiError ? caught.message : String(caught)))
      .finally(() => setLoading(false));
  }, [patientId]);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4" aria-labelledby="prediction-heading">
      <div className="flex items-center justify-between">
        <h2 id="prediction-heading" className="text-sm font-semibold uppercase tracking-wide text-slate-600">
          Model estimate
        </h2>
        <button
          type="button"
          onClick={run}
          disabled={loading}
          className="rounded bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {loading ? "Running…" : "Run inference"}
        </button>
      </div>

      <p className="mt-2 text-xs text-slate-500">
        Runs the saved synthetic Ridge pipeline for <strong>{patientId}</strong>. Estimated values are not laboratory
        results.
      </p>

      <div className="mt-3">
        {loading ? (
          <LoadingState label="Running the saved pipeline…" />
        ) : error ? (
          <ErrorState title="Prediction failed" message={error} onRetry={run} />
        ) : prediction ? (
          <div className="space-y-3">
            <div className="flex flex-wrap items-baseline gap-4">
              <p className="text-3xl font-bold tabular-nums text-slate-900">
                {prediction.estimated_hba1c_percent.toFixed(2)}
                <span className="ml-1 text-base font-medium text-slate-500">% HbA1c</span>
              </p>
              <div className="text-xs text-slate-500">
                <p>
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 font-medium uppercase tracking-wide">
                    {prediction.output_kind.replace(/_/g, " ")}
                  </span>
                </p>
                <p className="mt-1">
                  {prediction.estimate_horizon_days}-day horizon from {prediction.prediction_at} · model{" "}
                  <code className="rounded bg-slate-100 px-1">{prediction.model_version}</code> (
                  {prediction.model_name})
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 text-xs">
              <span className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-slate-600">
                Uncertainty: not quantified by this model
              </span>
              <span className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-slate-600">
                Deterioration risk: no validated classifier — not shown
              </span>
            </div>

            {prediction.warnings.map((warning) => (
              <p key={warning} className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                {warning}
              </p>
            ))}

            <ContributionChart prediction={prediction} />
          </div>
        ) : (
          <p className="text-sm text-slate-400">No estimate yet — run inference to see the model output.</p>
        )}
      </div>
    </section>
  );
}
