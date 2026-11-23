import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, tokens } from './api'
import type { Role, User } from './types'

interface RegisterInput {
  email: string
  password: string
  first_name: string
  last_name: string
  phone?: string
  role: Role
}

interface AuthState {
  user: User | null
  loading: boolean
  login(email: string, password: string): Promise<User>
  register(data: RegisterInput): Promise<User>
  logout(): void
  updateMe(data: Partial<User>): Promise<User>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(Boolean(tokens.access))
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!tokens.access) return
    api<User>('/auth/me/')
      .then(setUser)
      .catch(() => tokens.clear())
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const t = await api<{ access: string; refresh: string }>('/auth/token/', {
      body: { email, password },
      auth: false,
    })
    tokens.set(t.access, t.refresh)
    const me = await api<User>('/auth/me/')
    setUser(me)
    queryClient.clear()
    return me
  }, [queryClient])

  const register = useCallback(async (data: RegisterInput) => {
    const res = await api<{ tokens: { access: string; refresh: string } }>('/auth/register/', {
      body: data,
      auth: false,
    })
    tokens.set(res.tokens.access, res.tokens.refresh)
    const me = await api<User>('/auth/me/')
    setUser(me)
    return me
  }, [])

  const logout = useCallback(() => {
    tokens.clear()
    setUser(null)
    queryClient.clear()
  }, [queryClient])

  const updateMe = useCallback(async (data: Partial<User>) => {
    const me = await api<User>('/auth/me/', { method: 'PATCH', body: data })
    setUser(me)
    return me
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout, updateMe }),
    [user, loading, login, register, logout, updateMe],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
