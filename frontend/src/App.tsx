import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api/client";
import type { PatientDetail, PatientSummary } from "./api/types";
import { AlertsPanel } from "./components/AlertsPanel";
import { ClinicalSummary } from "./components/ClinicalSummary";
import { HealthBadge } from "./components/HealthBadge";
import { PatientSelector } from "./components/PatientSelector";
import { PredictionPanel } from "./components/PredictionPanel";
import { PrototypeNotice } from "./components/PrototypeNotice";
import { ErrorState, LoadingState } from "./components/states";
import { SimulatorPanel } from "./components/SimulatorPanel";
import { WearableTrends } from "./components/WearableTrends";

export default function App() {
  const [patients, setPatients] = useState<PatientSummary[] | null>(null);
  const [patientsError, setPatientsError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [detail, setDetail] = useState<PatientDetail | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadPatients = useCallback(() => {
    setPatientsError(null);
    api
      .patients()
      .then((response) => {
        setPatients(response.patients);
        setSelectedId((current) => current ?? response.patients[0]?.patient_id ?? null);
      })
      .catch((caught: unknown) => {
        setPatients(null);
        setPatientsError(caught instanceof ApiError ? caught.message : String(caught));
      });
  }, []);

  useEffect(loadPatients, [loadPatients]);

  const loadDetail = useCallback(() => {
    if (!selectedId) return;
    // Clear the previous patient's data immediately so a failed load never
    // shows stale values for a different patient.
    setDetail(null);
    setDetailError(null);
    setDetailLoading(true);
    api
      .patientDetail(selectedId)
      .then(setDetail)
      .catch((caught: unknown) => setDetailError(caught instanceof ApiError ? caught.message : String(caught)))
      .finally(() => setDetailLoading(false));
  }, [selectedId]);

  useEffect(loadDetail, [loadDetail]);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 font-sans text-slate-900">
      <PrototypeNotice />
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3">
        <h1 className="text-lg font-bold tracking-tight">GlycoTwin — Virtual Biomarker Lab (Synthetic Demo)</h1>
        <HealthBadge />
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-72 shrink-0 border-r border-slate-200 bg-white">
          {patientsError ? (
            <div className="p-3">
              <ErrorState title="Could not load patients" message={patientsError} onRetry={loadPatients} />
            </div>
          ) : !patients ? (
            <div className="p-3">
              <LoadingState label="Loading synthetic patients…" />
            </div>
          ) : (
            <PatientSelector patients={patients} selectedId={selectedId} onSelect={setSelectedId} />
          )}
        </aside>

        <main className="flex-1 space-y-6 overflow-y-auto p-6">
          {!selectedId ? (
            <p className="text-sm text-slate-500">Select a synthetic patient to begin.</p>
          ) : detailLoading ? (
            <LoadingState label={`Loading ${selectedId}…`} />
          ) : detailError ? (
            <ErrorState title="Could not load this patient" message={detailError} onRetry={loadDetail} />
          ) : detail ? (
            <>
              {detail.warnings.map((warning) => (
                <p key={warning} className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                  {warning}
                </p>
              ))}
              <div className="flex items-baseline gap-3">
                <h2 className="text-xl font-bold">{detail.patient_id}</h2>
                <p className="text-xs text-slate-500">Synthetic prediction timestamp: {detail.prediction_at}</p>
              </div>
              <ClinicalSummary detail={detail} />
              <PredictionPanel key={detail.patient_id} patientId={detail.patient_id} />
              <SimulatorPanel key={`sim-${detail.patient_id}`} detail={detail} />
              <WearableTrends days={detail.wearable_daily} />
              <AlertsPanel onSelectPatient={setSelectedId} />
            </>
          ) : (
            <AlertsPanel onSelectPatient={setSelectedId} />
          )}
        </main>
      </div>
    </div>
  );
}
