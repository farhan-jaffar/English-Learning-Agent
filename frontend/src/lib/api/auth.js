import { apiClient } from './client';

export const authApi = {
  // Authentication
  register: async (data) => {
    const response = await apiClient.post('/auth/register/', data);
    return response.data; // { access, user }
  },

  login: async (credentials) => {
    const response = await apiClient.post('/auth/login/', credentials);
    return response.data; // { access, user }
  },

  logout: async () => {
    const response = await apiClient.post('/auth/logout/');
    return response.data;
  },

  refreshToken: async () => {
    const response = await apiClient.post('/auth/refresh/');
    return response.data; // { access }
  },

  // User Profile
  getProfile: async () => {
    const response = await apiClient.get('/auth/me/');
    return response.data; // Full User object with nested user_languages
  },

  updateProfile: async (data) => {
    const response = await apiClient.patch('/auth/me/', data);
    return response.data;
  },

  // User Languages
  getUserLanguages: async () => {
    const response = await apiClient.get('/auth/languages/');
    return response.data;
  },

  enrollLanguage: async ({ language, cefr_level, is_primary = false }) => {
    const response = await apiClient.post('/auth/languages/', {
      language,
      cefr_level,
      is_primary,
    });
    return response.data;
  },

  updateUserLanguage: async (id, data) => {
    const response = await apiClient.patch(`/auth/languages/${id}/`, data);
    return response.data;
  },

  setPrimaryLanguage: async (id) => {
    const response = await apiClient.post(`/auth/languages/${id}/set-primary/`);
    return response.data;
  },

  deleteUserLanguage: async (id) => {
    const response = await apiClient.delete(`/auth/languages/${id}/`);
    return response.data;
  },
};
