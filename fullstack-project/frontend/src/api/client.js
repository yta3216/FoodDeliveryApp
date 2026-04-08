const BASE_URL = '';

function getToken() {
  return localStorage.getItem('auth_token');
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: 'PATCH', body: body !== undefined ? JSON.stringify(body) : undefined }),
  delete: (path) => request(path, { method: 'DELETE' }),
};

export const userApi = {
  login: (email, password) => api.post('/user/login', { email, password }),
  register: (data) => api.post('/user', data),
  getById: (id) => api.get(`/user/${id}`),
  update: (id, data) => api.put(`/user/${id}`, data),
  updatePassword: (id, data) => api.patch(`/user/${id}/password`, data),
  requestReset: (email) => api.post('/user/password-reset/request', { email }),
  performReset: (token, new_password) => api.patch('/user/password-reset', { reset_token: token, new_password }),
  getNotifications: (id) => api.get(`/user/${id}/notifications`),
  readNotification: (userId, notifId) => api.patch(`/user/${userId}/notifications/${notifId}/read`),
  // Favourites - customer only
  getFavourites: () => api.get('/user/me/favourites'),
  addFavourite: (restaurantId) => api.post(`/user/me/favourites/${restaurantId}`),
  removeFavourite: (restaurantId) => api.delete(`/user/me/favourites/${restaurantId}`),
};

export const restaurantApi = {
  // Basic fetch-all (keeps backward compat)
  getAll: () => api.get('/restaurant/search?page_size=50').then(r => r.results ?? r),
  // Advanced search - passes name, city, menu_item, sort_price, page, page_size to backend
  search: (params = {}) => {
    const qs = new URLSearchParams({ page_size: 50, ...params }).toString();
    return api.get(`/restaurant/search?${qs}`);
  },
  getById: (id) => api.get('/restaurant/search?page_size=50').then(r => (r.results ?? r).find(r => r.id === Number(id))),
  create: (data) => api.post('/restaurant', data),
  update: (id, data) => api.put(`/restaurant/${id}`, { id, ...data }),
  updateManagers: (id, manager_ids) => api.patch(`/restaurant/${id}/managers`, { id, manager_ids }),
  createMenuItem: (restaurantId, data) => api.post(`/restaurant/${restaurantId}/menu`, data),
  updateMenuItem: (restaurantId, data) => api.put(`/restaurant/${restaurantId}/menu/${data.id}`, data),
  bulkCreateMenuItems: (restaurantId, items) => api.post(`/restaurant/${restaurantId}/menu/bulk`, { items }),
  bulkUpdateMenuItems: (restaurantId, items) => api.put(`/restaurant/${restaurantId}/menu/bulk`, { items }),
  delete: (id) => api.delete(`/restaurant/${id}`),
};

export const cartApi = {
  get: () => api.get('/cart'),
  setRestaurant: (restaurantId) => api.patch(`/cart/${restaurantId}`),
  addItem: (data) => api.post('/cart/item', data),
  updateItem: (itemId, newQty) => api.patch(`/cart/item/${itemId}`, { new_qty: newQty }),
  removeItem: (itemId) => api.delete(`/cart/item/${itemId}`),
  clear: () => api.delete('/cart'),
};

export const orderApi = {
  getForCustomer: () => api.get('/order/customer'),
  getForRestaurant: (restaurantId) => api.get(`/order/restaurant/${restaurantId}`),
  cancel: (orderId) => api.delete(`/order/${orderId}`),
  acceptReject: (orderId, status) => api.patch(`/order/${orderId}/status`, { status }),
  markReady: (orderId) => api.patch(`/order/${orderId}/ready`),
};

export const paymentApi = {
  topup: (data) => api.patch('/payment/topup-wallet', data),
  checkout: (receiptId) => api.post('/payment/checkout', { receipt_id: receiptId }),
};

// receiptApi.get - backend is GET /receipt?distance_km=X (was incorrectly POST before)
export const receiptApi = {
  get: (distanceKm = 0.0) => api.get(`/receipt?distance_km=${distanceKm}`),
  getById: (id) => api.get(`/receipt/${id}`),
};

export const deliveryApi = {
  updateStatus: (status) => api.patch(`/delivery/status?status=${status}`),
  startDelivery: (orderId) => api.patch(`/delivery/${orderId}/start`),
  completeDelivery: (orderId) => api.patch(`/delivery/${orderId}/complete`),
  getByOrder: (orderId) => api.get(`/delivery/${orderId}`),
};

export const promoApi = {
  getPublic: () => api.get('/promo'),
  getAll: () => api.get('/promo/all'),
  apply: (code) => api.post('/promo/apply', { code }),
  remove: () => api.delete('/promo/remove'),
  create: (data) => api.post('/promo', data),
  updateStatus: (id, is_active) => api.patch(`/promo/${id}/status`, { is_active }),
};

export const configApi = {
  setTaxRate: (rate) => api.patch(`/config/tax-rate?new_tax_rate=${rate}`),
};