import { createBrowserRouter } from "react-router-dom";
import AuthGuard from "../components/guards/AuthGuard";

// LAYOUTS
import PublicLayout from "../components/layout/PublicLayout";
import LawyerLayout from "../components/layout/LawyerLayout";

// PUBLIC PAGES
import HomePage from "../features/public/pages/HomePage";
import BookingPage from "../features/appointments/pages/BookingPage";
import ContactPage from "../features/public/pages/ContactPage";

// AUTH PAGES
import LoginPage from "../features/auth/pages/LoginPage";
import SignupPartnerPage from "../features/auth/pages/SignupPartnerPage";
import ActivateAccountPage from "../features/auth/pages/ActivateAccountPage";
import ForgotPasswordPage from "../features/auth/pages/ForgotPasswordPage";
import ResetPasswordPage from "../features/auth/pages/ResetPasswordPage";

// LAWYER PAGES
import DashboardPage from "../features/dashboard/pages/DashboardPage";
import ClientsListPage from "../features/clients/pages/ClientsListPage";
import ClientDetailPage from "../features/clients/pages/ClientDetailPage";
import MattersListPage from "../features/matters/pages/MattersListPage";
import MatterDetailPage from "../features/matters/pages/MatterDetailPage";
import CalendarPage from "../features/calendar/pages/CalendarPage";
import TasksPage from "../features/tasks/pages/TasksPage";
import PartnerApplicationsPage from "../features/partners/PartnerApplicationsPage";
import BillingPage from "../features/billing/pages/BillingPage";
// import NotificationsPage from "../features/notifications/pages/NotificationsPage";
import ProfilePage from "../features/profiles/ProfilePage";

// ROUTER
export const router = createBrowserRouter([
  {
    element: <PublicLayout />,

    children: [
      // Public
      {
        index: true,
        element: <HomePage />,
      },

      {
        path: "rendez-vous",
        element: <BookingPage />,
      },

      {
        path: "contact",
        element: <ContactPage />,
      },

      // Authentication
      {
        path: "auth/login",
        element: <LoginPage />,
      },

      {
        path: "auth/signup",
        element: <SignupPartnerPage />,
      },

      {
        path: "auth/activate-account",
        element: <ActivateAccountPage />,
      },

      {
        path: "auth/forgot-password",
        element: <ForgotPasswordPage />,
      },

      {
        path: "auth/reset-password",
        element: <ResetPasswordPage />,
      },
    ],
  },

  // ==========================================================
  // AVOCAT INTERNE (LAWYER)
  // ==========================================================
  {
    path: "/app",
    element: <AuthGuard><LawyerLayout /></AuthGuard>,
    // TODO: protéger avec un guard (rôle LAWYER) une fois l'auth branchée.
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "clients", element: <ClientsListPage /> },
      { path: "clients/:id", element: <ClientDetailPage /> },
      { path: "matters", element: <MattersListPage /> },
      { path: "matters/:id", element: <MatterDetailPage /> },
      { path: "calendar", element: <CalendarPage /> },
      { path: "tasks", element: <TasksPage /> },
      { path: "billing", element: <BillingPage /> },
      { path: "partner-applications", element: <PartnerApplicationsPage /> },
      // { path: "notifications", element: <NotificationsPage /> },
      { path: "profile", element: <ProfilePage /> },
    ],
  },

  // ==========================================================
  // AVOCAT EXTERNE / PARTENAIRE
  // ==========================================================

  // {
  //   path: "/portail",
  //   element: <PartnerLayout />,
  //   children: [...]
  // },
]);
