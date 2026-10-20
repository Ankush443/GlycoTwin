import type { PatientDetail } from "../api/types";
import { EmptyState } from "./states";

/**
 * Historical clinical/laboratory summary. Values are synthetic historical
 * observations, never live measurements; the last lab date is highlighted
 * because the model predicts from data available at that timestamp.
 */
export function ClinicalSummary({ detail }: { detail: PatientDetail }) {
  const observations = [...detail.clinical_observations].sort((a, b) => a.observed_at.localeCompare(b.observed_at));
  const latest = observations.at(-1);

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4" aria-labelledby="clinical-heading">
      <h2 id="clinical-heading" className="text-sm font-semibold uppercase tracking-wide text-slate-600">
        Historical clinical summary
      </h2>

      <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-xs text-slate-500">Age</dt>
          <dd className="font-medium">{detail.age_years} years</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Sex at birth</dt>
          <dd className="font-medium capitalize">{detail.sex_at_birth}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Diabetes history</dt>
          <dd className="font-medium">{detail.diabetes_history_years} years</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Last synthetic lab date</dt>
          <dd className="font-medium">{latest ? latest.observed_at : "—"}</dd>
        </div>
      </dl>

      {observations.length === 0 ? (
        <div className="mt-3">
          <EmptyState>No historical laboratory observations for this synthetic patient.</EmptyState>
        </div>
      ) : (
        <table className="mt-4 w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
              <th scope="col" className="py-1.5 font-semibold">
                Observed
              </th>
              <th scope="col" className="py-1.5 text-right font-semibold">
                HbA1c (%)
              </th>
              <th scope="col" className="py-1.5 text-right font-semibold">
                Fasting glucose (mg/dL)
              </th>
              <th scope="col" className="py-1.5 text-right font-semibold">
                BMI (kg/m²)
              </th>
            </tr>
          </thead>
          <tbody>
            {observations.map((row) => (
              <tr key={row.observed_at} className="border-b border-slate-100 last:border-0">
                <td className="py-1.5">
                  {row.observed_at}
                  {row === latest && <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs">latest</span>}
                </td>
                <td className="py-1.5 text-right tabular-nums">{row.hba1c_percent.toFixed(2)}</td>
                <td className="py-1.5 text-right tabular-nums">{row.fasting_glucose_mg_dl.toFixed(1)}</td>
                <td className="py-1.5 text-right tabular-nums">{row.bmi_kg_m2.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="mt-3 text-xs text-slate-400">Source: {observations[0]?.data_kind ?? "n/a"} — synthetic data.</p>
    </section>
  );
}
