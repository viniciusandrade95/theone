export type AnalyticsOverview = {
  from: string;
  to: string;
  location_id: string | null;
  total_appointments_created: number;
  completed_count: number;
  cancelled_count: number;
  no_show_count: number;
  completion_rate: number;
  cancellation_rate: number;
  no_show_rate: number;
  new_customers: number;
  returning_customers: number;
  repeat_rate: number;
  status_breakdown: {
    booked: number;
    completed: number;
    cancelled: number;
    no_show: number;
  };
};

export type AnalyticsServiceItem = {
  service_id: string | null;
  service_name: string;
  bookings: number;
  share: number;
};

export type AnalyticsServicesBreakdown = {
  from: string;
  to: string;
  location_id: string | null;
  total_bookings: number;
  top_services: AnalyticsServiceItem[];
  service_mix: AnalyticsServiceItem[];
};

export type AnalyticsHeatmapCell = {
  weekday: "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";
  hour: number;
  count: number;
};

export type AnalyticsHeatmap = {
  from: string;
  to: string;
  location_id: string | null;
  timezone: string;
  items: AnalyticsHeatmapCell[];
};

export type AnalyticsBookingsPoint = {
  date: string;
  count: number;
};

export type AnalyticsBookingsOverTime = {
  from: string;
  to: string;
  location_id: string | null;
  timezone: string;
  items: AnalyticsBookingsPoint[];
};

export type AnalyticsAtRiskCustomer = {
  customer_id: string;
  customer_name: string;
  customer_phone: string | null;
  customer_email: string | null;
  last_appointment_at: string;
  days_since_last_appointment: number;
};

export type AnalyticsAtRisk = {
  threshold_days: number;
  reference_at: string;
  location_id: string | null;
  items: AnalyticsAtRiskCustomer[];
};
