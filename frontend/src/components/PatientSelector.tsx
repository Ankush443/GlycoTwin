import { useMemo, useState } from "react";
import type { PatientSummary } from "../api/types";
import { EmptyState } from "./states";

/**
 * Searchable synthetic patient selector. The list is labelled synthetic-only
 * because every record comes from the project's generated cohort.
 */
export function PatientSelector({
  patients,
  selectedId,
  onSelect,
}: {
  patients: PatientSummary[];
  selectedId: string | null;
  onSelect: (patientId: string) => void;
}) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return patients;
    return patients.filter((patient) => patient.patient_id.toLowerCase().includes(needle));
  }, [patients, query]);

  return (
    <nav aria-label="Synthetic patients" className="flex h-full flex-col">
      <label className="block px-3 pt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Synthetic patients
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter by ID…"
          className="mt-2 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal normal-case text-slate-800 placeholder:text-slate-400 focus:border-slate-500 focus:outline-none"
        />
      </label>
      <ul className="mt-2 flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <li className="px-3 py-2">
            <EmptyState>No synthetic patient matches “{query}”.</EmptyState>
          </li>
        )}
        {filtered.map((patient) => {
          const selected = patient.patient_id === selectedId;
          return (
            <li key={patient.patient_id}>
              <button
                type="button"
                onClick={() => onSelect(patient.patient_id)}
                aria-current={selected ? "true" : undefined}
                className={`w-full border-l-4 px-3 py-2 text-left text-sm transition-colors ${
                  selected
                    ? "border-slate-700 bg-slate-100 font-semibold text-slate-900"
                    : "border-transparent text-slate-700 hover:bg-slate-50"
                }`}
              >
                {patient.patient_id}
                <span className="block text-xs font-normal text-slate-500">
                  {patient.age_years}y · {patient.sex_at_birth} · {patient.diabetes_history_years}y history
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      <p className="border-t border-slate-200 px-3 py-2 text-xs text-slate-400">{patients.length} synthetic records</p>
    </nav>
  );
}
