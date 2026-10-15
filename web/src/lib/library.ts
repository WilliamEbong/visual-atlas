// Library filters live in the URL so Back, reload and sharing a view all work. Pure helpers, unit-tested.

export interface Filters {
  q: string; technique: string; goal: string; provider: string; license: string; orientation: string
  color: string; state: string; favorite: boolean; collection: number; sort: string
}

export const EMPTY: Filters = {
  q: '', technique: '', goal: '', provider: '', license: '', orientation: '', color: '', state: '', favorite: false,
  collection: 0, sort: 'newest',
}

export function fromQuery(query: URLSearchParams): Filters {
  return {
    q: query.get('q') ?? '', technique: query.get('technique') ?? '', goal: query.get('goal') ?? '',
    provider: query.get('provider') ?? '', license: query.get('license') ?? '', orientation: query.get('orientation') ?? '',
    color: query.get('color') ?? '', state: query.get('state') ?? '', favorite: query.get('favorite') === '1',
    collection: Number(query.get('collection') ?? 0) || 0, sort: query.get('sort') ?? 'newest',
  }
}

/** Only non-default values, for both the hash URL and the API query string. */
export function toQuery(filters: Filters): Record<string, string> {
  const out: Record<string, string> = {}
  for (const [key, value] of Object.entries(filters)) {
    const fallback = EMPTY[key as keyof Filters]
    if (value === fallback) continue
    out[key] = typeof value === 'boolean' ? (value ? '1' : '') : String(value)
  }
  return out
}

export function apiPath(filters: Filters, limit = 60, offset = 0): string {
  const query = new URLSearchParams(toQuery(filters))
  if (filters.favorite) query.set('favorite', 'true')
  query.set('limit', String(limit))
  query.set('offset', String(offset))
  return `library?${query.toString()}`
}

export function activeCount(filters: Filters): number {
  return Object.keys(toQuery(filters)).filter((key) => key !== 'sort').length
}

export const PAGE = 60

/** Add the next page, never repeating an image (new images can shift offsets between pages). */
export function appendPage<T extends { id: number }>(current: T[], page: T[]): T[] {
  const seen = new Set(current.map((item) => item.id))
  return [...current, ...page.filter((item) => !seen.has(item.id))]
}

/** Arrow-key movement in a grid of `count` items laid out in `columns` columns. */
export function nextIndex(index: number, key: string, columns: number, count: number): number {
  const step = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: columns, ArrowUp: -columns, Home: -index, End: count - 1 - index }[key]
  if (step === undefined || count === 0) return index
  return Math.min(count - 1, Math.max(0, index + step))
}
