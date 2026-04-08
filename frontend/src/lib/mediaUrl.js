const API_URL = (process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001').replace(/\/$/, '');

export function resolveMediaUrl(src) {
  if (!src || typeof src !== 'string') return '';
  const t = src.trim();
  if (!t) return '';
  if (t.startsWith('http://') || t.startsWith('https://')) return t;
  if (t.startsWith('/')) return `${API_URL}${t}`;
  return t;
}
