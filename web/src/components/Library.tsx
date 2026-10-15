import { useEffect, useRef, useState } from 'react'
import { media, post, readOnly, request } from '../lib/client'
import { useApp, useData } from '../lib/hooks'
import { activeCount, apiPath, EMPTY, fromQuery, nextIndex, toQuery, type Filters } from '../lib/library'
import { go, href } from '../lib/router'
import type { LibraryItem, Settings } from '../lib/types'
import { PROVIDERS } from '../lib/types'

const COLORS: [string, string][] = [['red', '#A23B2E'], ['orange', '#C47A3A'], ['yellow', '#C9A646'], ['green', '#4E6A58'],
  ['cyan', '#5F9A99'], ['blue', '#4A6A8C'], ['purple', '#6E5A86'], ['pink', '#C08A97'], ['brown', '#7A5A3C'],
  ['neutral', '#B8B0A0'], ['monochrome', '#55524C']]

export default function Library({ query }: { query: URLSearchParams }) {
  const filters = fromQuery(query)
  const { taxonomy, compare, toggleCompare } = useApp()
  const [limit, setLimit] = useState(60)
  const { data, error } = useData<{ items: LibraryItem[]; total: number; waiting?: number[] }>(apiPath(filters, limit))
  const [queued, setQueued] = useState<string | null>(null)
  async function analyseWaiting(ids: number[]) {
    try {
      const settings = await request<Settings>('settings')
      const job = await post<{ id: string }>('jobs', { kind: 'analyze', spec: { image_ids: ids, backend: settings.backend } })
      setQueued(job.id)
    } catch (reason) { setQueued(null); window.alert((reason as Error).message) }
  }
  const [text, setText] = useState(filters.q)
  const grid = useRef<HTMLDivElement>(null)
  useEffect(() => setText(filters.q), [filters.q])
  const set = (change: Partial<Filters>) => go('', toQuery({ ...filters, ...change }))
  const empty = data && data.total === 0 && activeCount(filters) === 0

  function onGridKey(event: React.KeyboardEvent) {
    const links = Array.from(grid.current?.querySelectorAll<HTMLAnchorElement>('a.plate') ?? [])
    const index = links.indexOf(document.activeElement as HTMLAnchorElement)
    if (index < 0) return
    const columns = getComputedStyle(grid.current!).gridTemplateColumns.split(' ').length
    const next = nextIndex(index, event.key, columns, links.length)
    if (next !== index) { event.preventDefault(); links[next].focus() }
  }

  return (
    <>
      <div className="page-head">
        <h1>A library of ways of looking</h1>
        {data && <span className="mono">{data.total} reference{data.total === 1 ? '' : 's'} · {taxonomy?.techniques.length ?? '…'} techniques</span>}
      </div>
      <p className="lede">Free-to-use images, filed by the visual techniques that make them work. Every image keeps its source, licence and the evidence behind each reading.</p>
      <div className="drawers">
        <a className="drawer" href="#/find"><span className="letter" aria-hidden="true">F</span><strong>Find images</strong>
          <span>Describe what you need; the atlas searches open collections and checks permissions.</span></a>
        <a className="drawer" href="#/explore"><span className="letter" aria-hidden="true">E</span><strong>Explore techniques</strong>
          <span>From a goal like “make one thing stand out” to the techniques and examples behind it.</span></a>
        <a className="drawer" href="#/project"><span className="letter" aria-hidden="true">P</span><strong>Help with my project</strong>
          <span>Describe a project; get directions grounded in images you already have.</span></a>
        <a className="drawer" href="#/collections"><span className="letter" aria-hidden="true">C</span><strong>My collections</strong>
          <span>Boards for projects, with credits ready to export.</span></a>
      </div>
      <hr className="horizon" />

      {empty ? (
        <div className="empty">
          <h2>Your library is empty</h2>
          <p className="muted">Start with <strong>Find images</strong> (describe what you want to see) or let the atlas <strong>grow your library</strong> where technique examples are thinnest. Every image is licence-checked before it is added.</p>
          {!readOnly && <div className="row"><a className="button primary" href="#/find">Find images</a><a className="button" href="#/find?mode=grow">Grow my library</a></div>}
        </div>
      ) : (
        <>
          <form className="filters" role="search" onSubmit={(event) => { event.preventDefault(); set({ q: text.trim() }) }}>
            <label className="field grow">Search the library
              <input type="search" value={text} placeholder="lighthouse, fog, gaze, a technique…" onChange={(event) => setText(event.target.value)} />
            </label>
            <label className="field">Technique
              <select value={filters.technique} onChange={(event) => set({ technique: event.target.value })}>
                <option value="">Any technique</option>
                {taxonomy?.techniques.map((technique) => <option key={technique.id} value={technique.id}>{technique.name}</option>)}
              </select>
            </label>
            <label className="field">Goal
              <select value={filters.goal} onChange={(event) => set({ goal: event.target.value })}>
                <option value="">Any goal</option>
                {taxonomy?.goals.map((goal) => <option key={goal.id} value={goal.id}>{goal.name}</option>)}
              </select>
            </label>
            <label className="field">Shape
              <select value={filters.orientation} onChange={(event) => set({ orientation: event.target.value })}>
                <option value="">Any</option><option value="landscape">Landscape</option><option value="portrait">Portrait</option><option value="square">Square</option>
              </select>
            </label>
            <label className="field">Source
              <select value={filters.provider} onChange={(event) => set({ provider: event.target.value })}>
                <option value="">Any source</option>
                {Object.entries(PROVIDERS).map(([id, name]) => <option key={id} value={id}>{name}</option>)}
              </select>
            </label>
            <label className="field">Review
              <select value={filters.state} onChange={(event) => set({ state: event.target.value })}>
                <option value="">Any state</option><option value="human_reviewed">Confirmed by you</option>
                <option value="model_reviewed">Agreed by a second model</option><option value="proposed">Proposed only</option>
                <option value="rejected">Has a rejected reading</option>
              </select>
            </label>
            <label className="field">Sort
              <select value={filters.sort} onChange={(event) => set({ sort: event.target.value })}>
                <option value="newest">Newest</option><option value="oldest">Oldest</option><option value="title">Title</option>
                <option value="maker">Maker</option><option value="techniques">Most techniques</option>
                <option value="colorful">Most colourful</option><option value="bright">Lightest</option><option value="dark">Darkest</option>
              </select>
            </label>
            <button type="submit">Search</button>
          </form>
          <div className="row" style={{ margin: '14px 0 4px' }}>
            <span className="mono">Colour</span>
            {COLORS.map(([name, hex]) => (
              <button key={name} type="button" className="swatch" title={name} aria-label={`Colour: ${name}`} aria-pressed={filters.color === name}
                style={{ background: hex }} onClick={() => set({ color: filters.color === name ? '' : name })} />
            ))}
            <label className="choice"><input type="checkbox" checked={filters.favorite} onChange={(event) => set({ favorite: event.target.checked })} /> Favourites</label>
            {activeCount(filters) > 0 && <button type="button" className="quiet" onClick={() => go('', toQuery({ ...EMPTY, sort: filters.sort }))}>Clear filters</button>}
            <span className="mono" style={{ marginLeft: 'auto' }} aria-live="polite">{data ? `Showing ${data.items.length} of ${data.total}` : 'Loading…'}</span>
          </div>
          {error && <p className="notice error" role="alert">{error}</p>}
          {!readOnly && !!data?.waiting?.length && <p className="notice" role="status">
            {data.waiting.length} downloaded image{data.waiting.length === 1 ? ' is' : 's are'} waiting for analysis (a job stopped at its budget or was interrupted).{' '}
            {queued ? <a href={href(`jobs/${queued}`)}>Analysis started — see progress</a>
              : <button type="button" onClick={() => analyseWaiting(data.waiting!)}>Analyse them now</button>}</p>}
          {data && data.total === 0 && <div className="empty"><p>No images match these filters.</p>
            {!readOnly && <a className="button" href={href('find', { goal: filters.q, technique: filters.technique })}>Find new images like this</a>}</div>}
          <div className="plates" ref={grid} onKeyDown={onGridKey}>
            {data?.items.map((item) => (
              <div key={item.id} style={{ position: 'relative' }}>
                <a className="plate" href={href(`image/${item.id}`)}>
                  <div className="frame"><img src={media(item.thumb)} alt={`${item.title}${item.creator ? `, ${item.creator}` : ''}`} loading="lazy" /></div>
                  <span className="mono">Fig. {item.id} · {item.license_label}</span>
                  <span className="title">{item.title}</span>
                  <span className="maker">{[item.creator, item.date_text].filter(Boolean).join(', ') || 'Unknown maker'}</span>
                  <span className="techs">{item.techniques.slice(0, 3).map((t) => t.name).join(' · ') || (item.status === 'pending' ? 'Waiting for analysis' : 'No technique yet')}</span>
                  <span className="palette" aria-hidden="true">{item.palette.map((hex) => <span key={hex} style={{ background: hex }} />)}</span>
                </a>
                <button type="button" className="pick" aria-pressed={compare.some((p) => p.id === item.id)}
                  onClick={() => toggleCompare({ id: item.id, title: item.title, thumb: item.thumb })}>
                  {compare.some((p) => p.id === item.id) ? '✓ Comparing' : '+ Compare'}
                </button>
              </div>
            ))}
          </div>
          {data && data.items.length < data.total && <p style={{ marginTop: 24 }}><button type="button" onClick={() => setLimit(limit + 60)}>Show more</button></p>}
        </>
      )}
    </>
  )
}
