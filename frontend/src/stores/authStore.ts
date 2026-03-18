import { create } from 'zustand';
import { login as apiLogin, register as apiRegister } from '../services/api';

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: !!localStorage.getItem('access_token'),
  token: localStorage.getItem('access_token'),

  login: async (email, password) => {
    const res = await apiLogin(email, password);
    localStorage.setItem('access_token', res.data.access_token);
    localStorage.setItem('refresh_token', res.data.refresh_token);
    set({ isAuthenticated: true, token: res.data.access_token });
  },

  register: async (email, username, password) => {
    await apiRegister({ email, username, password });
  },

  logout: () => {
    localStorage.clear();
    set({ isAuthenticated: false, token: null });
  },

  checkAuth: () => {
    const token = localStorage.getItem('access_token');
    set({ isAuthenticated: !!token, token });
  },
}));
