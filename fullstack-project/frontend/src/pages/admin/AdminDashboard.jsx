import { useState, useEffect } from 'react';
import { restaurantApi, configApi, promoApi } from '../../api/client';
import { Button, Spinner, Input, Toast, EmptyState } from '../../components/common/UI';
import { useToast } from '../../hooks/useToast';
import { UtensilsCrossed, Settings, Trash2, Tag, Plus, ToggleLeft, ToggleRight } from 'lucide-react';
import styles from './AdminPage.module.css';

const PROMO_TYPES = ['fixed_amount', 'percentage', 'free_delivery'];

const EMPTY_PROMO = {
  code: '', description: '', type: 'fixed_amount', value: '',
  min_order_value: '', expiry_date: '', is_public: true, is_first_order_only: false,
};

export default function AdminDashboard() {
  const { toast, show, hide } = useToast();
  const [tab, setTab] = useState('restaurants');
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [taxRate, setTaxRate] = useState('');
  const [savingTax, setSavingTax] = useState(false);
  const [deleting, setDeleting] = useState(null);

  // Promo state
  const [promos, setPromos] = useState([]);
  const [promosLoading, setPromosLoading] = useState(false);
  const [promoForm, setPromoForm] = useState(EMPTY_PROMO);
  const [creatingPromo, setCreatingPromo] = useState(false);
  const [showPromoForm, setShowPromoForm] = useState(false);
  const [togglingPromo, setTogglingPromo] = useState(null);
  const setP = (k) => (e) => setPromoForm(f => ({ ...f, [k]: e.target.value }));

  useEffect(() => {
    restaurantApi.getAll()
      .then(setRestaurants)
      .catch(err => show(err.message, 'error'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (tab === 'promos' && promos.length === 0) loadPromos();
  }, [tab]);

  const loadPromos = async () => {
    setPromosLoading(true);
    try {
      const p = await promoApi.getAll();
      setPromos(p);
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setPromosLoading(false);
    }
  };

  const deleteRestaurant = async (id) => {
    if (!window.confirm('Delete this restaurant?')) return;
    setDeleting(id);
    try {
      await restaurantApi.delete(id);
      setRestaurants(prev => prev.filter(r => r.id !== id));
      show('Restaurant deleted.', 'success');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setDeleting(null);
    }
  };

  const updateTax = async (e) => {
    e.preventDefault();
    setSavingTax(true);
    try {
      await configApi.setTaxRate(Number(taxRate));
      show(`Tax rate updated to ${(Number(taxRate) * 100).toFixed(1)}%!`, 'success');
      setTaxRate('');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setSavingTax(false);
    }
  };

  const createPromo = async (e) => {
    e.preventDefault();
    setCreatingPromo(true);
    try {
      await promoApi.create({
        ...promoForm,
        value: Number(promoForm.value) || 0,
        min_order_value: Number(promoForm.min_order_value) || 0,
        expiry_date: promoForm.expiry_date || null,
      });
      show('Promo code created!', 'success');
      setPromoForm(EMPTY_PROMO);
      setShowPromoForm(false);
      await loadPromos();
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setCreatingPromo(false);
    }
  };

  const togglePromo = async (promo) => {
    setTogglingPromo(promo.id);
    try {
      const updated = await promoApi.updateStatus(promo.id, !promo.is_active);
      setPromos(prev => prev.map(p => p.id === promo.id ? updated : p));
      show(`Promo ${updated.is_active ? 'activated' : 'deactivated'}.`, 'success');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setTogglingPromo(null);
    }
  };

  const TABS = [
    { id: 'restaurants', label: 'Restaurants', icon: <UtensilsCrossed size={15} /> },
    { id: 'promos', label: 'Promo Codes', icon: <Tag size={15} /> },
    { id: 'config', label: 'Config', icon: <Settings size={15} /> },
  ];

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}

      <div className="container">
        <h1 className={styles.title}>Admin Dashboard</h1>

        {/* Tab Bar */}
        <div className={styles.tabs}>
          {TABS.map(t => (
            <button
              key={t.id}
              className={[styles.tab, tab === t.id && styles.tabActive].filter(Boolean).join(' ')}
              onClick={() => setTab(t.id)}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* Restaurants Tab */}
        {tab === 'restaurants' && (
          <div className={styles.section}>
            {loading ? <Spinner center size={32} /> : restaurants.length === 0 ? (
              <EmptyState icon={<UtensilsCrossed size={48} />} title="No restaurants" subtitle="None registered yet." />
            ) : (
              <div className={styles.list}>
                {restaurants.map(r => (
                  <div key={r.id} className={styles.listItem}>
                    <div>
                      <strong>{r.name}</strong>
                      <span className={styles.sub}> · {r.city} · {r.menu?.items?.length || 0} items · {r.manager_ids?.length || 0} managers</span>
                    </div>
                    <Button
                      variant="danger"
                      size="sm"
                      loading={deleting === r.id}
                      onClick={() => deleteRestaurant(r.id)}
                    >
                      <Trash2 size={14} /> Delete
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Promo Codes Tab */}
        {tab === 'promos' && (
          <div className={styles.section}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ margin: 0 }}>Promotional Codes</h2>
              <Button size="sm" onClick={() => setShowPromoForm(v => !v)}>
                <Plus size={14} /> {showPromoForm ? 'Cancel' : 'New Promo'}
              </Button>
            </div>

            {/* Create Promo Form */}
            {showPromoForm && (
              <form onSubmit={createPromo} style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 12, padding: 20, marginBottom: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
                <h3 style={{ margin: 0, fontSize: 15 }}>Create Promo Code</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <Input label="Code" value={promoForm.code} onChange={setP('code')} required placeholder="SUMMER20" />
                  <div>
                    <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 4 }}>Type</label>
                    <select
                      value={promoForm.type} onChange={setP('type')} required
                      style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 14, background: '#fff' }}
                    >
                      {PROMO_TYPES.map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                    </select>
                  </div>
                </div>
                <Input label="Description" value={promoForm.description} onChange={setP('description')} placeholder="20% off your order" />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                  <Input label="Value" type="number" min="0" step="0.01" value={promoForm.value} onChange={setP('value')} placeholder="20" />
                  <Input label="Min. Order ($)" type="number" min="0" step="0.01" value={promoForm.min_order_value} onChange={setP('min_order_value')} placeholder="0" />
                  <Input label="Expiry Date" type="date" value={promoForm.expiry_date} onChange={setP('expiry_date')} />
                </div>
                <div style={{ display: 'flex', gap: 16, fontSize: 14 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                    <input type="checkbox" checked={promoForm.is_public} onChange={e => setPromoForm(f => ({ ...f, is_public: e.target.checked }))} />
                    Public (visible to customers)
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                    <input type="checkbox" checked={promoForm.is_first_order_only} onChange={e => setPromoForm(f => ({ ...f, is_first_order_only: e.target.checked }))} />
                    First order only
                  </label>
                </div>
                <Button type="submit" loading={creatingPromo} style={{ alignSelf: 'flex-start' }}>
                  <Plus size={14} /> Create Promo
                </Button>
              </form>
            )}

            {/* Promos List */}
            {promosLoading ? <Spinner center size={32} /> : promos.length === 0 ? (
              <EmptyState icon={<Tag size={48} />} title="No promo codes" subtitle="Create your first promotional code above." />
            ) : (
              <div className={styles.list}>
                {promos.map(p => (
                  <div key={p.id} className={styles.listItem} style={{ flexWrap: 'wrap', gap: 8 }}>
                    <div style={{ flex: 1, minWidth: 200 }}>
                      <strong style={{ fontFamily: 'monospace', fontSize: 15 }}>{p.code}</strong>
                      <span style={{ marginLeft: 8, fontSize: 12, color: 'var(--text-muted)' }}>
                        {p.type.replace('_', ' ')} · {p.type === 'free_delivery' ? 'free delivery' : (p.type === 'percentage' ? `${p.value}%` : `$${p.value}`)}
                        {p.min_order_value > 0 && ` · min $${p.min_order_value}`}
                        {p.expiry_date && ` · expires ${p.expiry_date}`}
                        {p.is_first_order_only && ' · first order only'}
                        {!p.is_public && ' · private'}
                      </span>
                      {p.description && <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>{p.description}</p>}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 12, fontWeight: 600, color: p.is_active ? 'var(--green, #27ae60)' : 'var(--text-muted)' }}>
                        {p.is_active ? 'Active' : 'Inactive'}
                      </span>
                      <Button
                        variant={p.is_active ? 'ghost' : 'secondary'}
                        size="sm"
                        loading={togglingPromo === p.id}
                        onClick={() => togglePromo(p)}
                        title={p.is_active ? 'Deactivate' : 'Activate'}
                      >
                        {p.is_active ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                        {p.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Config Tab */}
        {tab === 'config' && (
          <div className={styles.section}>
            <h2>System Configuration</h2>
            <div className={styles.configCard}>
              <h3>Tax Rate</h3>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                Set the global tax rate applied to all orders. Enter a decimal value (e.g. 0.12 for 12%).
              </p>
              <form onSubmit={updateTax} style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                <div style={{ flex: '1 1 160px' }}>
                  <Input
                    label="New Tax Rate (0–1)"
                    type="number"
                    min="0"
                    max="1"
                    step="0.001"
                    value={taxRate}
                    onChange={e => setTaxRate(e.target.value)}
                    placeholder="e.g. 0.12"
                    required
                  />
                </div>
                <Button type="submit" loading={savingTax} style={{ marginBottom: 1 }}>
                  <Settings size={14} /> Update Tax Rate
                </Button>
              </form>
              {taxRate && !isNaN(taxRate) && (
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
                  Preview: {(Number(taxRate) * 100).toFixed(2)}%
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}