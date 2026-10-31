import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '../core/auth/ProtectedRoute';
import { RoleGuard } from '../core/auth/RoleGuard';
import { useAuth } from '../core/auth/AuthProvider';
import { PortalLayout } from '../shared/layouts/PortalLayout';
import { RouteErrorBoundary } from '../shared/components/RouteErrorBoundary';
import { NotFoundPage } from '../shared/components/NotFoundPage';
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
import { AdminTimetableManagementView } from '../portals/admin/AdminTimetableManagementView';
import { AdminTransportManagementView } from '../portals/admin/AdminTransportManagementView';

// Technician Pages
import { TechnicianDashboard } from '../portals/technician/TechnicianDashboard';

// Faculty Pages
import { FacultyDashboard } from '../portals/faculty/FacultyDashboard';
import { FacultyTimetableView } from '../portals/faculty/FacultyTimetableView';
import { FacultyRequestsView } from '../portals/faculty/FacultyRequestsView';
import { FacultyExamSupportView } from '../portals/faculty/FacultyExamSupportView';
import { FacultyNoticesView } from '../portals/faculty/FacultyNoticesView';
import { FacultyTransportView } from '../portals/faculty/FacultyTransportView';

// Student Pages
import { StudentDashboard } from '../portals/student/StudentDashboard';
import { StudentNoticeBoardView } from '../portals/student/StudentNoticeBoardView';
import { StudentAdmissionsView } from '../portals/student/StudentAdmissionsView';
import { StudentTransportHostelView } from '../portals/student/StudentTransportHostelView';
import { StudentMyLearningView } from '../portals/student/StudentMyLearningView';
import { StudentTimetableView } from '../portals/student/StudentTimetableView';
import { StudentAttendanceView } from '../portals/student/StudentAttendanceView';

/** Everyone lands directly in the only portal their role can use. */
function HomeRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={`/${user.role}`} replace />;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
    errorElement: <RouteErrorBoundary />
  },
  {
    path: '/',
    element: <ProtectedRoute />,
    errorElement: <RouteErrorBoundary />,
    children: [
      {
        index: true,
        element: <HomeRedirect />
      },
      // Admin Portal Routes
      {
        path: 'admin',
        errorElement: <RouteErrorBoundary />,
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
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin', 'department_manager', 'facilities_admin']}>
                <PredictiveMaintenanceView />
              </RoleGuard>
            )
          },
          { path: 'incidents', element: <IncidentsView /> },
          {
            path: 'campus',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin', 'facilities_admin']}>
                <CampusView />
              </RoleGuard>
            )
          },
          {
            path: 'work-orders',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin', 'department_manager', 'facilities_admin']}>
                <WorkOrdersView />
              </RoleGuard>
            )
          },
          {
            path: 'inventory',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin', 'facilities_admin', 'procurement_approver']}>
                <InventoryView />
              </RoleGuard>
            )
          },
          {
            path: 'approvals',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin', 'department_manager', 'facilities_admin', 'procurement_approver']}>
                <ApprovalsView />
              </RoleGuard>
            )
          },
          {
            path: 'staff',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin', 'facilities_admin']}>
                <StaffView />
              </RoleGuard>
            )
          },
          {
            path: 'timetable',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin', 'department_manager', 'facilities_admin']}>
                <AdminTimetableManagementView />
              </RoleGuard>
            )
          },
          {
            path: 'transport',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin', 'facilities_admin']}>
                <AdminTransportManagementView />
              </RoleGuard>
            )
          },
          {
            path: 'simulations',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin']}>
                <ScenarioSimulatorView />
              </RoleGuard>
            )
          },
          {
            path: 'simulator',
            element: (
              <RoleGuard allowedRoles={['admin']} allowedSubRoles={['system_admin']}>
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
        errorElement: <RouteErrorBoundary />,
        element: (
          <RoleGuard allowedRoles={['technician']}>
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
        errorElement: <RouteErrorBoundary />,
        element: (
          <RoleGuard allowedRoles={['faculty']}>
            <PortalLayout portalName="Faculty Portal — Academic Workspace" />
          </RoleGuard>
        ),
        children: [
          { index: true, element: <FacultyDashboard /> },
          { path: 'timetable', element: <FacultyTimetableView /> },
          { path: 'requests', element: <FacultyRequestsView /> },
          { path: 'exam-support', element: <FacultyExamSupportView /> },
          { path: 'transport', element: <FacultyTransportView /> },
          { path: 'notices', element: <FacultyNoticesView /> }
        ]
      },
      // Student Portal Routes
      {
        path: 'student',
        errorElement: <RouteErrorBoundary />,
        element: (
          <RoleGuard allowedRoles={['student']}>
            <PortalLayout portalName="Students Portal — Student Service Workspace" />
          </RoleGuard>
        ),
        children: [
          { index: true, element: <StudentDashboard /> },
          { path: 'quick-report', element: <StudentDashboard /> },
          { path: 'timetable', element: <StudentTimetableView /> },
          { path: 'attendance', element: <StudentAttendanceView /> },
          { path: 'requests', element: <FacultyRequestsView /> },
          { path: 'facilities', element: <CampusView /> },
          { path: 'notice-board', element: <StudentNoticeBoardView /> },
          { path: 'notices', element: <FacultyNoticesView /> },
          { path: 'admissions', element: <StudentAdmissionsView /> },
          { path: 'transport-hostel', element: <StudentTransportHostelView /> },
          { path: 'transport', element: <StudentTransportHostelView /> },
          { path: 'my-learning', element: <StudentMyLearningView /> },
        ]
      }
    ]
  },
  {
    path: '*',
    element: <NotFoundPage />,
    errorElement: <RouteErrorBoundary />
  }
]);
