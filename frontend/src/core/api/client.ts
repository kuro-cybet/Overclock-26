const API_BASE = '/api/v1';

export class ApiError extends Error {
  status: number;
  data: any;
  constructor(message: string, status: number, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('campusops_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    let data;
    try {
      data = await response.json();
      errorDetail = data.detail || JSON.stringify(data);
    } catch {
      // ignore
    }
    throw new ApiError(errorDetail, response.status, data);
  }

  return response.json();
}

export const api = {
  // Auth
  login: (credentials: { email: string; password: string }) =>
    apiRequest('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }),
  getMe: () => apiRequest('/auth/me'),
  getDemoAccounts: () => apiRequest('/users/demo-accounts'),

  // Dashboard & Analytics
  getDashboard: (portal: string) => apiRequest(`/dashboard/${portal}`),
  getAnalytics: () => apiRequest('/analytics'),

  // Incidents & Reports
  getIncidents: (params?: string) => apiRequest(`/incidents${params ? `?${params}` : ''}`),
  getIncidentDetails: (id: string) => apiRequest(`/incidents/${id}/details`),
  createIncident: (data: any) =>
    apiRequest('/incidents', { method: 'POST', body: JSON.stringify(data) }),
  correlateReports: (data: { report_ids: string[]; target_incident_id?: string; new_title?: string }) =>
    apiRequest('/incidents/correlate', { method: 'POST', body: JSON.stringify(data) }),

  getReports: (params?: string) => apiRequest(`/reports${params ? `?${params}` : ''}`),
  submitReport: (data: any) =>
    apiRequest('/reports', { method: 'POST', body: JSON.stringify(data) }),

  // Work Orders & Staff
  getWorkOrders: (params?: string) => apiRequest(`/work-orders${params ? `?${params}` : ''}`),
  getWorkOrderDetails: (id: string) => apiRequest(`/work-orders/${id}/details`),
  updateWorkOrder: (id: string, data: any) =>
    apiRequest(`/work-orders/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  reassignWorkOrder: (id: string, data: { new_technician_id: string; reassignment_reason: string }) =>
    apiRequest(`/work-orders/${id}/reassign`, { method: 'POST', body: JSON.stringify(data) }),

  getStaff: () => apiRequest('/staff'),
  updateStaffStatus: (userId: string, status: string) =>
    apiRequest(`/staff/${userId}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  getEligibleStaff: (skills?: string) =>
    apiRequest(`/staff/eligible${skills ? `?skills=${skills}` : ''}`),

  // Rooms & Bookings & Assets
  getRooms: (params?: string) => apiRequest(`/rooms${params ? `?${params}` : ''}`),
  getBuildings: () => apiRequest('/rooms/buildings'),
  updateRoomReadiness: (roomId: string, readiness: string) =>
    apiRequest(`/rooms/${roomId}/readiness`, { method: 'PATCH', body: JSON.stringify({ daily_readiness_status: readiness }) }),

  getBookings: (params?: string) => apiRequest(`/bookings${params ? `?${params}` : ''}`),
  createBooking: (data: any) =>
    apiRequest('/bookings', { method: 'POST', body: JSON.stringify(data) }),

  getAssets: (params?: string) => apiRequest(`/assets${params ? `?${params}` : ''}`),

  // Inventory & Approvals
  getInventory: (params?: string) => apiRequest(`/inventory${params ? `?${params}` : ''}`),
  reserveStock: (data: { work_order_id: string; item_id: string; quantity: number }) =>
    apiRequest('/inventory/reserve', { method: 'POST', body: JSON.stringify(data) }),

  getProcurement: () => apiRequest('/procurement'),
  createProcurement: (data: any) =>
    apiRequest('/procurement', { method: 'POST', body: JSON.stringify(data) }),

  getApprovals: (params?: string) => apiRequest(`/approvals${params ? `?${params}` : ''}`),
  decideApproval: (id: string, data: { decision: string; decision_reason: string }) =>
    apiRequest(`/approvals/${id}/decision`, { method: 'POST', body: JSON.stringify(data) }),

  // Recovery & Disruption Simulations
  getRecoveryPlan: (data: { disruption_type: string; entity_id: string }) =>
    apiRequest('/recovery/plan', { method: 'POST', body: JSON.stringify(data) }),
  executeRecovery: (data: any) =>
    apiRequest('/recovery/execute', { method: 'POST', body: JSON.stringify(data) }),

  triggerSimulation: (scenario: string) =>
    apiRequest(`/simulations/${scenario}`, { method: 'POST' }),
  resetSimulation: () =>
    apiRequest('/simulations/reset', { method: 'POST' }),

  // Notifications
  getNotifications: () => apiRequest('/notifications'),
  markNotificationRead: (id: string) =>
    apiRequest(`/notifications/${id}/read`, { method: 'PATCH' }),
  markAllNotificationsRead: () =>
    apiRequest('/notifications/read-all', { method: 'POST' }),

  // Integrations
  sendSimulatedEmail: (data: { sender_email: string; subject: string; body: string }) =>
    apiRequest('/integrations/email/inbox', { method: 'POST', body: JSON.stringify(data) }),
  getOutbox: () => apiRequest('/integrations/email/outbox'),

  // Intelligence & Upgrades
  getHistoricalCases: (category: string, symptoms: string) =>
    apiRequest(`/intelligence/historical-cases?category=${category}&symptoms=${encodeURIComponent(symptoms)}`),
  getPredictiveAlerts: () => apiRequest('/intelligence/predictive-alerts'),
  apiRequest
};

