import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { restaurantApi } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Button, Spinner, EmptyState, Modal, Input, Toast } from '../../components/common/UI';
import { useToast } from '../../hooks/useToast';
import { Plus, Edit, ChefHat, Settings, Users } from 'lucide-react';
import styles from './ManagerPage.module.css';

const EMPTY_FORM = { name: '', city: '', street: '', province: '', postal_code: '', delivery_fee: '', max_delivery_radius_km: '10' };

export default function ManagerDashboard() {
  const { user } = useAuth();
  const { toast, show, hide } = useToast();
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [createModal, setCreateModal] = useState(false);
  const [editModal, setEditModal] = useState(null);
  const [menuModal, setMenuModal] = useState(null);
  const [managersModal, setManagersModal] = useState(null); // { id, manager_ids }

  const [createForm, setCreateForm] = useState(EMPTY_FORM);
  const [editForm, setEditForm] = useState(EMPTY_FORM);
  const [addItemForm, setAddItemForm] = useState({ name: '', price: '', tags: '' });
  const [editItemForm, setEditItemForm] = useState(null);
  const [managersInput, setManagersInput] = useState(''); // comma-separated IDs

  const cf = (field) => (e) => setCreateForm(f => ({ ...f, [field]: e.target.value }));
  const ef = (field) => (e) => setEditForm(f => ({ ...f, [field]: e.target.value }));

  const refresh = async () => {
    const all = await restaurantApi.getAll();
    const mine = all.filter(r => r.manager_ids?.includes(user?.user_id));
    setRestaurants(mine);
    return mine;
  };

  useEffect(() => {
    refresh().catch(e => show(e.message, 'error')).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      await restaurantApi.create({
        name: createForm.name, city: createForm.city,
        address: { street: createForm.street, city: createForm.city, province: createForm.province.trim().toUpperCase(), postal_code: createForm.postal_code.trim().toUpperCase() },
        delivery_fee: Number(createForm.delivery_fee) || 0,
        max_delivery_radius_km: Number(createForm.max_delivery_radius_km) || 10,
      });
      show('Restaurant created!', 'success');
      setCreateModal(false); setCreateForm(EMPTY_FORM);
      await refresh();
    } catch (err) { show(err.message, 'error'); } finally { setSaving(false); }
  };

  const openEdit = (r) => {
    setEditForm({ name: r.name, city: r.city, street: r.address?.street || '', province: r.address?.province || '', postal_code: r.address?.postal_code || '', delivery_fee: String(r.delivery_fee ?? ''), max_delivery_radius_km: String(r.max_delivery_radius_km ?? '10') });
    setEditModal(r);
  };

  const handleEdit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      await restaurantApi.update(editModal.id, {
        name: editForm.name, city: editForm.city,
        address: { street: editForm.street, city: editForm.city, province: editForm.province.trim().toUpperCase(), postal_code: editForm.postal_code.trim().toUpperCase() },
        delivery_fee: Number(editForm.delivery_fee) || 0,
        max_delivery_radius_km: Number(editForm.max_delivery_radius_km) || 10,
      });
      show('Restaurant updated!', 'success');
      setEditModal(null);
      await refresh();
    } catch (err) { show(err.message, 'error'); } finally { setSaving(false); }
  };

  const handleAddItem = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const tags = addItemForm.tags.split(',').map(t => t.trim()).filter(Boolean);
      await restaurantApi.createMenuItem(menuModal.id, { name: addItemForm.name, price: Number(addItemForm.price), tags });
      show('Item added!', 'success');
      setAddItemForm({ name: '', price: '', tags: '' });
      const mine = await refresh();
      const updated = mine.find(r => r.id === menuModal.id);
      if (updated) setMenuModal(updated);
    } catch (err) { show(err.message, 'error'); } finally { setSaving(false); }
  };

  const handleEditItem = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const tags = editItemForm.tags.split(',').map(t => t.trim()).filter(Boolean);
      await restaurantApi.updateMenuItem(menuModal.id, { id: editItemForm.id, name: editItemForm.name, price: Number(editItemForm.price), tags });
      show('Item updated!', 'success');
      setEditItemForm(null);
      const mine = await refresh();
      const updated = mine.find(r => r.id === menuModal.id);
      if (updated) setMenuModal(updated);
    } catch (err) { show(err.message, 'error'); } finally { setSaving(false); }
  };

  const openManagers = (r) => {
    setManagersInput(r.manager_ids?.join(', ') || '');
    setManagersModal(r);
  };

  const handleUpdateManagers = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const ids = managersInput.split(',').map(s => s.trim()).filter(Boolean);
      await restaurantApi.updateManagers(managersModal.id, ids);
      show('Managers updated!', 'success');
      setManagersModal(null);
      await refresh();
    } catch (err) { show(err.message, 'error'); } finally { setSaving(false); }
  };

  if (loading) return <div className="page"><Spinner center size={36} /></div>;

  const RestaurantForm = ({ form, onChange, onSubmit, submitLabel }) => (
    <form onSubmit={onSubmit} className={styles.formGrid}>
      <Input label="Restaurant Name" value={form.name} onChange={onChange('name')} required />
      <Input label="City" value={form.city} onChange={onChange('city')} required placeholder="e.g. Kelowna" />
      <Input label="Street Address" value={form.street} onChange={onChange('street')} required placeholder="e.g. 123 Main St" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Input label="Province" value={form.province} onChange={onChange('province')} required placeholder="BC" maxLength={2} />
        <Input label="Postal Code" value={form.postal_code} onChange={onChange('postal_code')} required placeholder="V1Y 1A1" />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Input label="Delivery Fee ($)" type="number" min="0" step="0.01" value={form.delivery_fee} onChange={onChange('delivery_fee')} />
        <Input label="Max Delivery Radius (km)" type="number" min="0" step="0.1" value={form.max_delivery_radius_km} onChange={onChange('max_delivery_radius_km')} />
      </div>
      <Button type="submit" loading={saving}>{submitLabel}</Button>
    </form>
  );

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}

      {/* Create Restaurant Modal */}
      <Modal open={createModal} onClose={() => setCreateModal(false)} title="New Restaurant">
        <RestaurantForm form={createForm} onChange={cf} onSubmit={handleCreate} submitLabel="Create Restaurant" />
      </Modal>

      {/* Edit Restaurant Modal */}
      <Modal open={!!editModal} onClose={() => setEditModal(null)} title="Edit Restaurant">
        {editModal && <RestaurantForm form={editForm} onChange={ef} onSubmit={handleEdit} submitLabel="Save Changes" />}
      </Modal>

      {/* Update Managers Modal */}
      <Modal open={!!managersModal} onClose={() => setManagersModal(null)} title="Manage Restaurant Managers">
        {managersModal && (
          <form onSubmit={handleUpdateManagers} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0 }}>
              Enter the user IDs of all managers for <strong>{managersModal.name}</strong>, separated by commas.
              This overwrites the current list.
            </p>
            <Input
              label="Manager User IDs (comma-separated)"
              value={managersInput}
              onChange={e => setManagersInput(e.target.value)}
              placeholder="uuid-1, uuid-2, ..."
            />
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Current: {managersModal.manager_ids?.join(', ') || 'none'}
            </div>
            <Button type="submit" loading={saving}><Users size={14} /> Update Managers</Button>
          </form>
        )}
      </Modal>

      {/* Menu Modal */}
      <Modal open={!!menuModal} onClose={() => { setMenuModal(null); setEditItemForm(null); }} title={`Menu — ${menuModal?.name}`}>
        {menuModal && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Existing items */}
            {menuModal.menu?.items?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {menuModal.menu.items.map(item => (
                  <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(255,255,255,0.06)', borderRadius: 8 }}>
                    {editItemForm?.id === item.id ? (
                      <form onSubmit={handleEditItem} style={{ display: 'flex', gap: 8, flex: 1, flexWrap: 'wrap' }}>
                        <Input value={editItemForm.name} onChange={e => setEditItemForm(f => ({ ...f, name: e.target.value }))} required style={{ flex: '2 1 120px' }} />
                        <Input type="number" min="0" step="0.01" value={editItemForm.price} onChange={e => setEditItemForm(f => ({ ...f, price: e.target.value }))} required style={{ flex: '1 1 80px' }} />
                        <Input value={editItemForm.tags} onChange={e => setEditItemForm(f => ({ ...f, tags: e.target.value }))} placeholder="tags" style={{ flex: '1 1 100px' }} />
                        <Button type="submit" size="sm" loading={saving}>Save</Button>
                        <Button type="button" variant="ghost" size="sm" onClick={() => setEditItemForm(null)}>Cancel</Button>
                      </form>
                    ) : (
                      <>
                        <div>
                          <strong>{item.name}</strong>
                          <span style={{ marginLeft: 8, color: 'var(--text-muted)', fontSize: 13 }}>${item.price?.toFixed(2)}</span>
                          {item.tags?.length > 0 && <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--text-muted)' }}>{item.tags.join(', ')}</span>}
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => setEditItemForm({ id: item.id, name: item.name, price: String(item.price), tags: item.tags?.join(', ') || '' })}>
                          <Edit size={13} />
                        </Button>
                      </>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No menu items yet.</p>
            )}

            {/* Add new item */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
              <h4 style={{ margin: '0 0 10px', fontSize: 13 }}>Add New Item</h4>
              <form onSubmit={handleAddItem} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <Input label="Item Name" value={addItemForm.name} onChange={e => setAddItemForm(f => ({ ...f, name: e.target.value }))} required />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <Input label="Price ($)" type="number" min="0" step="0.01" value={addItemForm.price} onChange={e => setAddItemForm(f => ({ ...f, price: e.target.value }))} required />
                  <Input label="Tags (comma separated)" value={addItemForm.tags} onChange={e => setAddItemForm(f => ({ ...f, tags: e.target.value }))} placeholder="spicy, vegetarian" />
                </div>
                <Button type="submit" size="sm" loading={saving}><Plus size={14} /> Add Item</Button>
              </form>
            </div>
          </div>
        )}
      </Modal>

      <div className="container">
        <div className={styles.header}>
          <div>
            <h1>Manager Dashboard</h1>
            <p className={styles.sub}>Manage your restaurants and menus</p>
          </div>
          <Button onClick={() => setCreateModal(true)}><Plus size={16} /> New Restaurant</Button>
        </div>

        {restaurants.length === 0 ? (
          <EmptyState icon={<ChefHat size={48} />} title="No restaurants yet" subtitle="Create your first restaurant to get started." />
        ) : (
          <div className={styles.grid}>
            {restaurants.map(r => (
              <div key={r.id} className={styles.card}>
                <div className={styles.cardHeader}>
                  <div className={styles.cardEmoji}>{getEmoji(r.name)}</div>
                  <div>
                    <h3>{r.name}</h3>
                    <p className={styles.cardCity}>{r.city}{r.address?.province ? ` · ${r.address.province}` : ''}</p>
                  </div>
                </div>
                <div className={styles.cardStats}>
                  <div><span>{r.menu?.items?.length || 0}</span><label>Items</label></div>
                  <div><span>${r.delivery_fee?.toFixed(2)}</span><label>Delivery</label></div>
                  <div><span>{r.max_delivery_radius_km}km</span><label>Radius</label></div>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '0 0 8px', wordBreak: 'break-all' }}>
                  {r.manager_ids?.length || 0} manager(s)
                </div>
                <div className={styles.cardActions} style={{ flexWrap: 'wrap' }}>
                  <Button variant="ghost" size="sm" onClick={() => { setMenuModal(r); setEditItemForm(null); }}>
                    <Edit size={14} /> Menu
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => openEdit(r)}>
                    <Settings size={14} /> Details
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => openManagers(r)}>
                    <Users size={14} /> Managers
                  </Button>
                  <Link to="/manager/orders">
                    <Button variant="secondary" size="sm">Orders</Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const emojiMap = ['🍕', '🍣', '🌮', '🍜', '🍔', '🥗', '🍱', '🥩', '🍛', '🌯'];
function getEmoji(name) { return emojiMap[name.charCodeAt(0) % emojiMap.length]; }