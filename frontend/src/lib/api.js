import { supabase } from './supabaseClient'

export async function apiFetch(path, options = {}) {
  const { data: { session } } = await supabase.auth.getSession()
  return fetch(`${import.meta.env.VITE_API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token}`,
      ...options.headers,
    },
  })
}
