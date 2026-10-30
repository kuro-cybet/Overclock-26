import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '../core/auth/ProtectedRoute';
import { RoleGuard } from '../core/auth/RoleGuard';
import { PortalLayout } from '../shared/layouts/PortalLayout';
import { LoginPage } from './LoginPage';

// Admin Pages
import { AdminDashboard } from '../portals/admin/AdminDashboard';
import { IncidentsView } from '../portals/admin/IncidentsView';
import { CampusView } from '../portals/admin/CampusView';
import { WorkOrdersView } from '../portals/admin/WorkOrdersView';
import { InventoryView } from '../portals/admin/InventoryView';
import { ApprovalsView } from '../portals/admin/ApprovalsView';
import { StaffView } from '../portals/admin/StaffView';
import { ScenarioSimulatorView } from '../portals/admin/ScenarioSimulatorView';
import { AnalyticsView } from '../portals/admin/AnalyticsView';
import { OperationalIntelligenceView } from '../portals/admin/OperationalIntelligenceView';
import { PredictiveMaintenanceView } from '../portals/admin/PredictiveMaintenanceView';

// Technician Pages
import { TechnicianDashboard } from '../portals/technician/TechnicianDashboard';

// Faculty Pages
import { FacultyDashboard } from '../portals/faculty/FacultyDashboard';
import { FacultyTimetableView } from '../portals/faculty/FacultyTimetableView';
import { FacultyRequestsView } from '../portals/faculty/FacultyRequestsView';
import { FacultyExamSupportView } from '../portals/faculty/FacultyExamSupportView';
import { FacultyNoticesView } from '../portals/faculty/FacultyNoticesView';

// Student Pages
import { StudentDashboard } from '../portals/student/StudentDashboard';
import { StudentNoticeBoardView } from '../portals/student/StudentNoticeBoardView';
import { StudentAdmissionsView } from '../portals/student/StudentAdmissionsView';
import { StudentTransportHostelView } from '../portals/student/StudentTransportHostelView';
import { StudentMyLearningView } from '../portals/student/StudentMyLearningView';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />
  },
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      {
        index: true,
        element: <Navigate to="/admin" replace />
      },
      // Admin Portal Routes
      {
        path: 'admin',
        element: (
          <RoleGuard allowedRoles={['admin']}>
            <PortalLayout portalName="Admin Portal — Operations Control Centre" />
          </RoleGuard>
        ),
        children: [
          { index: true, element: <AdminDashboard /> },
          {
            path: 'intelligence',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin', 'department_manager', 'facilities_admin']}>
                <OperationalIntelligenceView />
              </RoleGuard>
            )
          },
          {
            path: 'predictive',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin', 'facilities_admin']}>
                <PredictiveMaintenanceView />
              </RoleGuard>
            )
          },
          {
            path: 'incidents',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['department_manager', 'facilities_admin']}>
                <IncidentsView />
              </RoleGuard>
            )
          },
          {
            path: 'campus',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['facilities_admin']}>
                <CampusView />
              </RoleGuard>
            )
          },
          {
            path: 'work-orders',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['facilities_admin']}>
                <WorkOrdersView />
              </RoleGuard>
            )
          },
          {
            path: 'inventory',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['procurement_approver']}>
                <InventoryView />
              </RoleGuard>
            )
          },
          {
            path: 'approvals',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['department_manager', 'procurement_approver']}>
                <ApprovalsView />
              </RoleGuard>
            )
          },
          {
            path: 'staff',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={[]}>
                <StaffView />
              </RoleGuard>
            )
          },
          {
            path: 'simulator',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={[]}>
                <ScenarioSimulatorView />
              </RoleGuard>
            )
          },
          {
            path: 'analytics',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['department_manager']}>
                <AnalyticsView />
              </RoleGuard>
            )
          }
        ]
      },
      // Technician Portal Routes
      {
        path: 'technician',
        element: (
          <RoleGuard allowedRoles={['technician', 'admin']}>
            <PortalLayout portalName="Technicians Portal — Operational Workspace" />
          </RoleGuard>
        ),
        children: [
          { index: true, element: <TechnicianDashboard /> },
          { path: 'tasks', element: <WorkOrdersView /> },
          { path: 'schedule', element: <FacultyTimetableView /> },
          { path: 'readiness', element: <CampusView /> },
          { path: 'parts', element: <InventoryView /> }
        ]
      },
      // Faculty Portal Routes
      {
        path: 'faculty',
        element: (
          <RoleGuard allowedRoles={['faculty', 'admin']}>
            <PortalLayout portalName="Faculty Portal — Academic Workspace" />
          </RoleGuard>
        ),
        children: [
          { index: true, element: <FacultyDashboard /> },
          { path: 'timetable', element: <FacultyTimetableView /> },
          { path: 'requests', element: <FacultyRequestsView /> },
          { path: 'exam-support', element: <FacultyExamSupportView /> },
          { path: 'notices', element: <FacultyNoticesView /> }
        ]
      },
      // Student Portal Routes
      {
        path: 'student',
        element: (
          <RoleGuard allowedRoles={['student', 'admin']}>
            <PortalLayout portalName="Students Portal — Student Service Workspace" />
          </RoleGuard>
        ),
        children: [
          { index: true, element: <StudentDashboard /> },
          { path: 'quick-report', element: <StudentDashboard /> },
          { path: 'requests', element: <FacultyRequestsView /> },
          { path: 'facilities', element: <CampusView /> },
          { path: 'notices', element: <FacultyNoticesView /> },
          { path: 'notice-board', element: <StudentNoticeBoardView /> },
          { path: 'admissions', element: <StudentAdmissionsView /> },
          { path: 'transport-hostel', element: <StudentTransportHostelView /> },
          { path: 'my-learning', element: <StudentMyLearningView /> },
        ]
      }
    ]
  },
  {
    path: '*',
    element: <Navigate to="/login" replace />
  }
]);
