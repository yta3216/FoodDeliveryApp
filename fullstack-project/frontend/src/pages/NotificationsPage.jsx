import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { userApi } from '../api/client';
import { Spinner, EmptyState, Button, Toast } from '../components/common/UI';
import { useToast } from '../hooks/useToast';
import { Bell, Check } from 'lucide-react';
import styles from './NotificationsPage.module.css';

export default function NotificationsPage() {
  const { user } = useAuth();
  const { toast, show, hide } = useToast();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState(null);

  useEffect(() => {
    if (!user?.user_id) return;
    userApi.getNotifications(user.user_id)
      .then(n => setNotifications([...n].sort((a, b) => b.id - a.id)))
      .catch(err => show(err.message, 'error'))
      .finally(() => setLoading(false));
  }, []);

  const markRead = async (notifId) => {
    setMarking(notifId);
    try {
      await userApi.readNotification(user.user_id, notifId);
      setNotifications(prev => prev.map(n => n.id === notifId ? { ...n, is_read: true } : n));
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setMarking(null);
    }
  };

  if (loading) return <div className="page"><Spinner center size={36} /></div>;

  const unread = notifications.filter(n => !n.is_read);
  const read = notifications.filter(n => n.is_read);

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}
      <div className="container">
        <div className={styles.header}>
          <h1>Notifications</h1>
          {unread.length > 0 && <span className={styles.unreadBadge}>{unread.length} unread</span>}
        </div>

        {notifications.length === 0 ? (
          <EmptyState icon={<Bell size={48} />} title="No notifications" subtitle="You're all caught up!" />
        ) : (
          <div className={styles.list}>
            {unread.length > 0 && (
              <div className={styles.group}>
                <h3 className={styles.groupLabel}>New</h3>
                {unread.map(n => <NotifCard key={n.id} notif={n} onRead={markRead} marking={marking} />)}
              </div>
            )}
            {read.length > 0 && (
              <div className={styles.group}>
                <h3 className={styles.groupLabel}>Earlier</h3>
                {read.map(n => <NotifCard key={n.id} notif={n} onRead={markRead} marking={marking} />)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function NotifCard({ notif, onRead, marking }) {
  return (
    <div className={[styles.card, !notif.is_read && styles.cardUnread].filter(Boolean).join(' ')}>
      <div className={styles.cardIcon}>
        {!notif.is_read ? '🔔' : '📩'}
      </div>
      <div className={styles.cardBody}>
        <p className={styles.cardMessage}>{notif.message}</p>
        {notif.date_sent && (
          <span className={styles.cardDate}>{new Date(notif.date_sent).toLocaleString()}</span>
        )}
      </div>
      {!notif.is_read && (
        <Button
          variant="ghost" size="sm"
          loading={marking === notif.id}
          onClick={() => onRead(notif.id)}
        >
          <Check size={14} /> Mark read
        </Button>
      )}
    </div>
  );
}
