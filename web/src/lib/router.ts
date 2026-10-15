import { useSyncExternalStore } from 'react'

// Hash routes (#/image/12?x=1): no router library needed for a dozen screens.
export interface Route { path: string[]; query: URLSearchParams }

function read(): Route {
  const [path, query = ''] = window.location.hash.replace(/^#\/?/, '').split('?')
  return { path: path.split('/').filter(Boolean).map(decodeURIComponent), query: new URLSearchParams(query) }
}

let current = read()
const listeners = new Set<() => void>()
window.addEventListener('hashchange', () => {
  current = read()
  listeners.forEach((listener) => listener())
})

export function useRoute(): Route {
  return useSyncExternalStore((listener) => { listeners.add(listener); return () => listeners.delete(listener) }, () => current)
}

export function href(path: string, query?: Record<string, string | number | undefined | null>): string {
  const params = new URLSearchParams()
  Object.entries(query ?? {}).forEach(([key, value]) => { if (value !== undefined && value !== null && value !== '') params.set(key, String(value)) })
  const search = params.toString()
  return `#/${path}${search ? `?${search}` : ''}`
}

export function go(path: string, query?: Record<string, string | number | undefined | null>) {
  window.location.hash = href(path, query)
}
