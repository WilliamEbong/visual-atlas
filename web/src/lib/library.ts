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

/** A picture's width/height, clamped so extreme panoramas or strips still lay out. */
export const aspect = (item: { width: number; height: number }) => Math.min(4, Math.max(0.25, item.width / Math.max(1, item.height) || 1))

/** Add the next page, never repeating an image (new images can shift offsets between pages). */
export function appendPage<T extends { id: number }>(current: T[], page: T[]): T[] {
  const seen = new Set(current.map((item) => item.id))
  return [...current, ...page.filter((item) => !seen.has(item.id))]
}

/** Later pages of one filter set. `consumed` counts rows the server has returned, so the next offset keeps
 * advancing even when a page only repeats images already shown; an empty page means there is nothing more. */
export interface Pages<T> { key: string; items: T[]; consumed: number; done: boolean }

export function nextPages<T extends { id: number }>(previous: Pages<T>, key: string, page: T[]): Pages<T> {
  const base = previous.key === key ? previous : { key, items: [], consumed: 0, done: false }
  return { key, items: appendPage(base.items, page), consumed: base.consumed + page.length, done: page.length === 0 }
}

/** Arrow-key movement in a grid of `count` items laid out in `columns` columns. */
export function nextIndex(index: number, key: string, columns: number, count: number): number {
  const step = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: columns, ArrowUp: -columns, Home: -index, End: count - 1 - index }[key]
  if (step === undefined || count === 0) return index
  return Math.min(count - 1, Math.max(0, index + step))
}

export interface Box { left: number; top: number; width: number }

/** Arrow-key movement in a justified grid, where rows hold different numbers of items: up and down go to the
 *  item in the previous or next row whose centre is nearest horizontally. `boxes` are in reading order. */
export function nextByPosition(boxes: Box[], index: number, key: string): number {
  const count = boxes.length
  if (count === 0 || index < 0) return index
  if (key === 'ArrowRight') return Math.min(count - 1, index + 1)
  if (key === 'ArrowLeft') return Math.max(0, index - 1)
  if (key === 'Home') return 0
  if (key === 'End') return count - 1
  if (key !== 'ArrowUp' && key !== 'ArrowDown') return index
  const rows = [...new Set(boxes.map((box) => Math.round(box.top)))].sort((a, b) => a - b)
  const row = rows.indexOf(Math.round(boxes[index].top)) + (key === 'ArrowDown' ? 1 : -1)
  if (row < 0 || row >= rows.length) return index
  const centre = boxes[index].left + boxes[index].width / 2
  let best = index
  let distance = Infinity
  boxes.forEach((box, candidate) => {
    if (Math.round(box.top) !== rows[row]) return
    const gap = Math.abs(box.left + box.width / 2 - centre)
    if (gap < distance) { distance = gap; best = candidate }
  })
  return best
}

/** The labels of the filters in use, each with the change that removes it. */
export function activeFilters(filters: Filters, names: Record<string, string>): { label: string; clear: Partial<Filters> }[] {
  const out: { label: string; clear: Partial<Filters> }[] = []
  if (filters.q) out.push({ label: `“${filters.q}”`, clear: { q: '' } })
  if (filters.technique) out.push({ label: names[filters.technique] ?? filters.technique, clear: { technique: '' } })
  if (filters.goal) out.push({ label: names[filters.goal] ?? filters.goal, clear: { goal: '' } })
  if (filters.orientation) out.push({ label: filters.orientation[0].toUpperCase() + filters.orientation.slice(1), clear: { orientation: '' } })
  if (filters.provider) out.push({ label: names[filters.provider] ?? filters.provider, clear: { provider: '' } })
  if (filters.license) out.push({ label: filters.license, clear: { license: '' } })
  if (filters.color) out.push({ label: `Mostly ${filters.color}`, clear: { color: '' } })
  if (filters.state) out.push({ label: names[filters.state] ?? filters.state, clear: { state: '' } })
  if (filters.favorite) out.push({ label: 'Favourites', clear: { favorite: false } })
  if (filters.collection) out.push({ label: 'In a collection', clear: { collection: 0 } })
  return out
}
