import axios from 'axios';

const normalizeBaseUrl = (url) => {
  if (!url) return '';
  return url.replace(/\/$/, '');
};

const detectBaseUrl = () => {
  const fromEnv = normalizeBaseUrl(process.env.REACT_APP_BACKEND_URL);
  if (fromEnv) {
    return fromEnv;
  }

  if (typeof window !== 'undefined') {
    const host = window.location.hostname || '127.0.0.1';
    // По умолчанию backend запускается на 8001 (Makefile/README).
    return `http://${host}:8001`;
  }

  return 'http://127.0.0.1:8001';
};

const API_URL = detectBaseUrl();

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
