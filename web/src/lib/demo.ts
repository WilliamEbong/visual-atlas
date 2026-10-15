// Read-only public demo: answers a subset of GET requests from a bundled snapshot.json.
// Built by scripts/build_demo.py from the starter library; no AI, no writes.

type Snapshot = Record<string, unknown> & {
  library: { items: Record<string, unknown>[] }
  images: Record<string, unknown>
  techniques: Record<string, unknown>
  goals: Record<string, unknown>
}

let snapshot: Promise<Snapshot> | null = null

function load(): Promise<Snapshot> {
  snapshot ??= fetch(`${import.meta.env.BASE_URL}snapshot.json`, { credentials: 'omit' }).then((response) => {
    if (!response.ok) throw new Error('The demo library could not be loaded.')
    return response.json() as Promise<Snapshot>
  })
  return snapshot
}

export async function demoRequest<T>(path: string, init?: RequestInit): Promise<T> {
  if (init?.method && init.method !== 'GET') throw new Error('This is a read-only online demo. Download Visual Atlas to find and analyse images.')
  const data = await load()
  const [route, search = ''] = path.split('?')
  const query = new URLSearchParams(search)
  const parts = route.split('/')
  if (route === 'library') {
    let items = data.library.items as (Record<string, unknown> & { techniques: { id: string }[]; title: string; creator: string })[]
    const q = (query.get('q') ?? '').toLowerCase()
    const technique = query.get('technique')
    const orientation = query.get('orientation')
    const color = query.get('color')
    const provider = query.get('provider')
    if (q) items = items.filter((item) => JSON.stringify(item).toLowerCase().includes(q))
    if (technique) items = items.filter((item) => item.techniques.some((t) => t.id === technique))
    if (orientation) items = items.filter((item) => item.orientation === orientation)
    if (color) items = items.filter((item) => item.color_family === color)
    if (provider) items = items.filter((item) => item.provider === provider)
    return { items, total: items.length } as T
  }
  if (parts[0] === 'images' && parts[1]) return (data.images[parts[1]] ?? Promise.reject(new Error('Not in the demo.'))) as T
  if (parts[0] === 'techniques' && parts[1]) return data.techniques[parts[1]] as T
  if (parts[0] === 'goals' && parts[1]) return data.goals[parts[1]] as T
  if (parts[0] === 'jobs' || parts[0] === 'collections' || parts[0] === 'briefs' || parts[0] === 'backups') return [] as T
  if (route === 'settings') return { backend: 'fake', verify_with: 'none', daily_ai_cap: 0, welcomed: true } as T
  if (route in data) return data[route] as T
  throw new Error('That part of Visual Atlas needs the downloaded app.')
}
