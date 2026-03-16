import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  authApi,
  LoginRequest,
  RegisterRequest,
  UserResponse,
  ApiError,
} from '@/lib/api';

interface AuthState {
  user: UserResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  setLoading: (loading: boolean) => void;
  clearError: () => void;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (data: LoginRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login(data);
          localStorage.setItem('token', response.access_token);
          set({ token: response.access_token, isLoading: false });

          // Fetch user profile after login
          await get().fetchUser();
        } catch (err) {
          const message =
            err instanceof ApiError ? err.message : 'Login failed';
          set({ isLoading: false, error: message });
          throw err;
        }
      },

      register: async (data: RegisterRequest) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.register(data);
          set({ isLoading: false });
        } catch (err) {
          const message =
            err instanceof ApiError ? err.message : 'Registration failed';
          set({ isLoading: false, error: message });
          throw err;
        }
      },

      logout: async () => {
        try {
          await authApi.logout();
        } catch {
          // Even if API call fails, clear local state
        }
        localStorage.removeItem('token');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      fetchUser: async () => {
        const token = get().token ?? localStorage.getItem('token');
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        try {
          const user = await authApi.me();
          set({ user, isAuthenticated: true, token });
        } catch {
          // Token invalid — clear auth
          localStorage.removeItem('token');
          set({ user: null, token: null, isAuthenticated: false });
        }
      },

      setLoading: (loading) => set({ isLoading: loading }),

      clearError: () => set({ error: null }),

      hydrate: async () => {
        const token = localStorage.getItem('token');
        if (token) {
          set({ token });
          await get().fetchUser();
        }
      },
    }),
    {
      name: 'qubot-auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
);
