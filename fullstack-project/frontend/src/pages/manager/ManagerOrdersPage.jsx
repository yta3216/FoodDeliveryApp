import { useState, useEffect } from 'react';
import { restaurantApi, orderApi } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Spinner, EmptyState, StatusBadge, Button, Toast } from '../../components/common/UI';
import { useToast } from '../../hooks/useToast';
import { Check, X } from 'lucide-react';
import styles from './ManagerOrders.module.css';

export default function ManagerOrdersPage() {
  const { user } = useAuth();
  const { toast, show, hide } = useToast();
  const [restaurants, setRestaurants] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const all = await restaurantApi.getAll();
        const mine = all.filter(r => r.manager_ids?.includes(user?.user_id));
        setRestaurants(mine);
        const allOrders = [];
        for (const r of mine) {
          try {
            const ords = await orderApi.getForRestaurant(r.id);
            allOrders.push(...ords.map(o => ({ ...o, restaurantName: r.name })));
          } catch {}
        }
        setOrders(allOrders.sort((a, b) => b.id - a.id));
      } catch (err) {
        show(err.message, 'error');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleStatus = async (orderId, status) => {
    setProcessing(orderId);
    try {
      await orderApi.acceptReject(orderId, status);
      setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: status === 'accepted' ? 'accepted' : 'rejected' } : o));
      show(`Order ${status}!`, 'success');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setProcessing(null);
    }
  };

  if (loading) return <div className="page"><Spinner center size={36} /></div>;

  const pending = orders.filter(o => o.status === 'pending');
  const others = orders.filter(o => o.status !== 'pending');

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}
      <div className="container">
        <h1 className={styles.title}>Order Management</h1>

        {orders.length === 0 ? (
          <EmptyState icon="📋" title="No orders yet" subtitle="Orders will appear here when customers place them." />
        ) : (
          <>
            {pending.length > 0 && (
              <section className={styles.section}>
                <h2 className={styles.sectionTitle}>
                  <span className={styles.dot} style={{ background: 'var(--yellow)' }} />
                  Pending ({pending.length})
                </h2>
                <div className={styles.list}>
                  {pending.map(order => (
                    <OrderRow key={order.id} order={order} processing={processing} onAction={handleStatus} showActions />
                  ))}
                </div>
              </section>
            )}
            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>
                <span className={styles.dot} style={{ background: 'var(--text3)' }} />
                All Orders
              </h2>
              <div className={styles.list}>
                {others.map(order => (
                  <OrderRow key={order.id} order={order} processing={processing} onAction={handleStatus} />
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}

function OrderRow({ order, processing, onAction, showActions }) {
  return (
    <div className={styles.row}>
      <div className={styles.rowMain}>
        <span className={styles.orderId}>#{order.id}</span>
        <span className={styles.restaurantName}>{order.restaurantName}</span>
        <span className={styles.meta}>📍 {order.distance_km.toFixed(1)} km</span>
        {order.date_created && <span className={styles.meta}>{new Date(order.date_created).toLocaleDateString()}</span>}
      </div>
      <div className={styles.rowRight}>
        <StatusBadge status={order.status} />
        {showActions && order.status === 'pending' && (
          <div className={styles.actions}>
            <Button
              variant="success" size="sm"
              loading={processing === order.id}
              onClick={() => onAction(order.id, 'accepted')}
            >
              <Check size={14} /> Accept
            </Button>
            <Button
              variant="danger" size="sm"
              loading={processing === order.id}
              onClick={() => onAction(order.id, 'rejected')}
            >
              <X size={14} /> Reject
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
