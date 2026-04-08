import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { cartApi, receiptApi, paymentApi, promoApi, restaurantApi } from '../../api/client';
import { Button, Spinner, EmptyState, Input, Toast } from '../../components/common/UI';
import { Minus, Plus, Tag, ShoppingBag, MapPin, X } from 'lucide-react';
import { useToast } from '../../hooks/useToast';
import styles from './CartPage.module.css';

const getItemEmoji = (name) => {
  const n = name.toLowerCase();
  if (n.includes('pizza')) return '🍕';
  if (n.includes('sushi') || n.includes('roll')) return '🍣';
  if (n.includes('burger')) return '🍔';
  if (n.includes('taco')) return '🌮';
  if (n.includes('noodle') || n.includes('ramen')) return '🍜';
  if (n.includes('salad')) return '🥗';
  if (n.includes('chicken')) return '🍗';
  return '🍽️';
};

const EMPTY_ADDR = { street: '', city: '', province: '', postal_code: '' };

export default function CartPage() {
  const navigate = useNavigate();
  const { toast, show, hide } = useToast();
  const [cart, setCart] = useState(null);
  const [restaurant, setRestaurant] = useState(null);
  const [receipt, setReceipt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [promoCode, setPromoCode] = useState('');
  const [promoApplied, setPromoApplied] = useState(false);
  const [checkingOut, setCheckingOut] = useState(false);
  const [generatingReceipt, setGeneratingReceipt] = useState(false);
  const [removingPromo, setRemovingPromo] = useState(false);
  // Delivery details
  const [address, setAddress] = useState(EMPTY_ADDR);
  const [distanceKm, setDistanceKm] = useState('');
  const setA = (k) => (e) => { setAddress(a => ({ ...a, [k]: e.target.value })); setReceipt(null); };

  const fetchCart = useCallback(async () => {
    try {
      const c = await cartApi.get();
      setCart(c);
      // Pre-fill promo state if cart already has a code
      if (c.promo_code) {
        setPromoCode(c.promo_code);
        setPromoApplied(true);
      }
      if (c.restaurant_id) {
        const r = await restaurantApi.getById(c.restaurant_id);
        setRestaurant(r);
      }
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchCart(); }, []);

  const updateQty = async (itemId, newQty) => {
    try {
      if (newQty <= 0) {
        await cartApi.removeItem(itemId);
      } else {
        await cartApi.updateItem(itemId, newQty);
      }
      generateReceipt();
      await fetchCart();
    } catch (err) {
      show(err.message, 'error');
    }
  };

  const clearCart = async () => {
    try {
      await cartApi.clear();
      setCart(null); setRestaurant(null); setReceipt(null);
      setPromoCode(''); setPromoApplied(false);
    } catch (err) {
      show(err.message, 'error');
    }
  };

  // Apply promo to cart via POST /promo/apply (saves to cart server-side)
  const applyPromo = async () => {
    if (!promoCode.trim()) return;
    try {
      await promoApi.apply(promoCode.trim());
      setPromoApplied(true);
      generateReceipt();
      show('Promo code applied! ✅', 'success');
    } catch (err) {
      show(err.message, 'error');
    }
  };

  // Remove promo from cart via DELETE /promo/remove
  const removePromo = async () => {
    setRemovingPromo(true);
    try {
      await promoApi.remove();
      setPromoCode('');
      setPromoApplied(false);
      generateReceipt();
      show('Promo code removed', 'success');
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setRemovingPromo(false);
    }
  };

  const addressValid = address.street.trim() && address.city.trim() && address.province.trim() && address.postal_code.trim();

  // Generate receipt via GET /receipt?distance_km=X
  const generateReceipt = async () => {
    if (!addressValid) {
      return show('Please fill in all delivery address fields.', 'error');
    }
    setGeneratingReceipt(true);
    try {
      const km = parseFloat(distanceKm) || 0.0;
      const r = await receiptApi.get(km);
      setReceipt(r);
    } catch (err) {
      show(err.message, 'error');
    } finally {
      setGeneratingReceipt(false);
    }
  };

  const checkout = async () => {
    if (!receipt) return;
    setCheckingOut(true);
    try {
      await paymentApi.checkout(receipt.id);
      show('Order placed successfully! 🎉', 'success');
      navigate('/orders');
    } catch (err) {
      // 409 means receipt is stale — regenerate
      if (err.message?.includes('409') || err.message?.toLowerCase().includes('changed')) {
        show('Prices changed — receipt refreshed. Please review and confirm.', 'error');
        const km = parseFloat(distanceKm) || 0.0;
        const refreshed = await receiptApi.get(km).catch(() => null);
        if (refreshed) setReceipt(refreshed);
      } else {
        show(err.message, 'error');
      }
    } finally {
      setCheckingOut(false);
    }
  };

  if (loading) return <div className="page"><Spinner center size={36} /></div>;

  const isEmpty = !cart || !cart.cart_items || cart.cart_items.length === 0;

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}

      {isEmpty ? (
        <div className="container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 80, gap: 16 }}>
          <EmptyState
            icon={<ShoppingBag size={48} />}
            title="Your cart is empty"
            subtitle="Browse restaurants and add some food!"
          />
          <Button onClick={() => navigate('/home')}>Browse Restaurants</Button>
        </div>
      ) : (
        <div className="container">
          <div className={styles.layout}>
            {/* Left: cart items + promo + address */}
            <div className={styles.main}>
              {restaurant && (
                <p className={styles.fromLabel}>Ordering from <strong>{restaurant.name}</strong></p>
              )}

              {/* Cart Items */}
              <div className={styles.items}>
                {cart.cart_items.map(item => {
                  const menuItem = restaurant?.menu?.items?.find(i => i.id === item.menu_item_id);
                  return (
                    <div key={item.menu_item_id} className={styles.item}>
                      <div className={styles.itemEmoji}>{getItemEmoji(menuItem?.name || '')}</div>
                      <div className={styles.itemInfo}>
                        <span className={styles.itemName}>{menuItem?.name || `Item #${item.menu_item_id}`}</span>
                        <span className={styles.itemPrice}>${((menuItem?.price || 0) * item.qty).toFixed(2)}</span>
                      </div>
                      <div className={styles.qtyCtrl}>
                        <button onClick={() => updateQty(item.menu_item_id, item.qty - 1)}><Minus size={13} /></button>
                        <span>{item.qty}</span>
                        <button onClick={() => updateQty(item.menu_item_id, item.qty + 1)}><Plus size={13} /></button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Promo Code */}
              <div className={styles.promoRow}>
                <input
                  className={styles.promoInput}
                  placeholder="Promo code"
                  value={promoCode}
                  onChange={e => setPromoCode(e.target.value)}
                  disabled={promoApplied}
                />
                {promoApplied ? (
                  <Button variant="ghost" size="sm" onClick={removePromo} loading={removingPromo}>
                    <X size={14} /> Remove
                  </Button>
                ) : (
                  <Button variant="ghost" size="sm" onClick={applyPromo}>
                    <Tag size={14} /> Apply
                  </Button>
                )}
              </div>
              {promoApplied && (
                <p style={{ fontSize: 12, color: 'var(--green, #27ae60)', marginTop: 4 }}>
                  🎟️ Promo <strong>{promoCode}</strong> applied
                </p>
              )}

              {/* Delivery Address */}
              <div style={{ marginTop: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <MapPin size={15} /> Delivery Address
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <Input
                      label="Street"
                      placeholder="e.g. 123 Main St"
                      value={address.street}
                      onChange={setA('street')}
                    />
                  </div>
                  <Input label="City" placeholder="e.g. Kelowna" value={address.city} onChange={setA('city')} />
                  <Input label="Province" placeholder="e.g. BC" value={address.province} onChange={setA('province')} maxLength={2} />
                  <Input label="Postal Code" placeholder="e.g. V1Y 1A1" value={address.postal_code} onChange={setA('postal_code')} />
                  <Input
                    label="Distance to Restaurant (km)"
                    type="number"
                    min="0"
                    step="0.1"
                    placeholder="e.g. 3.5"
                    value={distanceKm}
                    onChange={e => { setDistanceKm(e.target.value); setReceipt(null); }}
                  />
                </div>
              </div>

              <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                <Button variant="ghost" size="sm" onClick={clearCart}>Clear Cart</Button>
              </div>
            </div>

            {/* Right: receipt + checkout */}
            <div className={styles.sidebar}>
              {receipt ? (
                <div className={styles.receipt}>
                  <h3>Order Summary</h3>
                  <div className={styles.receiptLines}>
                    {receipt.items?.map(item => (
                      <div key={item.menu_item_id} className={styles.receiptLine}>
                        <span>{item.qty}× {item.name}</span>
                        <span>${item.line_total?.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                  <div className={styles.receiptTotals}>
                    <div><span>Subtotal</span><span>${receipt.subtotal?.toFixed(2)}</span></div>
                    <div><span>Delivery fee</span><span>${receipt.delivery_fee?.toFixed(2)}</span></div>
                    <div><span>Tax</span><span>${receipt.tax?.toFixed(2)}</span></div>
                    {receipt.discount > 0 && (
                      <div style={{ color: 'var(--green)' }}>
                        <span>Discount</span><span>-${receipt.discount?.toFixed(2)}</span>
                      </div>
                    )}
                    <div className={styles.totalLine}><span>Total</span><span>${receipt.total?.toFixed(2)}</span></div>
                  </div>
                  {receipt.promo_code && (
                    <p style={{ fontSize: 12, color: 'var(--green)', marginTop: 8 }}>
                      🎟️ Promo: <strong>{receipt.promo_code}</strong>
                    </p>
                  )}
                  <Button
                    style={{ width: '100%', marginTop: 16 }}
                    onClick={checkout}
                    loading={checkingOut}
                  >
                    Pay ${receipt.total?.toFixed(2)} from Wallet
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    style={{ width: '100%', marginTop: 8 }}
                    onClick={() => setReceipt(null)}
                  >
                    Re-enter Details
                  </Button>
                </div>
              ) : (
                <div className={styles.receiptPlaceholder}>
                  <ShoppingBag size={32} style={{ opacity: 0.3 }} />
                  <p>Fill in your delivery address, then generate a receipt to see the full cost breakdown.</p>
                  <Button
                    style={{ width: '100%', marginTop: 12 }}
                    onClick={generateReceipt}
                    loading={generatingReceipt}
                    disabled={!addressValid}
                  >
                    Generate Receipt
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}