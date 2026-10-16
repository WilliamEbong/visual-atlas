// Read-only public demo: answers GET requests from a bundled snapshot.json (built by scripts/build_demo.py from
// the starter library). No AI, no writes; the library list is filtered here in the browser.

interface Item { id: number; title: string; creator: string; provider: string; orientation: string; color_family: string
  favorite: number; techniques: { id: string; state?: string }[] }
interface Snapshot { responses: Record<string, unknown>; library: { items: Item[]; total: number } }

let snapshot: Promise<Snapshot> | null = null

function load(): Promise<Snapshot> {
  snapshot ??= fetch(`${import.meta.env.BASE_URL}snapshot.json`, { credentials: 'omit' }).then((response) => {
    if (!response.ok) throw new Error('The demo library could not be loaded.')
    return response.json() as Promise<Snapshot>
  })
  return snapshot
}

export async function demoRequest<T>(path: string, init?: RequestInit): Promise<T> {
  if (init?.method && init.method !== 'GET') throw new Error('This is a read-only online demo. Download Visual Atlas to find, analyse and save images.')
  const data = await load()
  const key = decodeURIComponent(path)
  if (key in data.responses) return data.responses[key] as T
  const [route, search = ''] = key.split('?')
  if (route === 'graph') {
    const query = new URLSearchParams(search)
    const focus = query.get('focus') ?? ''
    const base = `graph?focus=${focus}`
    const full = data.responses[`${base}&limit=200`] as import('./types').GraphData | undefined
    const graph = full ?? data.responses[base] as import('./types').GraphData | undefined
    if (!graph) throw new Error('This connection is not in the demo.')
    if (!full) return graph as T
    const limit = Math.min(200, Math.max(1, Number(query.get('limit')) || 6))
    const examples = graph.edges.filter((e) => e.kind === 'example').slice(0, limit)
    const ids = new Set(examples.map((e) => e.target))
    return { ...graph, limit, nodes: graph.nodes.filter((n) => n.kind !== 'image' || ids.has(n.id)),
      edges: graph.edges.filter((e) => e.kind !== 'example').concat(examples) } as T
  }
  if (route === 'library') {
    const query = new URLSearchParams(search)
    const q = (query.get('q') ?? '').toLowerCase()
    let items = data.library.items
    if (q) items = items.filter((item) => JSON.stringify(item).toLowerCase().includes(q))
    for (const [param, pick] of [['technique', (i: Item) => i.techniques.map((t) => t.id)], ['orientation', (i: Item) => [i.orientation]],
      ['color', (i: Item) => [i.color_family]], ['provider', (i: Item) => [i.provider]],
      ['state', (i: Item) => i.techniques.map((t) => t.state ?? '')]] as const) {
      const wanted = query.get(param)
      if (wanted) items = items.filter((item) => pick(item).includes(wanted))
    }
    const sort = query.get('sort')
    if (sort === 'title') items = [...items].sort((a, b) => a.title.localeCompare(b.title))
    if (sort === 'maker') items = [...items].sort((a, b) => a.creator.localeCompare(b.creator))
    if (sort === 'oldest') items = [...items].reverse()
    const offset = Number(query.get('offset') ?? 0)
    return { items: items.slice(offset, offset + Number(query.get('limit') ?? 60)), total: items.length } as T
  }
  if (route === 'compare') {  // assembled from the image records already in the snapshot; no written comparison
    const ids = (new URLSearchParams(search).get('ids') ?? '').split(',').filter(Boolean)
    const images = ids.map((id) => data.responses[`images/${id}`]).filter(Boolean)
    if (images.length < 2) throw new Error('These images are not in the online demo.')
    return { images, comparison: null } as T
  }
  if (route === 'settings') return { backend: 'fake', verify_with: 'none', daily_ai_cap: 0, welcomed: true } as T
  if (route.startsWith('jobs') || route === 'backups') return [] as T
  if (route === 'health') return { version: 'demo', home: 'online demo' } as T
  throw new Error('That part of Visual Atlas needs the downloaded app.')
}
