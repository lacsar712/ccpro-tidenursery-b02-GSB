import { useEffect, useState } from 'react'
import { api, getToken } from './client'

export type CurrentUser = {
  id: number
  username: string
  role: string
  display_name: string
}

let cache: CurrentUser | null = null
let inflight: Promise<CurrentUser> | null = null

export function setCachedUser(user: CurrentUser) {
  cache = user
}

export function clearCachedUser() {
  cache = null
  inflight = null
}

export function refreshCurrentUser(): Promise<CurrentUser> {
  inflight = api<CurrentUser>('/api/auth/me').then((u) => {
    cache = u
    return u
  })
  return inflight
}

export function useCurrentUser(): CurrentUser | null {
  const [user, setUser] = useState<CurrentUser | null>(cache)

  useEffect(() => {
    if (cache) {
      setUser(cache)
      return
    }
    if (!getToken()) return
    let alive = true
    ;(inflight ?? refreshCurrentUser()).then((u) => {
      if (alive) setUser(u)
    })
    return () => {
      alive = false
    }
  }, [])

  return user
}
