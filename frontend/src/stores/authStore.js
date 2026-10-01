import { create } from 'zustand';
import { authApi } from '../lib/api/auth';

export const useAuthStore = create((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true,
  activeLanguage: null,

  setAuth: (payload) => {
    const user = payload?.user;
    const token = payload?.accessToken || payload?.access;
    const primaryLang =
      user?.user_languages?.find((l) => l.is_primary) ||
      user?.user_languages?.[0] ||
      null;

    set({
      user,
      accessToken: token,
      isAuthenticated: Boolean(token && user),
      activeLanguage: primaryLang,
      isLoading: false,
    });
  },

  setAccessToken: (accessToken) => {
    set({
      accessToken,
      isAuthenticated: !!accessToken,
    });
  },

  setUser: (user) => {
    const primaryLang =
      user?.user_languages?.find((l) => l.is_primary) ||
      user?.user_languages?.[0] ||
      get().activeLanguage;

    set({
      user,
      activeLanguage: primaryLang,
    });
  },

  setActiveLanguage: (activeLanguage) => {
    set({ activeLanguage });
  },

  clearAuth: () => {
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      activeLanguage: null,
      isLoading: false,
    });
  },

  // Silent session restore on app mount via httpOnly refresh cookie
  initializeAuth: async () => {
    try {
      set({ isLoading: true });
      const { access } = await authApi.refreshToken();
      set({ accessToken: access });

      // Fetch user profile with enrolled languages
      const userProfile = await authApi.getProfile();
      const primaryLang =
        userProfile?.user_languages?.find((l) => l.is_primary) ||
        userProfile?.user_languages?.[0] ||
        null;

      set({
        user: userProfile,
        isAuthenticated: true,
        activeLanguage: primaryLang,
        isLoading: false,
      });
    } catch {
      // Refresh failed or no cookie exists - clean state
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        activeLanguage: null,
        isLoading: false,
      });
    }
  },

  // Switch primary language and refresh profile state
  switchPrimaryLanguage: async (userLanguageId) => {
    await authApi.setPrimaryLanguage(userLanguageId);
    const updatedUser = await authApi.getProfile();
    const newPrimary = updatedUser?.user_languages?.find((l) => l.is_primary);

    set({
      user: updatedUser,
      activeLanguage: newPrimary,
    });
  },

  refreshUserProfile: async () => {
    try {
      const updatedUser = await authApi.getProfile();
      const currentActiveId = get().activeLanguage?.id;
      const matchingActive = updatedUser?.user_languages?.find((l) => l.id === currentActiveId);
      const primaryLang =
        updatedUser?.user_languages?.find((l) => l.is_primary) ||
        updatedUser?.user_languages?.[0];

      set({
        user: updatedUser,
        activeLanguage: matchingActive || primaryLang || null,
      });
      return updatedUser;
    } catch (e) {
      console.warn('Failed to refresh user profile:', e);
    }
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch (e) {
      console.error('Logout error on backend:', e);
    } finally {
      get().clearAuth();
    }
  },
}));
