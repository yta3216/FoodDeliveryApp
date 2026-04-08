import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { restaurantApi, cartApi } from '../../api/client';
import { Button, Spinner, EmptyState } from '../../components/common/UI';
import { MapPin, ShoppingCart, Plus, Minus, Tag, ShoppingBag } from 'lucide-react';
import { useToast } from '../../hooks/useToast';
import { Toast } from '../../components/common/UI';
import styles from './RestaurantPage.module.css';

export default function RestaurantPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast, show, hide } = useToast();
  const [restaurant, setRestaurant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantities, setQuantities] = useState({});
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        const [rest, cart] = await Promise.all([
          restaurantApi.getById(id),
          cartApi.get().catch(() => null),
        ]);
        setRestaurant(rest);
        // Pre-seed quantities from cart if viewing the same restaurant
        if (cart && cart.restaurant_id === Number(id) && cart.cart_items?.length) {
          const q = {};
          cart.cart_items.forEach(ci => { q[ci.menu_item_id] = ci.qty; });
          setQuantities(q);
        }
      } catch {
        show('Restaurant not found', 'error');
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [id]);

  const setQty = (itemId, delta) => {
    setQuantities(q => ({ ...q, [itemId]: Math.max(0, (q[itemId] || 0) + delta) }));
  };

  const totalSelected = Object.values(quantities).reduce((s, q) => s + q, 0);

  const handleAddAll = async () => {
    const entries = Object.entries(quantities).filter(([, qty]) => qty > 0);
    if (!entries.length) return show('Select at least one item first', 'error');
    setAdding(true);
    try {
      await cartApi.setRestaurant(Number(id));
      for (const [itemId, qty] of entries) {
        await cartApi.addItem({ menu_item_id: Number(itemId), qty });
      }
      show(`${totalSelected} item${totalSelected !== 1 ? 's' : ''} added to cart!`, 'success');
      setQuantities({});
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setAdding(false);
    }
  };

  if (loading) return <div className="page"><Spinner center size={36} /></div>;
  if (!restaurant) return <div className="page"><EmptyState icon="❌" title="Restaurant not found" /></div>;

  const items = restaurant.menu?.items || [];
  const combos = (restaurant.menu?.combos || []).filter(c => c.is_active);

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}

      <div className={styles.header}>
        <div className="container">
          <div className={styles.headerContent}>
            <div className={styles.restaurantEmoji}>{getEmoji(restaurant.name)}</div>
            <div className={styles.restaurantInfo}>
              <h1>{restaurant.name}</h1>
              <div className={styles.meta}>
                <span><MapPin size={14} /> {restaurant.city}</span>
                <span>📦 {restaurant.delivery_fee === 0 ? 'Free delivery' : `$${restaurant.delivery_fee.toFixed(2)} delivery`}</span>
                <span>🚗 {restaurant.max_delivery_radius_km} km radius</span>
              </div>
            </div>
            <Button variant="secondary" onClick={() => navigate('/cart')}>
              <ShoppingCart size={16} /> View Cart
            </Button>
          </div>
        </div>
      </div>

      <div className="container">
        {/* Combo Deals Section */}
        {combos.length > 0 && (
          <div className={styles.menuSection}>
            <h2 className={styles.menuTitle}>🎁 Combo Deals <span>({combos.length})</span></h2>
            <div className={styles.combosGrid}>
              {combos.map(combo => {
                const comboItems = combo.item_ids
                  .map(cid => items.find(i => i.id === cid))
                  .filter(Boolean);
                return (
                  <div key={combo.id} className={styles.comboCard}>
                    <div className={styles.comboHeader}>
                      <span className={styles.comboName}>{combo.name}</span>
                      <span className={styles.comboBadge}>
                        {combo.type === 'percentage'
                          ? `${combo.discount}% off`
                          : `-$${Number(combo.discount).toFixed(2)}`}
                      </span>
                    </div>
                    <div className={styles.comboItemsList}>
                      {comboItems.map(item => (
                        <span key={item.id} className={styles.comboItemChip}>
                          {getItemEmoji(item.name)} {item.name}
                          <span className={styles.comboItemPrice}>${item.price.toFixed(2)}</span>
                        </span>
                      ))}
                    </div>
                    <p className={styles.comboHint}>
                      Add all items to cart — discount applies automatically at checkout
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Menu Items */}
        <div className={styles.menuSection}>
          <h2 className={styles.menuTitle}>Menu <span>({items.length} items)</span></h2>
          {items.length === 0 ? (
            <EmptyState icon="🍽️" title="No menu items yet" subtitle="This restaurant hasn't added their menu." />
          ) : (
            <div className={styles.grid}>
              {items.map(item => (
                <div key={item.id} className={styles.menuCard}>
                  <div className={styles.menuCardTop}>
                    <div className={styles.menuEmoji}>{getItemEmoji(item.name)}</div>
                    <div className={styles.menuInfo}>
                      <h3>{item.name}</h3>
                      <div className={styles.tags}>
                        {item.tags?.map(t => (
                          <span key={t} className={styles.tag}><Tag size={10} />{t}</span>
                        ))}
                      </div>
                    </div>
                    <span className={styles.price}>${item.price.toFixed(2)}</span>
                  </div>
                  <div className={styles.menuCardActions}>
                    <div className={styles.qtyControl}>
                      <button onClick={() => setQty(item.id, -1)} disabled={!quantities[item.id]}>
                        <Minus size={14} />
                      </button>
                      <span>{quantities[item.id] || 0}</span>
                      <button onClick={() => setQty(item.id, 1)}>
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {totalSelected > 0 && (
        <div className={styles.stickyAddBar}>
          <div className="container" style={{ display: 'flex', justifyContent: 'center' }}>
            <Button loading={adding} onClick={handleAddAll} size="lg">
              <ShoppingBag size={16} />
              Add {totalSelected} item{totalSelected !== 1 ? 's' : ''} to Cart
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

const emojiMap = ['🍕', '🍣', '🌮', '🍜', '🍔', '🥗', '🍱', '🥩', '🍛', '🌯'];
function getEmoji(name) { return emojiMap[name.charCodeAt(0) % emojiMap.length]; }
function getItemEmoji(name) {
  const lower = name.toLowerCase();
  if (lower.includes('pizza')) return '🍕';
  if (lower.includes('sushi') || lower.includes('salmon')) return '🍣';
  if (lower.includes('burger')) return '🍔';
  if (lower.includes('taco')) return '🌮';
  if (lower.includes('salad')) return '🥗';
  if (lower.includes('pasta') || lower.includes('noodle')) return '🍜';
  if (lower.includes('chicken')) return '🍗';
  if (lower.includes('soup')) return '🍲';
  if (lower.includes('rice')) return '🍚';
  if (lower.includes('steak') || lower.includes('beef')) return '🥩';
  return '🍽️';
}