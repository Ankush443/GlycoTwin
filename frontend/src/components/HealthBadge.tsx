import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { HealthResponse } from "../api/types";
import { LoadingState } from "./states";

/**
 * Polls `/health` and shows backend/model availability.
 * A failed poll is shown as an error instead of a stale "ok".
 */
export function HealthBadge() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    api
      .health()
      .then(setHealth)
      .catch((caught: unknown) => {
        setHealth(null);
        setError(caught instanceof ApiError ? caught.message : String(caught));
      });
  }, []);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, 30_000);
    return () => window.clearInterval(timer);
  }, [load]);

  if (error) {
    return (
      <div className="text-xs text-red-700" title={error}>
        API unreachable
      </div>
    );
  }
  if (!health) {
    return <LoadingState label="Checking API…" />;
  }

  const modelLabel = health.model_available
    ? `Model: ${health.model_version ?? "available"}`
    : "Model unavailable";
  return (
    <div className="flex items-center gap-3 text-xs text-slate-600">
      <span className="flex items-center gap-1.5">
        <span className="size-2 rounded-full bg-green-500" aria-hidden />
        API ok
      </span>
      <span className={health.model_available ? "text-slate-600" : "font-semibold text-amber-700"}>{modelLabel}</span>
      {health.deterioration_risk_available === false && (
        <span className="text-slate-400">No deterioration-risk classifier</span>
      )}
    </div>
  );
}
