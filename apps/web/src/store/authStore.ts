import { create } from "zustand";
import type { AuthUser } from "@isl/shared";

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: AuthUser) => void;
  logout: () => void;
}

const STORAGE_KEY = "isl_auth";

function loadInitial(): { token: string | null; user: AuthUser | null } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { token: null, user: null };
    return JSON.parse(raw);
  } catch {
    return { token: null, user: null };
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  ...loadInitial(),
  isAuthenticated: !!loadInitial().token,
  setAuth: (token, user) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token, user }));
    set({ token, user, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem(STORAGE_KEY);
    set({ token: null, user: null, isAuthenticated: false });
  },
}));
