export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'technician' | 'faculty' | 'student';
  sub_role?: string;
  department?: string;
  building_id?: string;
  floor_id?: string;
}

export interface Incident {
  id: string;
  incident_code: string;
  title: string;
  description: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  priority: 'P1' | 'P2' | 'P3' | 'P4';
  building_id: string;
  room_id?: string;
  asset_id?: string;
  status: 'open' | 'in_progress' | 'pending_parts' | 'pending_approval' | 'resolved' | 'closed';
  sla_due_at?: string;
  is_sla_breached: boolean;
  correlated_count: number;
  summary?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Report {
  id: string;
  report_code: string;
  title: string;
  description: string;
  category: string;
  urgency: string;
  building_id: string;
  room_id?: string;
  asset_id?: string;
  reporter_id: string;
  reporter_role: string;
  reporter_name?: string;
  building_name?: string;
  room_number?: string;
  room_name?: string;
  asset_tag?: string;
  asset_name?: string;
  source: string;
  status: string;
  incident_id?: string;
  ai_extracted_meta?: string;
  created_at: string;
}

export interface WorkOrder {
  id: string;
  work_order_code: string;
  incident_id: string;
  title: string;
  description: string;
  assigned_technician_id?: string;
  priority: string;
  status: 'assigned' | 'in_progress' | 'blocked' | 'pending_parts' | 'completed' | 'cancelled';
  required_skills?: string;
  sla_deadline?: string;
  blocked_reason?: string;
  diagnosis?: string;
  checklist?: string;
  evidence_notes?: string;
  completed_at?: string;
  created_at: string;
}

export interface Room {
  id: string;
  building_id: string;
  floor_id: string;
  room_number: string;
  name: string;
  type: string;
  capacity: number;
  features?: string;
  status: 'available' | 'occupied' | 'under_maintenance' | 'unavailable';
  daily_readiness_status: 'confirmed_today' | 'stale' | 'unconfirmed' | 'unavailable';
  readiness_checked_at?: string;
  readiness_checked_by?: string;
  freshness_state?: string;
  last_confirmed_at?: string;
  confirmed_by?: string;
  freshness_source?: string;
  created_at: string;
}

export interface RoomBooking {
  id: string;
  booking_code: string;
  room_id: string;
  user_id: string;
  user_role: string;
  title: string;
  purpose: string;
  start_time: string;
  end_time: string;
  status: string;
  equipment_required?: string;
  conflict_resolved_to_room_id?: string;
  created_at: string;
}

export interface InventoryItem {
  id: string;
  item_code: string;
  name: string;
  category: string;
  stock_quantity: number;
  reserved_quantity: number;
  unit_cost: number;
  minimum_threshold: number;
}

export interface ApprovalRequest {
  id: string;
  approval_type: string;
  target_entity_type: string;
  target_entity_id: string;
  requester_id: string;
  approver_id?: string;
  status: 'pending' | 'approved' | 'rejected';
  cost_amount: number;
  justification: string;
  decision_reason?: string;
  decided_at?: string;
  created_at: string;
}

export interface Notification {
  id: string;
  recipient_id: string;
  recipient_role: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'critical' | 'action_required';
  read: boolean;
  link_url?: string;
  created_at: string;
}

export interface KPICards {
  open_incidents: number;
  sla_compliance_rate: number;
  active_work_orders: number;
  room_utilisation_rate: number;
  parts_shortages: number;
  pending_approvals?: number;
}
