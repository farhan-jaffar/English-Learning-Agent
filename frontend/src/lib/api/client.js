import axios from 'axios';
import { useAuthStore } from '../../stores/authStore';

// Base Axios instance
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  withCredentials: true, // Required for httpOnly refresh cookie
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getMediaUrl = (filePath) => {
  if (!filePath) return '';
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
    return filePath;
  }
  const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api').replace(/\/api\/?$/, '');
  const cleanPath = filePath.trim();
  if (cleanPath.startsWith('/media/')) {
    return `${baseUrl}${cleanPath}`;
  }
  if (cleanPath.startsWith('media/')) {
    return `${baseUrl}/${cleanPath}`;
  }
  if (cleanPath.startsWith('/')) {
    return `${baseUrl}/media${cleanPath}`;
  }
  return `${baseUrl}/media/${cleanPath}`;
};

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Request Interceptor: Attach in-memory access token
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401 and refresh automatically
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Avoid infinite loop if refresh endpoint itself failed or auth endpoints
    const isAuthEndpoint = originalRequest.url?.includes('/auth/login/') ||
      originalRequest.url?.includes('/auth/register/') ||
      originalRequest.url?.includes('/auth/refresh/');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Backend reads httpOnly refresh cookie from /api/auth/refresh/
        const { data } = await apiClient.post('/auth/refresh/');
        const newAccessToken = data.access;

        useAuthStore.getState().setAccessToken(newAccessToken);
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().clearAuth();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
