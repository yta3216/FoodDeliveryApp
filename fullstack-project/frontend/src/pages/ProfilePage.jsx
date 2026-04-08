import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { userApi, paymentApi } from '../api/client';
import { Button, Input, Select, Toast } from '../components/common/UI';
import { useToast } from '../hooks/useToast';
import { User, Lock, Wallet } from 'lucide-react';
import styles from './ProfilePage.module.css';

export default function ProfilePage() {
  const { user, login } = useAuth();
  const { toast, show, hide } = useToast();
  const [tab, setTab] = useState('profile');
  const [profileForm, setProfileForm] = useState({ name: user?.name || '', email: user?.email || '', age: user?.age || '', gender: user?.gender || 'male' });
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '', confirm: '' });
  const [walletForm, setWalletForm] = useState({
    amount: '',
    card_number: '',
    expiry_month: '',
    expiry_year: '',
    cvv: '',
    cardholder_name: '',
  });
  const [saving, setSaving] = useState(false);

  const setP = k => e => setProfileForm(f => ({ ...f, [k]: e.target.value }));
  const setPw = k => e => setPasswordForm(f => ({ ...f, [k]: e.target.value }));
  const setW = k => e => setWalletForm(f => ({ ...f, [k]: e.target.value }));

  const saveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await userApi.update(user.user_id, { ...profileForm, age: Number(profileForm.age) });
      show('Profile updated!', 'success');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  const changePassword = async (e) => {
    e.preventDefault();
    if (passwordForm.new_password !== passwordForm.confirm) {
      return show('Passwords do not match', 'error');
    }
    setSaving(true);
    try {
      await userApi.updatePassword(user.user_id, {
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      });
      show('Password changed!', 'success');
      setPasswordForm({ old_password: '', new_password: '', confirm: '' });
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setSaving(false);
    }
  };

 const topupWallet = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await paymentApi.topup({
        amount: Number(walletForm.amount),
        card_number: walletForm.card_number,
        expiry_month: Number(walletForm.expiry_month),
        expiry_year: Number(walletForm.expiry_year),
        cvv: walletForm.cvv,
        cardholder_name: walletForm.cardholder_name,
      });
      show(`$${walletForm.amount} added to your wallet!`, 'success');
      setWalletForm(f => ({ ...f, amount: '' }));
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: <User size={15} /> },
    { id: 'password', label: 'Password', icon: <Lock size={15} /> },
    ...(user?.role === 'customer' ? [{ id: 'wallet', label: 'Wallet', icon: <Wallet size={15} /> }] : []),
  ];

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}
      <div className="container">
        <div className={styles.layout}>
          {/* Sidebar */}
          <div className={styles.sidebar}>
            <div className={styles.avatarCard}>
              <div className={styles.avatar}>{user?.name?.[0]?.toUpperCase() || '?'}</div>
              <h3>{user?.name}</h3>
              <span className={`badge badge-accent`}>{user?.role}</span>
            </div>
            <nav className={styles.nav}>
              {tabs.map(t => (
                <button
                  key={t.id}
                  className={[styles.navItem, tab === t.id && styles.navActive].filter(Boolean).join(' ')}
                  onClick={() => setTab(t.id)}
                >
                  {t.icon} {t.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className={styles.content}>
            {tab === 'profile' && (
              <div className={styles.section}>
                <h2>Profile Information</h2>
                <form onSubmit={saveProfile} className={styles.form}>
                  <Input label="Full Name" value={profileForm.name} onChange={setP('name')} required />
                  <Input label="Email" type="email" value={profileForm.email} onChange={setP('email')} required />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <Input label="Age" type="number" min="0" max="100" value={profileForm.age} onChange={setP('age')} required />
                    <Select label="Gender" value={profileForm.gender} onChange={setP('gender')}>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                      <option value="prefer not to say">Prefer not to say</option>
                    </Select>
                  </div>
                  <Button type="submit" loading={saving}>Save Changes</Button>
                </form>
              </div>
            )}

            {tab === 'password' && (
              <div className={styles.section}>
                <h2>Change Password</h2>
                <form onSubmit={changePassword} className={styles.form}>
                  <Input label="Current Password" type="password" value={passwordForm.old_password} onChange={setPw('old_password')} required />
                  <Input label="New Password" type="password" value={passwordForm.new_password} onChange={setPw('new_password')} required minLength={8} />
                  <Input label="Confirm New Password" type="password" value={passwordForm.confirm} onChange={setPw('confirm')} required />
                  <Button type="submit" loading={saving}>Update Password</Button>
                </form>
              </div>
            )}

            {tab === 'wallet' && (
              <div className={styles.section}>
                <h2>Wallet</h2>
                <div className={styles.walletBalance}>
                  <span className={styles.balanceLabel}>Current Balance</span>
                  <span className={styles.balanceAmount}>${(user?.wallet_balance || 0).toFixed(2)}</span>
                </div>
                <h3 className={styles.subhead}>Top Up</h3>
                <form onSubmit={topupWallet} className={styles.form}>
                  <Input label="Cardholder Name" value={walletForm.cardholder_name} onChange={setW('cardholder_name')} required placeholder="John Smith" />
                  <Input label="Card Number" value={walletForm.card_number} onChange={setW('card_number')} maxLength={16} required placeholder="1234 5678 9012 3456" />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                    <Input label="Expiry Month" type="number" min="1" max="12" value={walletForm.expiry_month} onChange={setW('expiry_month')} required placeholder="06" />
                    <Input label="Expiry Year" type="number" min="2024" value={walletForm.expiry_year} onChange={setW('expiry_year')} required placeholder="2027" />
                    <Input label="CVV" value={walletForm.cvv} onChange={setW('cvv')} maxLength={4} required placeholder="123" />
                  </div>
                  <Input label="Amount ($)" type="number" min="0.01" step="0.01" value={walletForm.amount} onChange={setW('amount')} required placeholder="13.67"/>
                  <Button type="submit" loading={saving}><Wallet size={15} /> Top Up Wallet</Button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
