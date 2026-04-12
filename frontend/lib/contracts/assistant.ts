export type AssistantSourceV1 = "dashboard" | "chatbot1" | "api" | "system";
export type AssistantActorTypeV1 = "staff" | "system" | "customer" | "service";

export type AssistantActorV1 = {
  type: AssistantActorTypeV1;
  id: string | null; // UUID
};

export type AssistantActionEnvelopeV1 = {
  trace_id: string;
  tenant_id: string; // UUID
  conversation_id: string | null; // UUID
  session_id: string | null; // may be non-UUID
  customer_id: string | null; // UUID
  source: AssistantSourceV1;
  actor: AssistantActorV1;
  idempotency_key: string | null;
  meta: Record<string, unknown>;
};

export type AssistantTimeWindowV1 = {
  starts_at: string | null; // RFC3339 datetime
  ends_at: string | null; // RFC3339 datetime
  requested_date: string | null; // YYYY-MM-DD
  requested_time: string | null; // HH:MM
  timezone: string | null; // IANA TZ
};

// Handoff v1
export type HandoffPriorityV1 = "low" | "normal" | "high" | "urgent";
export type HandoffStatusV1 = "open" | "accepted" | "closed" | "expired";

export type AssistantHandoffRequestInV1 = AssistantActionEnvelopeV1 & {
  reason: string;
  priority: HandoffPriorityV1;
  queue_key: string;
  summary: string;
  context: Record<string, unknown>;
  requested_sla_minutes: number | null;
};

export type AssistantHandoffAcceptedByV1 = {
  actor_type: "staff" | "system";
  actor_id: string | null; // UUID
  name: string | null;
};

export type AssistantHandoffResponseOutV1 = {
  ok: true;
  trace_id: string;
  handoff_id: string; // UUID
  status: HandoffStatusV1;
  queue_key: string;
  accepted_by: AssistantHandoffAcceptedByV1 | null;
  opened_at: string;
  updated_at: string;
};

// Quote v1
export type QuoteStatusV1 = "open" | "in_review" | "proposed" | "accepted" | "rejected" | "expired";

export type AssistantQuoteConstraintsV1 = {
  budget_max_cents: number | null;
  professional_preference: string | null;
  extra: Record<string, unknown>;
};

export type AssistantQuoteRequestInV1 = AssistantActionEnvelopeV1 & {
  service_ids: string[]; // UUID[]
  location_id: string | null; // UUID
  requested_window: AssistantTimeWindowV1 | null;
  constraints: AssistantQuoteConstraintsV1;
  notes: string | null;
};

export type AssistantQuoteResponseOutV1 = {
  ok: true;
  trace_id: string;
  quote_request_id: string; // UUID
  status: QuoteStatusV1;
  service_ids: string[]; // UUID[]
  location_id: string | null; // UUID
  summary: string | null;
  created_at: string;
  updated_at: string;
};

// Consult v1
export type ConsultTypeV1 = "in_person" | "phone" | "video" | "whatsapp" | "unspecified";
export type ConsultStatusV1 = "open" | "contacting" | "scheduled" | "completed" | "cancelled";

export type AssistantConsultServiceInterestV1 = {
  service_ids: string[]; // UUID[]
  free_text: string | null;
};

export type AssistantLocationPreferenceV1 = {
  location_id: string | null; // UUID
  free_text: string | null;
};

export type AssistantConsultRequestInV1 = AssistantActionEnvelopeV1 & {
  consult_type: ConsultTypeV1;
  service_interest: AssistantConsultServiceInterestV1;
  preferred_windows: AssistantTimeWindowV1[];
  location_preference: AssistantLocationPreferenceV1 | null;
  notes: string | null;
  context: Record<string, unknown>;
};

export type AssistantConsultResponseOutV1 = {
  ok: true;
  trace_id: string;
  consult_request_id: string; // UUID
  status: ConsultStatusV1;
  consult_type: ConsultTypeV1;
  created_at: string;
  updated_at: string;
};

