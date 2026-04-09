export type BookingSettings = {
  tenant_id: string;
  booking_enabled: boolean;
  booking_slug: string | null;
  public_business_name: string | null;
  public_contact_phone: string | null;
  public_contact_email: string | null;
  min_booking_notice_minutes: number;
  max_booking_notice_days: number;
  auto_confirm_bookings: boolean;
  created_at: string;
  updated_at: string;
  public_url_path: string | null;
};

export type BookingSettingsUpdatePayload = Partial<
  Pick<
    BookingSettings,
    | "booking_enabled"
    | "booking_slug"
    | "public_business_name"
    | "public_contact_phone"
    | "public_contact_email"
    | "min_booking_notice_minutes"
    | "max_booking_notice_days"
    | "auto_confirm_bookings"
  >
>;

