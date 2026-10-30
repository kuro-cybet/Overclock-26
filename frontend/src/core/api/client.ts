// API base resolution:
// 1. VITE_API_URL when provided (explicit deployment configuration).
// 2. The deployed backend for the Render-hosted static site (no local proxy there).
// 3. Relative path so the Vite dev proxy / same-origin server handles it.
const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();
const isRenderHost =
  typeof window !== 'undefined' && /\.onrender\.com$/i.test(window.location.hostname);

const API_BASE = (
  configuredApiUrl && configuredApiUrl.length > 0
    ? configuredApiUrl
    : isRenderHost
      ? 'https://campusops-u6yt.onrender.com/api/v1'
      : '/api/v1'
).replace(/\/+$/, '');

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
  impersonate: (role: string) =>
    apiRequest('/auth/impersonate', { method: 'POST', body: JSON.stringify({ role }) }),

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
  createWorkOrder: (data: any) =>
    apiRequest('/work-orders', { method: 'POST', body: JSON.stringify(data) }),
  getWorkOrderDetails: (id: string) => apiRequest(`/work-orders/${id}/details`),
  getWorkOrderChecklist: (woId: string) => apiRequest(`/work-orders/${woId}/checklist`),
  updateChecklistItem: (woId: string, itemId: string, data: { is_completed: boolean; verification_notes?: string }) =>
    apiRequest(`/work-orders/${woId}/checklist/${itemId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  requisitionParts: (woId: string, data: { item_id: string; quantity: number; justification?: string }) =>
    apiRequest(`/work-orders/${woId}/parts-requisition`, { method: 'POST', body: JSON.stringify(data) }),
  updateWorkOrder: (id: string, data: any) =>
    apiRequest(`/work-orders/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  reassignWorkOrder: (id: string, data: { new_technician_id: string; reassignment_reason: string }) =>
    apiRequest(`/work-orders/${id}/reassign`, { method: 'POST', body: JSON.stringify(data) }),
  requestWorkOrderReassignment: (id: string, data: { reason: string; urgency?: string; notes?: string }) =>
    apiRequest(`/work-orders/${id}/request-reassignment`, { method: 'POST', body: JSON.stringify(data) }),

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
  getExaminations: () => apiRequest('/bookings/examinations'),
  submitExamReadiness: (bookingId: string, data: { status: string; checklist: any; notes?: string; reported_faults?: string[] }) =>
    apiRequest(`/bookings/${bookingId}/exam-readiness`, { method: 'POST', body: JSON.stringify(data) }),
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
  initiateAutonomousRecovery: (data: any) =>
    apiRequest('/recovery/initiate', { method: 'POST', body: JSON.stringify(data) }),
  runRecoveryActions: (executionId: string) =>
    apiRequest(`/recovery/${executionId}/run-actions`, { method: 'POST' }),
  verifyRecoveryOutcome: (executionId: string) =>
    apiRequest(`/recovery/${executionId}/verify`, { method: 'POST' }),
  getRecoveryExecutions: () =>
    apiRequest('/recovery/executions'),

  triggerSimulation: (scenario: string) =>
    apiRequest(`/simulations/${scenario}`, { method: 'POST' }),
  resetSimulation: () =>
    apiRequest('/simulations/reset', { method: 'POST' }),

  // Notifications & Outbox
  getNotifications: () => apiRequest('/notifications'),
  markNotificationRead: (id: string) =>
    apiRequest(`/notifications/${id}/read`, { method: 'PATCH' }),
  markAllNotificationsRead: () =>
    apiRequest('/notifications/read-all', { method: 'POST' }),
  processOutboxQueue: () =>
    apiRequest('/notifications/outbox/process', { method: 'POST' }),

  // Integrations
  sendSimulatedEmail: (data: { sender_email: string; subject: string; body: string }) =>
    apiRequest('/integrations/email/inbox', { method: 'POST', body: JSON.stringify(data) }),
  getOutbox: () => apiRequest('/integrations/email/outbox'),

  // Intelligence & Predictive Engine
  getHistoricalCases: (category: string, symptoms: string) =>
    apiRequest(`/intelligence/historical-cases?category=${category}&symptoms=${encodeURIComponent(symptoms)}`),
  getPredictiveAlerts: () => apiRequest('/intelligence/predictive-alerts'),
  getOperationalAssessment: () => apiRequest('/intelligence/operational-assessment'),
  getBuildingClusters: () => apiRequest('/intelligence/building-clusters'),
  getRoomsAtRisk: () => apiRequest('/intelligence/rooms-at-risk'),
  getAffectedExaminations: () => apiRequest('/intelligence/affected-examinations'),
  getDecisionExplanations: (type?: string) =>
    apiRequest(`/intelligence/explanations${type ? `?decision_type=${type}` : ''}`),
  getPredictiveFleetOverview: () => apiRequest('/assets/predictive-overview'),
  getAssetPredictiveHealth: (assetId: string) => apiRequest(`/assets/${assetId}/predictive-health`),

  apiRequest
};
