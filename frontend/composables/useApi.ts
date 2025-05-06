// Example: composables/useApi.ts
export async function useApi<T = any>(path: string, options?: RequestInit): Promise<T> {
  const config = useRuntimeConfig();
  const baseUrl = config.public.apiBase

  const res = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {})
    }
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}
