import axios from 'axios';

const normalizeBaseUrl = (url) => {
  if (!url) return '';
  return url.replace(/\/$/, '');
};

const collectBaseUrls = () => {
  const candidates = [];
  const add = (url) => {
    const normalized = normalizeBaseUrl(url);
    if (normalized && !candidates.includes(normalized)) {
      candidates.push(normalized);
    }
  };

  add(process.env.REACT_APP_BACKEND_URL);

  if (typeof window !== 'undefined') {
    const host = window.location.hostname || '127.0.0.1';
    add(window.location.origin); // для reverse-proxy / same-origin
    add(`http://${host}:8001`);  // дефолт из Makefile/README
    add(`http://${host}:8000`);  // частый локальный fallback
  }

  add('http://127.0.0.1:8001');
  add('http://127.0.0.1:8000');

  return candidates;
};

const BASE_URLS = collectBaseUrls();
const API_URL = BASE_URLS[0] || 'http://127.0.0.1:8001';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error?.config;

    if (!config || config.__fallbackTried) {
      return Promise.reject(error);
    }

    const status = error?.response?.status;
    const networkLikeError = !status || error.code === 'ECONNABORTED' || error.message?.includes('Network Error');

    if (!networkLikeError || BASE_URLS.length < 2) {
      return Promise.reject(error);
    }

    const currentBaseUrl = normalizeBaseUrl(config.baseURL || api.defaults.baseURL);
    const nextBaseUrl = BASE_URLS.find((url) => url !== currentBaseUrl);

    if (!nextBaseUrl) {
      return Promise.reject(error);
    }

    config.__fallbackTried = true;
    config.baseURL = nextBaseUrl;

    return api.request(config);
  }
);

export default api;

export const profilesAPI = {
  getAll: (params) => api.get('/api/profiles', { params }),
  getById: (id, params) => api.get(`/api/profiles/${id}`, { params }),
  create: (data) => api.post('/api/profiles', data),
  update: (id, data) => api.put(`/api/profiles/${id}`, data),
  delete: (id) => api.delete(`/api/profiles/${id}`),
};

export const adminAPI = {
  login: (credentials) => api.post('/api/admin/login', credentials),
  getMe: () => api.get('/api/admin/me'),
  getStats: () => api.get('/api/admin/stats'),
};

export const contactAPI = {
  submit: (data) => api.post('/api/contact', data),
};

export const cloudinaryAPI = {
  getSignature: (params) => api.get('/api/cloudinary/signature', { params }),
};
