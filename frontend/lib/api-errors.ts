type ApiResponseData = {
  error?: string;
  details?: unknown;
  detail?: unknown;
  message?: string;
  conflicts?: unknown;
};

type ApiResponse = {
  status?: number;
  data?: ApiResponseData;
};

type ApiLikeError = {
  response?: ApiResponse;
  message?: string;
};

export type ParsedApiError = {
  status: number;
  code: string | null;
  message: string;
  details: Record<string, unknown> | null;
  conflicts: Array<{ id: string; starts_at: string; ends_at: string }>;
  fieldErrors: Record<string, string>;
  payload: unknown;
};

function asObject(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function extractConflicts(payload: unknown): Array<{ id: string; starts_at: string; ends_at: string }> {
  if (!Array.isArray(payload)) {
    return [];
  }
  return payload.flatMap((item) => {
    const obj = asObject(item);
    if (!obj) {
      return [];
    }
    if (typeof obj.id !== "string" || typeof obj.starts_at !== "string" || typeof obj.ends_at !== "string") {
      return [];
    }
    return [{ id: obj.id, starts_at: obj.starts_at, ends_at: obj.ends_at }];
  });
}

function extractFieldErrors(details: Record<string, unknown> | null): Record<string, string> {
  if (!details) {
    return {};
  }

  const explicit = asObject(details.fields);
  if (explicit) {
    const normalized: Record<string, string> = {};
    for (const [field, value] of Object.entries(explicit)) {
      if (typeof value === "string" && value.trim()) {
        normalized[field] = value;
      }
    }
    if (Object.keys(normalized).length > 0) {
      return normalized;
    }
  }

  if (typeof details.field === "string" && typeof details.message === "string" && details.message.trim()) {
    return { [details.field]: details.message };
  }

  return {};
}

function inferMessage(code: string | null, fallback: string): string {
  if (code === "APPOINTMENT_OVERLAP") {
    return "Time slot conflicts with another appointment.";
  }
  if (code === "NOT_FOUND") {
    return "Resource not found.";
  }
  if (code === "UNAUTHORIZED") {
    return "Your session expired. Please log in again.";
  }
  if (code === "FORBIDDEN") {
    return "You are not authorized to perform this action.";
  }
  if (code === "VALIDATION_ERROR") {
    return "Please review the highlighted fields and try again.";
  }
  return fallback;
}

export function parseApiError(error: unknown, fallback = "Request failed."): ParsedApiError {
  const maybe = error as ApiLikeError;
  const status = maybe?.response?.status ?? 0;
  const payload = maybe?.response?.data ?? null;
  const code = typeof payload?.error === "string" ? payload.error : null;
  const details = asObject(payload?.details);
  const detailObj = asObject(payload?.detail);
  const fieldErrors = extractFieldErrors(details ?? detailObj);
  const conflicts = extractConflicts(payload?.conflicts);

  const explicitMessage =
    (details && typeof details.message === "string" ? details.message : null) ||
    (detailObj && typeof detailObj.message === "string" ? detailObj.message : null) ||
    (typeof payload?.message === "string" ? payload.message : null) ||
    (typeof payload?.detail === "string" ? payload.detail : null);

  const message = explicitMessage || inferMessage(code, maybe?.message || fallback);

  return {
    status,
    code,
    message,
    details: details ?? detailObj,
    conflicts,
    fieldErrors,
    payload,
  };
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  return parseApiError(error, fallback).message;
}
