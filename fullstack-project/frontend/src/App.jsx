import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { useWebSocket } from './hooks/useWebSocket';
import { useEffect } from 'react';
import ProtectedRoute from './components/layout/ProtectedRoute';
import Navbar from './components/layout/Navbar';

import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';
import CustomerHomePage from './pages/customer/CustomerHomePage';
import RestaurantPage from './pages/customer/RestaurantPage';
import CartPage from './pages/customer/CartPage';
import OrderHistoryPage from './pages/customer/OrderHistoryPage';
import ManagerDashboard from './pages/manager/ManagerDashboard';
import ManagerOrdersPage from './pages/manager/ManagerOrdersPage';
import DriverDashboard from './pages/driver/DriverDashboard';
import AdminDashboard from './pages/admin/AdminDashboard';
import ProfilePage from './pages/ProfilePage';
import NotificationsPage from './pages/NotificationsPage';
import { Toast } from './components/common/UI';

function Layout({ children }) {
  return <><Navbar />{children}</>;
}

function GlobalNotifications() {
  const { user, wsNotification, pushNotification, clearWsNotification } = useAuth();

  useWebSocket(user?.user_id, pushNotification);

  useEffect(() => {
    if (!wsNotification) return;
    const timer = setTimeout(clearWsNotification, 5000);
    return () => clearTimeout(timer);
  }, [wsNotification]);

  if (!wsNotification) return null;
  return (
    <div style={{ position: 'fixed', top: 72, right: 20, zIndex: 9999, minWidth: 280, maxWidth: 400 }}>
      <Toast message={`🔔 ${wsNotification.message}`} type="info" onClose={clearWsNotification} />
    </div>
  );
}

function RootRedirect() {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;

  const roleHome = { customer: '/home', manager: '/manager', driver: '/driver', admin: '/admin' };
  return <Navigate to={roleHome[user.role] || '/home'} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <GlobalNotifications />
        <Routes>
          <Route path="/login" element={<><Navbar /><LoginPage /></>} />
          <Route path="/register" element={<><Navbar /><RegisterPage /></>} />
          <Route path="/forgot-password" element={<><Navbar /><ForgotPasswordPage /></>} />
          <Route path="/reset-password" element={<><Navbar /><ResetPasswordPage /></>} />

          <Route path="/home" element={<ProtectedRoute roles={['customer']}><Layout><CustomerHomePage /></Layout></ProtectedRoute>} />
          <Route path="/restaurant/:id" element={<ProtectedRoute roles={['customer']}><Layout><RestaurantPage /></Layout></ProtectedRoute>} />
          <Route path="/cart" element={<ProtectedRoute roles={['customer']}><Layout><CartPage /></Layout></ProtectedRoute>} />
          <Route path="/orders" element={<ProtectedRoute roles={['customer']}><Layout><OrderHistoryPage /></Layout></ProtectedRoute>} />

          <Route path="/manager" element={<ProtectedRoute roles={['manager']}><Layout><ManagerDashboard /></Layout></ProtectedRoute>} />
          <Route path="/manager/orders" element={<ProtectedRoute roles={['manager']}><Layout><ManagerOrdersPage /></Layout></ProtectedRoute>} />

          <Route path="/driver" element={<ProtectedRoute roles={['driver']}><Layout><DriverDashboard /></Layout></ProtectedRoute>} />

          <Route path="/admin" element={<ProtectedRoute roles={['admin']}><Layout><AdminDashboard /></Layout></ProtectedRoute>} />

          <Route path="/profile" element={<ProtectedRoute><Layout><ProfilePage /></Layout></ProtectedRoute>} />
          <Route path="/notifications" element={<ProtectedRoute><Layout><NotificationsPage /></Layout></ProtectedRoute>} />

          <Route path="/" element={<RootRedirect />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}