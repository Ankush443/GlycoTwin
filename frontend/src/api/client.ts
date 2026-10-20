/**
 * Minimal typed client for the local GlycoTwin API.
 *
 * In development the Vite server proxies `/api` to `http://127.0.0.1:8000`,
 * so all requests are same-origin. Every call throws `ApiError` with the
 * server-provided detail message so the UI never shows fabricated values.
 */

import type {
  AlertsResponse,
  HealthResponse,
  PatientDetail,
  PatientsResponse,
  PredictionResponse,
  ScenarioFields,
  SimulationResponse,
} from "./types";

/** Error raised for non-2xx responses and network failures. */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const API_BASE = "/api";

interface ErrorDetail {
  detail?: unknown;
}

/** Extract a human-readable message from a FastAPI error body. */
async function errorFrom(response: Response): Promise<ApiError> {
  let message = `Request failed with HTTP ${response.status}`;
  try {
    const body = (await response.json()) as ErrorDetail;
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (body.detail !== undefined) {
      // Pydantic validation errors are arrays of structured objects.
      message = `${message}: ${JSON.stringify(body.detail)}`;
    }
  } catch {
    // Non-JSON body; keep the status-based message.
  }
  return new ApiError(message, response.status);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...init?.headers },
      ...init,
    });
  } catch (networkError) {
    const reason = networkError instanceof Error ? networkError.message : String(networkError);
    throw new ApiError(`Cannot reach the GlycoTwin API. Is the backend running? (${reason})`, 0);
  }
  if (!response.ok) {
    throw await errorFrom(response);
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  patients: () => request<PatientsResponse>("/patients"),
  patientDetail: (patientId: string) =>
    request<PatientDetail>(`/patients/${encodeURIComponent(patientId)}`),
  predict: (patientId: string) =>
    request<PredictionResponse>("/predict", {
      method: "POST",
      body: JSON.stringify({ patient_id: patientId }),
    }),
  simulate: (patientId: string, fields: ScenarioFields) =>
    request<SimulationResponse>("/simulate", {
      method: "POST",
      body: JSON.stringify({ patient_id: patientId, ...fields }),
    }),
  alerts: () => request<AlertsResponse>("/alerts"),
};
