import { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { userApi } from '../../api/client';
import { Button, Input } from '../../components/common/UI';
import styles from './Auth.module.css';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (newPassword !== confirm) return setError('Passwords do not match');
    if (newPassword.length < 8) return setError('Password must be at least 8 characters');
    if (!token) return setError('Invalid or missing reset token');
    setLoading(true);
    try {
      await userApi.performReset(token, newPassword);
      setDone(true);
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
        <div className={styles.brand}><span>🍔</span><h1>Delivr</h1></div>
        <h2 className={styles.heading}>Set new password</h2>
        {!token ? (
          <div className={styles.successBox}>
            <p style={{ color: 'var(--red)' }}>⚠️ Invalid or missing reset token. Please request a new reset link.</p>
            <Link to="/forgot-password" className={styles.link}>Request new link</Link>
          </div>
        ) : done ? (
          <div className={styles.successBox}>
            <p>✅ Password reset successfully!</p>
            <Link to="/login" className={styles.link}>Back to sign in</Link>
          </div>
        ) : (
          <form className={styles.form} onSubmit={handleSubmit}>
            <p className={styles.sub}>Enter your new password below.</p>
            <Input
              label="New Password"
              type="password"
              placeholder="At least 8 characters"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              required
              minLength={8}
            />
            <Input
              label="Confirm Password"
              type="password"
              placeholder="Re-enter your password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              required
            />
            {error && <p className={styles.error}>{error}</p>}
            <Button type="submit" fullWidth loading={loading} size="lg">Reset Password</Button>
            <div className={styles.links}><Link to="/login" className={styles.link}>Back to sign in</Link></div>
          </form>
        )}
      </div>
    </div>
  );
}