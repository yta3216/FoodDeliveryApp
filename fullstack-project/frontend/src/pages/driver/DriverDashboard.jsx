import { useState, useEffect } from 'react';
import { deliveryApi, userApi } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Button, EmptyState, StatusBadge, Toast, Input } from '../../components/common/UI';
import { useToast } from '../../hooks/useToast';
import { Truck, CheckCircle, Radio, Search, Save } from 'lucide-react';
import styles from './DriverPage.module.css';

export default function DriverDashboard() {
  const { user, updateUser } = useAuth();
  const { toast, show, hide } = useToast();
  const [driverStatus, setDriverStatus] = useState(user?.driver_status || 'available');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const [vehicle, setVehicle] = useState(user?.vehicle || '');
  const [editingVehicle, setEditingVehicle] = useState(false);
  const [savingVehicle, setSavingVehicle] = useState(false);

  const [activeDelivery, setActiveDelivery] = useState(null);
  const [lookupOrderId, setLookupOrderId] = useState('');
  const [lookupLoading, setLookupLoading] = useState(false);

  const toggleStatus = async () => {
    const newStatus = driverStatus === 'available' ? 'unavailable' : 'available';
    setUpdatingStatus(true);
    try {
      await deliveryApi.updateStatus(newStatus);
      setDriverStatus(newStatus);
      show(`Status set to ${newStatus}`, 'success');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const saveVehicle = async () => {
    if (!vehicle.trim()) return show('Vehicle cannot be empty', 'error');
    setSavingVehicle(true);
    try {
      // Requires backend: User_Update schema must include 'vehicle' field
      await userApi.update(user.user_id, {
        name: user.name,
        email: user.email,
        age: user.age,
        gender: user.gender,
        vehicle: vehicle.trim(),
      });
      updateUser({ vehicle: vehicle.trim() });
      setEditingVehicle(false);
      show('Vehicle updated!', 'success');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setSavingVehicle(false);
    }
  };

  const lookupDelivery = async () => {
    const orderId = parseInt(lookupOrderId, 10);
    if (!orderId) return show('Enter a valid Order ID', 'error');
    setLookupLoading(true);
    try {
      const delivery = await deliveryApi.getByOrder(orderId);
      if (delivery.driver_id && delivery.driver_id !== user?.user_id) {
        return show('This delivery is not assigned to you.', 'error');
      }
      setActiveDelivery(delivery);
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setLookupLoading(false);
    }
  };

  const startDelivery = async (orderId) => {
    try {
      const updated = await deliveryApi.startDelivery(orderId);
      setActiveDelivery(updated);
      show('Delivery started! 🚗', 'success');
    } catch (err) {
      show(err.message, 'error');
    }
  };

  const completeDelivery = async (orderId) => {
    try {
      const updated = await deliveryApi.completeDelivery(orderId);
      setActiveDelivery(updated);
      setDriverStatus('available');
      show('Delivery completed! 🎉', 'success');
    } catch (err) {
      show(err.message, 'error');
    }
  };

  const checkForOrders = async () => {
  setUpdatingStatus(true);
  try {
    await deliveryApi.updateStatus('unavailable');
    await deliveryApi.updateStatus('available');
    setDriverStatus('available');
    // try to load active delivery after the check
    try {
      const delivery = await deliveryApi.getMyActive();
      setActiveDelivery(delivery);
      show('Order assigned! 🎉', 'success');
    } catch {
      show('No waiting orders right now', 'default');
    }
  } catch (err) {
    show(err.message, 'error');
  } finally {
    setUpdatingStatus(false);
  }
};

  useEffect(() => {
  if (driverStatus === 'available' || driverStatus === 'delivering') {
    deliveryApi.getMyActive()
      .then(setActiveDelivery)
      .catch(() => {}); // silently ignore 404 if no active delivery
  }
}, []);

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}
      <div className="container">
        <div className={styles.header}>
          <div>
            <h1>Driver Dashboard</h1>
            <p className={styles.sub}>Welcome, {user?.name}</p>
          </div>
        </div>

        {/* Status Card */}
        <div className={styles.statusCard}>
          <div className={styles.statusLeft}>
            <div className={[styles.statusDot, driverStatus === 'available' && styles.dotActive].filter(Boolean).join(' ')} />
            <div>
              <h3>{driverStatus === 'available' ? 'Available for deliveries' : 'Currently unavailable'}</h3>
              <p>{driverStatus === 'available'
                ? 'You will be assigned new orders automatically.'
                : 'Toggle on to start receiving orders.'}</p>
            </div>
          </div>
          <Button
            variant={driverStatus === 'available' ? 'danger' : 'success'}
            loading={updatingStatus}
            onClick={toggleStatus}
          >
            <Radio size={16} />
            {driverStatus === 'available' ? 'Go Offline' : 'Go Online'}
          </Button>
        </div>

        {/* Info Cards */}
        <div className={styles.infoGrid}>
          <div className={styles.infoCard}>
            <Truck size={28} className={styles.infoIcon} />
            <h3>Your Vehicle</h3>
            {editingVehicle ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
                <Input
                  value={vehicle}
                  onChange={e => setVehicle(e.target.value)}
                  placeholder="e.g. bike, car, motorcycle"
                />
                <div style={{ display: 'flex', gap: 6 }}>
                  <Button size="sm" loading={savingVehicle} onClick={saveVehicle}>
                    <Save size={13} /> Save
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => { setEditingVehicle(false); setVehicle(user?.vehicle || ''); }}>
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-start' }}>
                <p>{user?.vehicle || 'Not specified'}</p>
                <Button size="sm" variant="ghost" onClick={() => setEditingVehicle(true)}>
                  Edit
                </Button>
              </div>
            )}
          </div>
          <div className={styles.infoCard}>
            <Radio size={28} className={styles.infoIcon} />
            <h3>Current Status</h3>
            <StatusBadge status={driverStatus} />
          </div>
          <div className={styles.infoCard}>
            <CheckCircle size={28} className={styles.infoIcon} />
            <h3>How it works</h3>
            <p className={styles.howTo}>Go online → get assigned → pick up → deliver</p>
          </div>
        </div>

        {/* Delivery Lookup */}
        <div className={styles.section} style={{ marginTop: 32 }}>
          <h2 className={styles.sectionTitle}>Manage a Delivery</h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>
            Check your notifications for an assigned Order ID, then look it up here.
          </p>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 180px' }}>
              <Input
                label="Order ID"
                type="number"
                placeholder="e.g. 42"
                value={lookupOrderId}
                onChange={e => setLookupOrderId(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && lookupDelivery()}
              />
            </div>
            <Button onClick={lookupDelivery} loading={lookupLoading} style={{ marginBottom: 1 }}>
              <Search size={15} /> Look Up
            </Button>
          </div>

          {/* Active Delivery Card */}
          {activeDelivery && (
            <div className={styles.deliveryCard} style={{ marginTop: 20 }}>
              <div className={styles.deliveryInfo}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <span style={{ fontWeight: 700 }}>Order #{activeDelivery.order_id}</span>
                  <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                    Distance: {activeDelivery.distance_km} km · Method: {activeDelivery.method}
                  </span>
                  {activeDelivery.eta_minutes > 0 && (
                    <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                      ETA: {activeDelivery.eta_minutes} min
                    </span>
                  )}
                  {activeDelivery.delivered_at > 0 && (
                    <span style={{ fontSize: 13, color: 'var(--green, #27ae60)' }}>
                      ✅ Delivered in {activeDelivery.actual_minutes} min
                    </span>
                  )}
                </div>
                <StatusBadge status={activeDelivery.delivered_at > 0 ? 'delivered' : (activeDelivery.started_at > 0 ? 'delivering' : 'assigned')} />
              </div>
              {!activeDelivery.delivered_at && (
                <div className={styles.deliveryActions} style={{ marginTop: 12 }}>
                  {!activeDelivery.started_at || activeDelivery.started_at === 0 ? (
                    <Button size="sm" onClick={() => startDelivery(activeDelivery.order_id)}>
                      <Truck size={14} /> Start Delivery
                    </Button>
                  ) : (
                    <Button variant="success" size="sm" onClick={() => completeDelivery(activeDelivery.order_id)}>
                      <CheckCircle size={14} /> Mark Delivered
                    </Button>
                  )}
                </div>
              )}
            </div>
          )}

          {!activeDelivery && (
            <div style={{ textAlign: 'center', padding: '32px 0' }}>
              <EmptyState
                icon={<Truck size={48} />}
                title="No delivery loaded"
                subtitle={driverStatus === 'available'
                  ? 'Once assigned an order, enter its ID above to manage it.'
                  : 'Go online to start receiving deliveries.'}
              />
              {driverStatus === 'available' && (
                <Button
                  onClick={checkForOrders}
                  loading={updatingStatus}
                  style={{ marginTop: 16 }}
                >
                  Check for Available Orders
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}