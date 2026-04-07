import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { userApi } from '../../api/client';
import { Button, Input, Select } from '../../components/common/UI';
import styles from './Auth.module.css';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '', name: '', age: '', gender: 'male', role: 'customer' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await userApi.register({ ...form, age: Number(form.age) });
      navigate('/login');
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
        <h2 className={styles.heading}>Create account</h2>
        <p className={styles.sub}>Join us today</p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <Input label="Full Name" placeholder="Jane Doe" value={form.name} onChange={set('name')} required />
          <Input label="Email" type="email" placeholder="you@example.com" value={form.email} onChange={set('email')} required />
          <Input label="Password" type="password" placeholder="Min. 8 characters" value={form.password} onChange={set('password')} required minLength={8} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Input label="Age" type="number" min={0} max={100} placeholder="25" value={form.age} onChange={set('age')} required />
            <Select label="Gender" value={form.gender} onChange={set('gender')}>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="prefer not to say">Prefer not to say</option>
            </Select>
          </div>
          <Select label="Account Type" value={form.role} onChange={set('role')}>
            <option value="customer">Customer</option>
            <option value="manager">Restaurant Manager</option>
            <option value="driver">Delivery Driver</option>
          </Select>
          {error && <p className={styles.error}>{error}</p>}
          <Button type="submit" fullWidth loading={loading} size="lg">Create account</Button>
        </form>

        <div className={styles.links}>
          <span>Already have an account?</span>
          <Link to="/login" className={styles.link}>Sign in</Link>
        </div>
      </div>
    </div>
  );
}
