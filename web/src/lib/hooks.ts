import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { BusyError, request } from './client'
import type { Taxonomy } from './types'

/** Load one API path; reload() refetches. Data from a previous path is never returned for a new one, so a page
 *  can never act on a record it is no longer showing. Errors become plain messages for the page. */
export function useData<T>(path: string | null, deps: unknown[] = []) {
  const [state, setState] = useState<{ path: string | null; data: T | null }>({ path: null, data: null })
  const latest = useRef(path)
  latest.current = path
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [tick, setTick] = useState(0)
  useEffect(() => {
    if (!path) return
    let live = true
    request<T>(path).then((value) => { if (live) { setState({ path, data: value }); setError(null); setBusy(false) } })
      .catch((reason: Error) => { if (live) { setError(reason.message); setBusy(reason instanceof BusyError) } })
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, tick, ...deps])
  const reload = useCallback(() => setTick((value) => value + 1), [])
  const setData = useCallback((value: T | null) => {
    if (latest.current === path) setState({ path, data: value })  // ignore answers for a page already left
  }, [path])
  return { data: state.path === path ? state.data : null, error, busy, reload, setData }
}

/** Poll while a condition holds (job progress). */
export function usePoll(callback: () => void, active: boolean, ms = 1500) {
  useEffect(() => {
    if (!active) return
    const timer = window.setInterval(callback, ms)
    return () => window.clearInterval(timer)
  }, [callback, active, ms])
}

export interface Pick { id: number; title: string; thumb?: string }

export interface AppState {
  taxonomy: Taxonomy | null
  compare: Pick[]
  toggleCompare: (pick: Pick) => void
  clearCompare: () => void
  refreshTaxonomy: () => void
}

export const AppContext = createContext<AppState>({
  taxonomy: null, compare: [], toggleCompare: () => {}, clearCompare: () => {}, refreshTaxonomy: () => {},
})
export const useApp = () => useContext(AppContext)

export function techniqueName(taxonomy: Taxonomy | null, id: string): string {
  return taxonomy?.techniques.find((technique) => technique.id === id)?.name ?? id
}

export function date(value: string | null | undefined): string {
  if (!value) return ''
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}
