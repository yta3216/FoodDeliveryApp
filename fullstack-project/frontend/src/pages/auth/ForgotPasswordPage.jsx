import { useState } from 'react';
import { Link } from 'react-router-dom';
import { userApi } from '../../api/client';
import { Button, Input } from '../../components/common/UI';
import styles from './Auth.module.css';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await userApi.requestReset(email);
      setSent(true);
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
        <h2 className={styles.heading}>Reset password</h2>
        {sent ? (
          <div className={styles.successBox}>
            <p>✅ If that email exists, a reset link has been sent. Check your terminal (dev mode).</p>
            <Link to="/login" className={styles.link}>Back to sign in</Link>
          </div>
        ) : (
          <form className={styles.form} onSubmit={handleSubmit}>
            <p className={styles.sub}>Enter your email and we'll send a reset link.</p>
            <Input label="Email" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required />
            {error && <p className={styles.error}>{error}</p>}
            <Button type="submit" fullWidth loading={loading} size="lg">Send reset link</Button>
            <div className={styles.links}><Link to="/login" className={styles.link}>Back to sign in</Link></div>
          </form>
        )}
      </div>
    </div>
  );
}
