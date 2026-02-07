/**
 * Authentication store using Zustand
 *
 * Manages user authentication state with Supabase
 */

import { create } from 'zustand';
import { getSupabaseClient } from '@/lib/supabase';
import type { User, Session, AuthChangeEvent } from '@supabase/supabase-js';

interface AuthState {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  isConfigured: boolean;
  error: string | null;

  // Computed
  isSuperUser: boolean;

  // Actions
  initialize: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signUp: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  signOut: () => Promise<void>;
  clearError: () => void;
}

const SUPER_USER_EMAIL = process.env.NEXT_PUBLIC_SUPER_USER_EMAIL || '';

function checkIsSuperUser(user: User | null): boolean {
  if (!user || !SUPER_USER_EMAIL) return false;
  return user.email?.toLowerCase() === SUPER_USER_EMAIL.toLowerCase();
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  session: null,
  isLoading: true,
  isConfigured: false,
  error: null,
  isSuperUser: false,

  initialize: async () => {
    const supabase = getSupabaseClient();

    if (!supabase) {
      set({ isLoading: false, isConfigured: false });
      return;
    }

    set({ isConfigured: true });

    try {
      // Get initial session
      const { data: { session }, error } = await supabase.auth.getSession();

      if (error) {
        console.error('Error getting session:', error);
        set({ isLoading: false, error: error.message });
        return;
      }

      const currentUser = session?.user ?? null;
      set({
        session,
        user: currentUser,
        isLoading: false,
        isSuperUser: checkIsSuperUser(currentUser),
      });

      // Listen for auth changes
      supabase.auth.onAuthStateChange((_event: AuthChangeEvent, session: Session | null) => {
        const changedUser = session?.user ?? null;
        set({
          session,
          user: changedUser,
          isSuperUser: checkIsSuperUser(changedUser),
        });
      });
    } catch (err) {
      console.error('Auth initialization error:', err);
      set({ isLoading: false });
    }
  },

  signIn: async (email: string, password: string) => {
    const supabase = getSupabaseClient();
    if (!supabase) {
      return { success: false, error: 'Supabase not configured' };
    }

    set({ isLoading: true, error: null });

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        set({ isLoading: false, error: error.message });
        return { success: false, error: error.message };
      }

      set({
        session: data.session,
        user: data.user,
        isLoading: false,
        isSuperUser: checkIsSuperUser(data.user),
      });

      return { success: true };
    } catch (err: any) {
      const message = err.message || 'Sign in failed';
      set({ isLoading: false, error: message });
      return { success: false, error: message };
    }
  },

  signUp: async (email: string, password: string) => {
    const supabase = getSupabaseClient();
    if (!supabase) {
      return { success: false, error: 'Supabase not configured' };
    }

    set({ isLoading: true, error: null });

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      });

      if (error) {
        set({ isLoading: false, error: error.message });
        return { success: false, error: error.message };
      }

      // Note: User might need to confirm email depending on Supabase settings
      set({
        session: data.session,
        user: data.user,
        isLoading: false,
        isSuperUser: checkIsSuperUser(data.user),
      });

      return { success: true };
    } catch (err: any) {
      const message = err.message || 'Sign up failed';
      set({ isLoading: false, error: message });
      return { success: false, error: message };
    }
  },

  signOut: async () => {
    const supabase = getSupabaseClient();
    if (!supabase) return;

    set({ isLoading: true });

    try {
      await supabase.auth.signOut();
      set({ user: null, session: null, isLoading: false, isSuperUser: false });
    } catch (err) {
      console.error('Sign out error:', err);
      set({ isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
