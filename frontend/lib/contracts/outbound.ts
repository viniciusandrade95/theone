export type OutboundTemplateType =
  | "booking_confirmation"
  | "reminder_24h"
  | "reminder_3h"
  | "post_service_followup"
  | "review_request"
  | "reactivation"
  | "simple_campaign"
  | "tomorrow_open_slot"
  | "internal_followup_support";

export type OutboundChannel = "whatsapp";

export type MessageTemplate = {
  id: string;
  tenant_id: string;
  name: string;
  type: OutboundTemplateType;
  channel: OutboundChannel;
  body: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type OutboundMessageStatus = "pending" | "sent" | "delivered" | "failed";

export type OutboundDeliveryStatus =
  | "queued"
  | "accepted"
  | "sent"
  | "delivered"
  | "read"
  | "failed"
  | "unconfirmed"
  | null;

export type OutboundMessage = {
  id: string;
  tenant_id: string;
  customer_id: string;
  appointment_id: string | null;
  template_id: string | null;
  type: OutboundTemplateType;
  channel: OutboundChannel;
  rendered_body: string;
  status: OutboundMessageStatus;
  error_message: string | null;
  sent_by_user_id: string | null;
  sent_at: string | null;
  provider?: string | null;
  provider_message_id?: string | null;
  recipient?: string | null;
  delivery_status?: OutboundDeliveryStatus;
  delivery_status_updated_at?: string | null;
  error_code?: string | null;
  idempotency_key?: string | null;
  trigger_type?: string | null;
  trace_id?: string | null;
  conversation_id?: string | null;
  assistant_session_id?: string | null;
  scheduled_for?: string | null;
  delivered_at?: string | null;
  failed_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type PreviewRequest = {
  customer_id: string;
  appointment_id?: string | null;
  template_id?: string | null;
  type?: OutboundTemplateType | null;
  body?: string | null;
};

export type PreviewResponse = {
  rendered_body: string;
  variables_used: string[];
};

export type SendRequest = {
  customer_id: string;
  appointment_id?: string | null;
  template_id?: string | null;
  final_body?: string | null;
  type: OutboundTemplateType;
  channel: OutboundChannel;
};

export type SendResponse = {
  ok: boolean;
  outbound_message: OutboundMessage;
  whatsapp_url?: string | null;
  note?: string | null;
};
