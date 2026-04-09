import { useState, useEffect, useCallback, useRef } from 'react';
import { restaurantApi, orderApi, receiptApi } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Spinner, EmptyState, StatusBadge, Button, Toast, Modal } from '../../components/common/UI';
import { useToast } from '../../hooks/useToast';
import { Check, X, ChefHat, Receipt } from 'lucide-react';
import styles from './ManagerOrders.module.css';

export default function ManagerOrdersPage() {
  const { user, wsNotification } = useAuth();
  const { toast, show, hide } = useToast();
  const [restaurants, setRestaurants] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);
  const [selectedReceipt, setSelectedReceipt] = useState(null);
  const [receiptLoading, setReceiptLoading] = useState(false);
  const pollRef = useRef(null);

  useEffect(() => {
    if (!wsNotification) return;
    loadOrders(false);
  }, [wsNotification?.id]);
  const loadOrders = useCallback(async (showSpinner = false) => {
    if (showSpinner) setLoading(true);
    try {
      const all = await restaurantApi.getAll();
      const mine = all.filter(r => r.manager_ids?.includes(user?.user_id));
      setRestaurants(mine);
      const allOrders = [];
      for (const r of mine) {
        try {
          const ords = await orderApi.getForRestaurant(r.id);
          allOrders.push(...ords.map(o => ({ ...o, restaurantName: r.name })));
        } catch { }
      }
      setOrders(allOrders.sort((a, b) => b.id - a.id));
    } catch (err) {
      show(err.message, 'error');
    } finally {
      if (showSpinner) setLoading(false);
    }
  }, [user?.user_id]);

  useEffect(() => {
    loadOrders(true);
    pollRef.current = setInterval(() => loadOrders(false), 30_000);
    return () => clearInterval(pollRef.current);
  }, [loadOrders]);

  const handleStatus = async (orderId, status) => {
    setProcessing(orderId);
    try {
      await orderApi.acceptReject(orderId, status);
      await loadOrders(false);
      show(`Order ${status}!`, 'success');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setProcessing(null);
    }
  };

  const handleMarkReady = async (orderId) => {
    setProcessing(orderId);
    try {
      await orderApi.markReady(orderId);
      await loadOrders(false);
      show('Order marked as ready for pickup! 🍽️', 'success');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setProcessing(null);
    }
  };

  const viewReceipt = async (receiptId) => {
    setReceiptLoading(true);
    try {
      const r = await receiptApi.getById(receiptId);
      setSelectedReceipt(r);
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setReceiptLoading(false);
    }
  };

  if (loading) return <div className="page"><Spinner center size={36} /></div>;

  const pending = orders.filter(o => o.status === 'pending');
  const preparing = orders.filter(o => o.status === 'preparing');
  const others = orders.filter(o => !['pending', 'preparing'].includes(o.status));

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}

      <Modal open={!!selectedReceipt} onClose={() => setSelectedReceipt(null)} title="Receipt Details">
        {selectedReceipt && (
          <div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
              {selectedReceipt.items?.map(item => (
                <div key={item.menu_item_id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                  <span>{item.qty}× {item.name}</span>
                  <span>${item.line_total.toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10, display: 'flex', flexDirection: 'column', gap: 4, fontSize: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Subtotal</span><span>${selectedReceipt.subtotal.toFixed(2)}</span></div>
              {selectedReceipt.discount > 0 && <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--green)' }}><span>Discount</span><span>-${selectedReceipt.discount.toFixed(2)}</span></div>}
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Delivery fee</span><span>${selectedReceipt.delivery_fee.toFixed(2)}</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Tax</span><span>${selectedReceipt.tax.toFixed(2)}</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, marginTop: 4 }}><span>Total</span><span>${selectedReceipt.total.toFixed(2)}</span></div>
            </div>
            {selectedReceipt.promo_code && (
              <p style={{ fontSize: 12, color: 'var(--green)', marginTop: 8 }}>🎟️ Promo: <strong>{selectedReceipt.promo_code}</strong></p>
            )}
          </div>
        )}
      </Modal>

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
                    <OrderRow key={order.id} order={order} processing={processing}
                      onAction={handleStatus} onViewReceipt={viewReceipt}
                      receiptLoading={receiptLoading} showPendingActions />
                  ))}
                </div>
              </section>
            )}

            {preparing.length > 0 && (
              <section className={styles.section}>
                <h2 className={styles.sectionTitle}>
                  <span className={styles.dot} style={{ background: 'var(--accent, #f5a623)' }} />
                  Preparing ({preparing.length})
                </h2>
                <div className={styles.list}>
                  {preparing.map(order => (
                    <OrderRow key={order.id} order={order} processing={processing}
                      onMarkReady={handleMarkReady} onViewReceipt={viewReceipt}
                      receiptLoading={receiptLoading} showReadyAction />
                  ))}
                </div>
              </section>
            )}

            {others.length > 0 && (
              <section className={styles.section}>
                <h2 className={styles.sectionTitle}>
                  <span className={styles.dot} style={{ background: 'var(--text3)' }} />
                  All Orders
                </h2>
                <div className={styles.list}>
                  {others.map(order => (
                    <OrderRow key={order.id} order={order} processing={processing}
                      onViewReceipt={viewReceipt} receiptLoading={receiptLoading} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function OrderRow({ order, processing, onAction, onMarkReady, onViewReceipt, receiptLoading, showPendingActions, showReadyAction }) {
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
        <div className={styles.actions}>
          {order.receipt_id > 0 && (
            <Button variant="ghost" size="sm" loading={receiptLoading} onClick={() => onViewReceipt(order.receipt_id)}>
              <Receipt size={14} /> Receipt
            </Button>
          )}
          {showPendingActions && (
            <>
              <Button variant="success" size="sm" loading={processing === order.id} onClick={() => onAction(order.id, 'accepted')}>
                <Check size={14} /> Accept
              </Button>
              <Button variant="danger" size="sm" loading={processing === order.id} onClick={() => onAction(order.id, 'rejected')}>
                <X size={14} /> Reject
              </Button>
            </>
          )}
          {showReadyAction && (
            <Button variant="success" size="sm" loading={processing === order.id} onClick={() => onMarkReady(order.id)}>
              <ChefHat size={14} /> Mark Ready
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
