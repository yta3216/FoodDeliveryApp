import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ShoppingCart, Bell, User, LogOut, ChefHat, Truck, Shield, Menu, X } from 'lucide-react';
import { useState } from 'react';
import styles from './Navbar.module.css';

const roleHome = {
  customer: '/home',
  manager: '/manager',
  driver: '/driver',
  admin: '/admin',
};

const roleIcon = {
  customer: <User size={16} />,
  manager: <ChefHat size={16} />,
  driver: <Truck size={16} />,
  admin: <Shield size={16} />,
};

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const home = user ? (roleHome[user.role] || '/') : '/';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinks = user ? getNavLinks(user.role) : [];

  return (
    <nav className={styles.nav}>
      <div className={styles.inner}>
        <Link to={home} className={styles.logo}>
          <span className={styles.logoIcon}>🍔</span>
          <span>Delivr</span>
        </Link>

        <div className={styles.links}>
          {navLinks.map(l => (
            <Link
              key={l.to}
              to={l.to}
              className={[styles.link, location.pathname === l.to && styles.active].filter(Boolean).join(' ')}
            >
              {l.label}
            </Link>
          ))}
        </div>

        <div className={styles.actions}>
          {user ? (
            <>
              {user.role === 'customer' && (
                <Link to="/cart" className={styles.iconBtn} title="Cart">
                  <ShoppingCart size={20} />
                </Link>
              )}
              <Link to={`/notifications`} className={styles.iconBtn} title="Notifications">
                <Bell size={20} />
              </Link>
              <Link to="/profile" className={styles.userChip}>
                {roleIcon[user.role]}
                <span>{user.name?.split(' ')[0]}</span>
              </Link>
              <button className={styles.iconBtn} onClick={handleLogout} title="Logout">
                <LogOut size={18} />
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className={styles.loginLink}>Sign in</Link>
              <Link to="/register" className={styles.registerBtn}>Get started</Link>
            </>
          )}
          <button className={styles.mobileToggle} onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className={styles.mobileMenu}>
          {navLinks.map(l => (
            <Link key={l.to} to={l.to} className={styles.mobileLink} onClick={() => setMobileOpen(false)}>
              {l.label}
            </Link>
          ))}
          {user && (
            <button className={styles.mobileLink} onClick={handleLogout} style={{ textAlign: 'left', background: 'none', border: 'none', color: 'var(--red)', width: '100%' }}>
              Sign out
            </button>
          )}
        </div>
      )}
    </nav>
  );
}

function getNavLinks(role) {
  if (role === 'customer') return [
    { to: '/home', label: 'Restaurants' },
    { to: '/orders', label: 'My Orders' },
    { to: '/cart', label: 'Cart' },
  ];
  if (role === 'manager') return [
    { to: '/manager', label: 'Dashboard' },
    { to: '/manager/orders', label: 'Orders' },
  ];
  if (role === 'driver') return [
    { to: '/driver', label: 'Dashboard' },
  ];
  if (role === 'admin') return [
    { to: '/admin', label: 'Dashboard' },
    { to: '/admin/users', label: 'Users' },
    { to: '/admin/config', label: 'Config' },
  ];
  return [];
}
