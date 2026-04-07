import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { userApi } from '../../api/client';
import { Button, Input } from '../../components/common/UI';
import styles from './Auth.module.css';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await userApi.login(form.email, form.password);
      login(data);
      const routes = { customer: '/home', manager: '/manager', driver: '/driver', admin: '/admin' };
      navigate(routes[data.role] || '/home');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.bg} />
      <div className={styles.card}>
        <div className={styles.brand}>
          <span>🍔</span>
          <h1>Delivr</h1>
        </div>
        <h2 className={styles.heading}>Welcome back</h2>
        <p className={styles.sub}>Sign in to your account</p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <Input label="Email" type="email" placeholder="you@example.com" value={form.email} onChange={set('email')} required />
          <Input label="Password" type="password" placeholder="••••••••" value={form.password} onChange={set('password')} required />
          {error && <p className={styles.error}>{error}</p>}
          <Button type="submit" fullWidth loading={loading} size="lg">Sign in</Button>
        </form>

        <div className={styles.links}>
          <Link to="/forgot-password" className={styles.link}>Forgot password?</Link>
          <span>·</span>
          <Link to="/register" className={styles.link}>Create account</Link>
        </div>
      </div>
    </div>
  );
}
