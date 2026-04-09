export type DashboardCounts = {
  appointments_today_count: number;
  appointments_pending_confirmation_count: number;
  tasks_today_count: number;
  inactive_customers_count: number;
  scheduled_reminders_count: number;
  recent_no_shows_count: number;
  new_online_bookings_count: number;
};

export type DashboardAppointmentItem = {
  id: string;
  created_at: string;
  starts_at: string;
  ends_at: string;
  status: string;
  needs_confirmation: boolean;
  customer_id: string;
  customer_name: string;
  service_id: string | null;
  service_name: string | null;
  location_id: string;
  location_name: string;
};

export type InactiveCustomerItem = {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  last_completed_at: string | null;
};

export type DashboardSections = {
  appointments_today: DashboardAppointmentItem[];
  appointments_pending_confirmation: DashboardAppointmentItem[];
  tasks_today: unknown[];
  inactive_customers: InactiveCustomerItem[];
  scheduled_reminders: unknown[];
  recent_no_shows: DashboardAppointmentItem[];
  new_online_bookings: DashboardAppointmentItem[];
};

export type DashboardOverview = {
  timezone: string;
  today_start_utc: string;
  today_end_utc: string;
  counts: DashboardCounts;
  sections: DashboardSections;
  notes: string[];
};

