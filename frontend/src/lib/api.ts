/**
 * Tiny fetch wrapper for the Django API.
 * - adds the JWT access token
 * - refreshes it once on 401 and retries
 * - turns DRF error bodies into ApiError with field messages
 */
const BASE = import.meta.env.VITE_API_URL ?? '/api'
const ACCESS = 'yy.access'
const REFRESH = 'yy.refresh'

export const tokens = {
  get access() { return localStorage.getItem(ACCESS) },
  get refresh() { return localStorage.getItem(REFRESH) },
  set(access: string, refresh?: string) {
    localStorage.setItem(ACCESS, access)
    if (refresh) localStorage.setItem(REFRESH, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS)
    localStorage.removeItem(REFRESH)
  },
}

export class ApiError extends Error {
  status: number
  fields: Record<string, string>
  constructor(status: number, body: unknown) {
    const fields: Record<string, string> = {}
    let message = 'Something went wrong. Please try again.'
    if (body && typeof body === 'object') {
      for (const [k, v] of Object.entries(body as Record<string, unknown>)) {
        const text = Array.isArray(v) ? String(v[0]) : typeof v === 'string' ? v : JSON.stringify(v)
        fields[k] = text
      }
      message = fields.detail ?? fields.non_field_errors ?? Object.values(fields)[0] ?? message
    }
    super(message)
    this.status = status
    this.fields = fields
  }
}

let refreshing: Promise<boolean> | null = null

async function refreshAccess(): Promise<boolean> {
  const refresh = tokens.refresh
  if (!refresh) return false
  // share one in-flight refresh between parallel requests
  refreshing ??= fetch(`${BASE}/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
    .then(async (r) => {
      if (!r.ok) { tokens.clear(); return false }
      const data = await r.json()
      tokens.set(data.access, data.refresh)
      return true
    })
    .finally(() => { refreshing = null })
  return refreshing
}

type Query = Record<string, string | number | boolean | undefined | null>

export function qs(params: Query = {}) {
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') sp.set(k, String(v))
  }
  const s = sp.toString()
  return s ? `?${s}` : ''
}

export async function api<T = unknown>(
  path: string,
  opts: { method?: string; body?: unknown; query?: Query; auth?: boolean } = {},
  retry = true,
): Promise<T> {
  const headers: Record<string, string> = {}
  const isForm = opts.body instanceof FormData
  if (opts.body !== undefined && !isForm) headers['Content-Type'] = 'application/json'
  if (opts.auth !== false && tokens.access) headers.Authorization = `Bearer ${tokens.access}`

  const res = await fetch(`${BASE}${path}${qs(opts.query)}`, {
    method: opts.method ?? (opts.body !== undefined ? 'POST' : 'GET'),
    headers,
    body: isForm ? (opts.body as FormData) : opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  })

  if (res.status === 401 && retry && tokens.refresh && (await refreshAccess())) {
    return api<T>(path, opts, false)
  }
  if (res.status === 204) return undefined as T
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, data)
  return data as T
}
