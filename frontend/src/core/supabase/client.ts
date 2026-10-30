import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

/**
 * Global Supabase client instance.
 * Configured via VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY environment variables.
 */
export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
      },
    })
  : null;

if (!isSupabaseConfigured) {
  console.info(
    '[CampusOps Supabase] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not configured. Running in standalone local backend mode.'
  );
}

