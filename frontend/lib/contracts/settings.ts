export type CalendarDefaultView = "week" | "day";

export type TenantSettings = {
  tenant_id: string;
  business_name: string | null;
  default_timezone: string;
  currency: string;
  calendar_default_view: CalendarDefaultView;
  default_location_id: string | null;
  primary_color: string | null;
  logo_url: string | null;
  created_at: string;
  updated_at: string;
};

export type TenantSettingsUpdatePayload = {
  business_name?: string | null;
  default_timezone?: string;
  currency?: string;
  calendar_default_view?: CalendarDefaultView;
  default_location_id?: string | null;
  primary_color?: string | null;
  logo_url?: string | null;
};

export type SettingsLocation = {
  id: string;
  tenant_id: string;
  name: string;
  timezone: string;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  postcode: string | null;
  country: string | null;
  phone: string | null;
  email: string | null;
  is_active: boolean;
  hours_json: Record<string, unknown> | null;
  allow_overlaps: boolean;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
};

export type SettingsLocationUpdatePayload = {
  name?: string;
  timezone?: string;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  postcode?: string | null;
  country?: string | null;
  phone?: string | null;
  email?: string | null;
  is_active?: boolean;
  hours_json?: Record<string, unknown> | null;
  allow_overlaps?: boolean;
};
