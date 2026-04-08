import { useState, useEffect, useCallback, useRef } from 'react';
import { orderApi, receiptApi, restaurantApi } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Spinner, EmptyState, StatusBadge, Button, Modal, Toast } from '../../components/common/UI';
import { useToast } from '../../hooks/useToast';
import { Receipt, X } from 'lucide-react';
import styles from './OrderHistoryPage.module.css';

export default function OrderHistoryPage() {
  const { wsNotification } = useAuth();
  const { toast, show, hide } = useToast();
  const [orders, setOrders] = useState([]);
  const [restaurantMap, setRestaurantMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState(null);
  const [receiptLoading, setReceiptLoading] = useState(false);
  const [cancelling, setCancelling] = useState(null);
  const pollRef = useRef(null);

  const loadOrders = useCallback(async (showSpinner = false) => {
    if (showSpinner) setLoading(true);
    try {
      const [fetchedOrders, allRestaurants] = await Promise.all([
        orderApi.getForCustomer(),
        restaurantApi.getAll().catch(() => []),
      ]);
      setOrders(fetchedOrders);
      const map = {};
      allRestaurants.forEach(r => { map[r.id] = r.name; });
      setRestaurantMap(map);
    } catch (err) {
      show(err.message, 'error');
    } finally {
      if (showSpinner) setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrders(true);
    pollRef.current = setInterval(() => loadOrders(false), 15_000);
    return () => clearInterval(pollRef.current);
  }, [loadOrders]);
  useEffect(() => {
    if (!wsNotification) return;
    loadOrders(false);
  }, [wsNotification?.id]);

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

  const cancelOrder = async (orderId) => {
    setCancelling(orderId);
    try {
      await orderApi.cancel(orderId);
      setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: 'cancelled' } : o));
      show('Order cancelled.', 'success');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setCancelling(null);
    }
  };

  if (loading) return <div className="page"><Spinner center size={36} /></div>;

  const sorted = [...orders].sort((a, b) => b.id - a.id);

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}

      <Modal open={!!selectedReceipt} onClose={() => setSelectedReceipt(null)} title="Receipt Details">
        {selectedReceipt && (
          <div className={styles.receiptModal}>
            <div className={styles.receiptItems}>
              {selectedReceipt.items?.map(item => (
                <div key={item.menu_item_id} className={styles.receiptRow}>
                  <span>{item.qty}× {item.name}</span>
                  <span>${item.line_total.toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div className={styles.receiptTotals}>
              <div><span>Subtotal</span><span>${selectedReceipt.subtotal.toFixed(2)}</span></div>
              {selectedReceipt.discount > 0 && <div style={{ color: 'var(--green)' }}><span>Discount</span><span>-${selectedReceipt.discount.toFixed(2)}</span></div>}
              <div><span>Delivery fee</span><span>${selectedReceipt.delivery_fee.toFixed(2)}</span></div>
              <div><span>Tax</span><span>${selectedReceipt.tax.toFixed(2)}</span></div>
              <div className={styles.totalLine}><span>Total</span><span>${selectedReceipt.total.toFixed(2)}</span></div>
            </div>
            {selectedReceipt.promo_code && (
              <p className={styles.promoNote}>🎟️ Promo applied: <strong>{selectedReceipt.promo_code}</strong></p>
            )}
          </div>
        )}
      </Modal>

      <div className="container">
        <div className={styles.header}>
          <h1>My Orders</h1>
          <span className={styles.count}>{orders.length} total</span>
        </div>

        {sorted.length === 0 ? (
          <EmptyState icon="📦" title="No orders yet" subtitle="Place your first order from a restaurant!" />
        ) : (
          <div className={styles.list}>
            {sorted.map(order => (
              <div key={order.id} className={styles.orderCard}>
                <div className={styles.orderTop}>
                  <div>
                    <span className={styles.orderId}>Order #{order.id}</span>
                    {order.date_created && (
                      <span className={styles.orderDate}>{new Date(order.date_created).toLocaleDateString()}</span>
                    )}
                  </div>
                  <StatusBadge status={order.status} />
                </div>
                <div className={styles.orderMeta}>
                  <span>🏪 {restaurantMap[order.restaurant_id] || `Restaurant #${order.restaurant_id}`}</span>
                  <span>📍 {order.distance_km.toFixed(1)} km</span>
                  {order.delivery_id > 0 && <span>🚗 Delivery assigned</span>}
                </div>
                <div className={styles.orderActions}>
                  {order.receipt_id > 0 && (
                    <Button
                      variant="ghost" size="sm"
                      onClick={() => viewReceipt(order.receipt_id)}
                      loading={receiptLoading}
                    >
                      <Receipt size={14} /> View receipt
                    </Button>
                  )}
                  {order.status === 'pending' && (
                    <Button
                      variant="danger" size="sm"
                      loading={cancelling === order.id}
                      onClick={() => cancelOrder(order.id)}
                    >
                      <X size={14} /> Cancel
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}