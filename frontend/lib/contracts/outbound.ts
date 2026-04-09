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

export type OutboundMessageStatus = "pending" | "sent" | "failed";

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

