import { useCallback, useState } from "react";
import { api, ApiError } from "../api/client";
import type { AlertsResponse } from "../api/types";
import { EmptyState, ErrorState, LoadingState } from "./states";

/**
 * Follow-up alert panel. The rule is a configurable synthetic demo threshold
 * (latest historical HbA1c ≥ 8.0%), explicitly not clinically approved. The
 * only suggested action is to consider clinical/laboratory review; there is
 * no automated diagnosis or booking.
 */
export function AlertsPanel({
  onSelectPatient,
}: {
  onSelectPatient: (patientId: string) => void;
}) {
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(() => {
    setError(null);
    setLoading(true);
    setAlerts(null);
    api
      .alerts()
      .then(setAlerts)
      .catch((caught: unknown) => setError(caught instanceof ApiError ? caught.message : String(caught)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4" aria-labelledby="alerts-heading">
      <div className="flex items-center justify-between">
        <h2 id="alerts-heading" className="text-sm font-semibold uppercase tracking-wide text-slate-600">
          Follow-up review alerts
        </h2>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="rounded border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
        >
          {loading ? "Loading…" : alerts ? "Refresh" : "Check alerts"}
        </button>
      </div>

      {alerts && (
        <p className="mt-2 text-xs text-slate-500">
          Rule <code className="rounded bg-slate-100 px-1">{alerts.rule.name}</code>: latest synthetic historical
          HbA1c ≥ {alerts.rule.threshold_percent}% ·{" "}
          <span className="font-semibold uppercase text-amber-700">{alerts.rule.status.replace(/_/g, " ")}</span>
        </p>
      )}

      <div className="mt-3">
        {loading ? (
          <LoadingState label="Evaluating the demo rule…" />
        ) : error ? (
          <ErrorState title="Could not load alerts" message={error} onRetry={load} />
        ) : alerts ? (
          alerts.alerts.length === 0 ? (
            <EmptyState>No synthetic patient currently meets the demo follow-up rule.</EmptyState>
          ) : (
            <ul className="space-y-2">
              {alerts.alerts.map((alert) => (
                <li
                  key={alert.patient_id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm"
                >
                  <span>
                    <strong>{alert.patient_id}</strong> — observed synthetic HbA1c{" "}
                    <span className="font-semibold tabular-nums">{alert.observed_synthetic_hba1c_percent}%</span>{" "}
                    on {alert.observed_at}
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="text-xs text-amber-800">{alert.message}</span>
                    <button
                      type="button"
                      onClick={() => onSelectPatient(alert.patient_id)}
                      className="rounded bg-amber-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-amber-700"
                    >
                      Review patient
                    </button>
                  </span>
                </li>
              ))}
            </ul>
          )
        ) : (
          <p className="text-sm text-slate-400">Rule not evaluated yet — check alerts to see which records qualify.</p>
        )}
      </div>

      {alerts?.warnings.map((warning) => (
        <p key={warning} className="mt-3 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          {warning}
        </p>
      ))}
    </section>
  );
}
