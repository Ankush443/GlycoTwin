/**
 * TypeScript mirrors of the GlycoTwin FastAPI response schemas.
 *
 * These types intentionally mirror `docs/api.md`. Every value served by this
 * API is synthetic; nothing here is a clinical measurement or diagnosis.
 */

export interface HealthResponse {
  status: string;
  synthetic_data_loaded: boolean;
  model_available: boolean;
  model_version: string | null;
  deterioration_risk_available: boolean;
}

export interface PatientSummary {
  patient_id: string;
  age_years: number;
  sex_at_birth: string;
  diabetes_history_years: number;
  /** ISO date of the synthetic prediction timestamp. */
  prediction_at: string;
}

export interface PatientsResponse {
  patients: PatientSummary[];
  synthetic_only: boolean;
}

export interface ClinicalObservation {
  observed_at: string;
  hba1c_percent: number;
  fasting_glucose_mg_dl: number;
  bmi_kg_m2: number;
  data_kind: string;
}

export interface WearableDay {
  recorded_on: string;
  steps: number;
  active_minutes: number;
  resting_heart_rate_bpm: number;
  sleep_duration_hours: number;
  sleep_consistency_percent: number;
  data_kind: string;
}

export interface PatientDetail {
  patient_id: string;
  age_years: number;
  sex_at_birth: string;
  diabetes_history_years: number;
  prediction_at: string;
  clinical_observations: ClinicalObservation[];
  wearable_daily: WearableDay[];
  warnings: string[];
}

export interface FeatureContribution {
  feature: string;
  observed_value: number;
  coefficient: number;
  contribution: number;
}

export interface Explanation {
  available: boolean;
  reason?: string;
  method?: string;
  intercept?: number;
  note?: string;
  features: FeatureContribution[];
}

export interface PredictionResponse {
  patient_id: string;
  prediction_at: string;
  estimate_horizon_days: number;
  output_kind: string;
  estimated_hba1c_percent: number;
  model_version: string;
  model_name: string;
  feature_columns: string[];
  explanation: Explanation;
  uncertainty: number | null;
  deterioration_risk_available: boolean;
  warnings: string[];
}

export interface ScenarioFields {
  steps_14d_mean?: number | null;
  active_minutes_14d_mean?: number | null;
  resting_heart_rate_14d_mean?: number | null;
  sleep_duration_14d_mean?: number | null;
  sleep_consistency_14d_mean?: number | null;
}

export interface ScenarioModification {
  observed_synthetic_feature_value: number;
  scenario_feature_value: number;
}

export interface SimulationResponse {
  patient_id: string;
  output_kind: string;
  baseline_estimated_hba1c_percent: number;
  scenario_estimated_hba1c_percent: number;
  scenario_minus_baseline: number;
  modifications: Record<string, ScenarioModification>;
  model_version: string;
  deterioration_risk_available: boolean;
  warnings: string[];
}

export interface AlertRule {
  name: string;
  threshold_percent: number;
  status: string;
}

export interface AlertRecord {
  patient_id: string;
  observed_at: string;
  observed_synthetic_hba1c_percent: number;
  message: string;
}

export interface AlertsResponse {
  rule: AlertRule;
  alerts: AlertRecord[];
  warnings: string[];
}
