import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { restaurantApi, userApi } from '../../api/client';
import { Spinner, EmptyState, Button, Toast } from '../../components/common/UI';
import { useToast } from '../../hooks/useToast';
import { Search, MapPin, Heart, SlidersHorizontal, X } from 'lucide-react';
import styles from './CustomerHome.module.css';

const emojiMap = ['🍕', '🍣', '🌮', '🍜', '🍔', '🥗', '🍱', '🥩', '🍛', '🌯'];
function getEmoji(name) { return emojiMap[(name?.charCodeAt(0) ?? 0) % emojiMap.length]; }

const EMPTY_FILTERS = { name: '', city: '', menu_item: '', sort_price: '' };

export default function CustomerHomePage() {
  const { toast, show, hide } = useToast();

  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);

  const [favourites, setFavourites] = useState([]);
  const [favIds, setFavIds] = useState(new Set());
  const [favLoading, setFavLoading] = useState(true);
  const [togglingFav, setTogglingFav] = useState(null);

  const [tab, setTab] = useState('all'); // 'all' | 'favourites'
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [showFilters, setShowFilters] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const setF = (k) => (e) => setFilters(f => ({ ...f, [k]: e.target.value }));

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const all = await restaurantApi.getAll();
      setRestaurants(all);
    } catch (e) {
      show(e.message, 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadFavourites = useCallback(async () => {
    setFavLoading(true);
    try {
      const favs = await userApi.getFavourites();
      setFavourites(favs);
      setFavIds(new Set(favs.map(f => f.id)));
    } catch (_) {
      // non-customer roles won't have favourites
    } finally {
      setFavLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
    loadFavourites();
  }, []);

  const handleSearch = async () => {
    const params = {};
    if (filters.name.trim()) params.name = filters.name.trim();
    if (filters.city.trim()) params.city = filters.city.trim();
    if (filters.menu_item.trim()) params.menu_item = filters.menu_item.trim();
    if (filters.sort_price) params.sort_price = filters.sort_price;

    setSearching(true);
    try {
      const result = await restaurantApi.search(params);
      setRestaurants(result.results ?? result);
      setHasSearched(true);
      setTab('all');
    } catch (e) {
      show(e.message, 'error');
    } finally {
      setSearching(false);
    }
  };

  const resetFilters = async () => {
    setFilters(EMPTY_FILTERS);
    setHasSearched(false);
    await loadAll();
  };

  const toggleFavourite = async (restaurantId, e) => {
    e.preventDefault();
    e.stopPropagation();
    if (togglingFav === restaurantId) return;
    setTogglingFav(restaurantId);
    try {
      if (favIds.has(restaurantId)) {
        await userApi.removeFavourite(restaurantId);
        setFavIds(prev => { const s = new Set(prev); s.delete(restaurantId); return s; });
        setFavourites(prev => prev.filter(f => f.id !== restaurantId));
        show('Removed from favourites', 'success');
      } else {
        await userApi.addFavourite(restaurantId);
        setFavIds(prev => new Set([...prev, restaurantId]));
        const r = restaurants.find(r => r.id === restaurantId);
        if (r) setFavourites(prev => [...prev, r]);
        show('Added to favourites ❤️', 'success');
      }
    } catch (e) {
      show(e.message, 'error');
    } finally {
      setTogglingFav(null);
    }
  };

  const isFiltered = filters.name || filters.city || filters.menu_item || filters.sort_price;
  const displayed = tab === 'favourites' ? favourites : restaurants;
  const isLoading = tab === 'favourites' ? favLoading : loading;

  return (
    <div className={`page ${styles.page}`}>
      {toast && <Toast message={toast.message} type={toast.type} onClose={hide} />}

      {/* Hero + Search */}
      <div className={styles.hero}>
        <div className="container">
          <p className={styles.heroEyebrow}>🍔 Food delivery</p>
          <h1 className={styles.heroTitle}>What are you<br /><span>craving today?</span></h1>

          <div className={styles.searchWrap}>
            <Search size={18} className={styles.searchIcon} />
            <input
              className={styles.searchInput}
              placeholder="Search restaurant name..."
              value={filters.name}
              onChange={setF('name')}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
            />
            <button
              className={styles.filterToggleBtn}
              onClick={() => setShowFilters(v => !v)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4, padding: '0 8px', fontSize: 13 }}
            >
              <SlidersHorizontal size={15} /> Filters
            </button>
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 12 }}>
              <input
                className={styles.searchInput}
                style={{ flex: '1 1 140px', marginTop: 0 }}
                placeholder="City"
                value={filters.city}
                onChange={setF('city')}
              />
              <input
                className={styles.searchInput}
                style={{ flex: '1 1 180px', marginTop: 0 }}
                placeholder="Menu item (e.g. Burger)"
                value={filters.menu_item}
                onChange={setF('menu_item')}
              />
              <select
                className={styles.searchInput}
                style={{ flex: '1 1 160px', marginTop: 0, background: 'var(--bg-card, #fff)' }}
                value={filters.sort_price}
                onChange={setF('sort_price')}
              >
                <option value="">Sort by avg. price</option>
                <option value="asc">Price: Low → High</option>
                <option value="desc">Price: High → Low</option>
              </select>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <Button size="sm" onClick={handleSearch} loading={searching}>Search</Button>
                {isFiltered && (
                  <Button size="sm" variant="ghost" onClick={resetFilters}>
                    <X size={13} /> Reset
                  </Button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="container">
        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--border)', paddingBottom: 0 }}>
          {[
            { id: 'all', label: 'All Restaurants' },
            { id: 'favourites', label: `❤️ Favourites${favIds.size > 0 ? ` (${favIds.size})` : ''}` },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                padding: '10px 16px', fontSize: 14, fontWeight: 600,
                color: tab === t.id ? 'var(--primary)' : 'var(--text-muted)',
                borderBottom: tab === t.id ? '2px solid var(--primary)' : '2px solid transparent',
                marginBottom: -1, transition: 'all .15s',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2>
              {tab === 'favourites' ? 'Your Favourites' :
                hasSearched ? 'Search Results' : 'All Restaurants'}
            </h2>
            <span className={styles.count}>{displayed.length} places</span>
          </div>

          {isLoading ? (
            <Spinner center size={32} />
          ) : displayed.length === 0 ? (
            <EmptyState
              icon={tab === 'favourites' ? '❤️' : '🍽️'}
              title={tab === 'favourites' ? 'No favourites yet' : 'No restaurants found'}
              subtitle={tab === 'favourites' ? 'Heart a restaurant to save it here.' : 'Try adjusting your search filters.'}
            />
          ) : (
            <div className={styles.grid}>
              {displayed.map(r => (
                <div key={r.id} className={styles.card} style={{ position: 'relative' }}>
                  {/* Favourite button */}
                  <button
                    onClick={(e) => toggleFavourite(r.id, e)}
                    disabled={togglingFav === r.id}
                    style={{
                      position: 'absolute', top: 12, right: 12, zIndex: 1,
                      background: 'rgba(255,255,255,0.9)', border: 'none', borderRadius: '50%',
                      width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      cursor: 'pointer', color: favIds.has(r.id) ? '#e74c3c' : 'var(--text-muted)',
                      transition: 'all .15s', boxShadow: '0 1px 4px rgba(0,0,0,.15)',
                    }}
                    title={favIds.has(r.id) ? 'Remove from favourites' : 'Add to favourites'}
                  >
                    <Heart size={15} fill={favIds.has(r.id) ? 'currentColor' : 'none'} />
                  </button>

                  <Link to={`/restaurant/${r.id}`} className={styles.cardLink}>
                    <div className={styles.cardEmoji}>{getEmoji(r.name)}</div>
                    <div className={styles.cardBody}>
                      <h3>{r.name}</h3>
                      <div className={styles.meta}>
                        <span><MapPin size={12} /> {r.city}</span>
                        {r.max_delivery_radius_km > 0 && (
                          <span>📍 {r.max_delivery_radius_km} km radius</span>
                        )}
                      </div>
                    </div>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}