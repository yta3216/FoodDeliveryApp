import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { restaurantApi, cartApi } from '../../api/client';
import { Button, Spinner, EmptyState } from '../../components/common/UI';
import { MapPin, ShoppingCart, Plus, Minus, Tag } from 'lucide-react';
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
  const [addingItem, setAddingItem] = useState(null);

  useEffect(() => {
    restaurantApi.getById(id)
      .then(setRestaurant)
      .catch(() => show('Restaurant not found', 'error'))
      .finally(() => setLoading(false));
  }, [id]);

  const setQty = (itemId, delta) => {
    setQuantities(q => ({ ...q, [itemId]: Math.max(0, (q[itemId] || 0) + delta) }));
  };

  const handleAdd = async (item) => {
    const qty = quantities[item.id] || 0;
    if (qty <= 0) return show("Can't add zero or negative quantities", 'error');
    setAddingItem(item.id);
    try {
      await cartApi.setRestaurant(Number(id));
      await cartApi.addItem({ menu_item_id: item.id, qty });
      show(`${item.name} added to cart!`, 'success');
      setQuantities(q => ({ ...q, [item.id]: 0 }));
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setAddingItem(null);
    }
  };

  if (loading) return <div className="page"><Spinner center size={36} /></div>;
  if (!restaurant) return <div className="page"><EmptyState icon="❌" title="Restaurant not found" /></div>;

  const items = restaurant.menu?.items || [];

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
                    <Button
                      size="sm"
                      loading={addingItem === item.id}
                      onClick={() => handleAdd(item)}
                    >
                      Add to cart
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
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
