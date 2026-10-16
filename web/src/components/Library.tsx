import { useEffect, useRef, useState } from 'react'
import { media, post, readOnly, request } from '../lib/client'
import { useApp, useData } from '../lib/hooks'
import { activeCount, activeFilters, apiPath, appendPage, aspect, EMPTY, fromQuery, nextByPosition, nextPages, PAGE, toQuery, type Filters, type Pages } from '../lib/library'
import { go, href } from '../lib/router'
import type { LibraryItem, Settings } from '../lib/types'
import { PROVIDERS } from '../lib/types'
import { Empty, Failure, Loading, PageHead, useNotice } from './ui'

const COLORS: [string, string][] = [['red', '#A23B2E'], ['orange', '#C47A3A'], ['yellow', '#C9A646'], ['green', '#4E6A58'],
  ['cyan', '#5F9A99'], ['blue', '#4A6A8C'], ['purple', '#6E5A86'], ['pink', '#C08A97'], ['brown', '#7A5A3C'],
  ['neutral', '#B8B0A0'], ['monochrome', '#55524C']]
const STATES: Record<string, string> = { human_reviewed: 'Confirmed by you', model_reviewed: 'Agreed by a second model',
  proposed: 'Proposed only', rejected: 'Has a rejected reading' }
const HERO = [150, 182, 206, 168, 132]

interface LibraryPage { items: LibraryItem[]; total: number; waiting?: number[] }

function plateState(item: LibraryItem): string {
  const states = item.techniques.map((t) => t.state)
  if (states.includes('human_reviewed')) return 'Confirmed by you'
  if (states.includes('model_reviewed')) return 'Agreed by a second model'
  if (states.length) return 'Proposed'
  return item.status === 'pending' ? 'Waiting for analysis' : ''
}

export default function Library({ query }: { query: URLSearchParams }) {
  const filters = fromQuery(query)
  const from = query.get('from')?.startsWith('#/connections?') ? query.get('from') : null
  const { taxonomy, compare, toggleCompare } = useApp()
  const { fail } = useNotice()
  const first = apiPath(filters, PAGE, 0)
  const { data, error, busy, reload } = useData<LibraryPage>(first)
  // Later pages are fetched with an offset and kept per filter set; an answer for filters already left is ignored.
  const [more, setMore] = useState<Pages<LibraryItem>>({ key: '', items: [], consumed: 0, done: false })
  const [loadingMore, setLoadingMore] = useState(false)
  const current = useRef(first)
  current.current = first
  const mine = more.key === first ? more : { key: first, items: [], consumed: 0, done: false }
  const items = appendPage(data?.items ?? [], mine.items)
  async function showMore() {
    const requested = first
    setLoadingMore(true)
    try {
      const page = await request<LibraryPage>(apiPath(filters, PAGE, (data?.items.length ?? 0) + mine.consumed))
      if (current.current !== requested) return
      setMore((previous) => nextPages(previous, requested, page.items))
    } catch (reason) { fail(reason) } finally { setLoadingMore(false) }
  }
  // The image page moves to the previous and next result of this list.
  useEffect(() => {
    if (!data) return
    try { sessionStorage.setItem('trail', JSON.stringify({ query: query.toString(), ids: items.map((item) => item.id) })) } catch { /* private mode */ }
  }, [data, items.length]) // eslint-disable-line react-hooks/exhaustive-deps
  const [queued, setQueued] = useState<string | null>(null)
  async function analyseWaiting(ids: number[]) {
    try {
      const settings = await request<Settings>('settings')
      const job = await post<{ id: string }>('jobs', { kind: 'analyze', spec: { image_ids: ids, backend: settings.backend } })
      setQueued(job.id)
    } catch (reason) { setQueued(null); fail(reason) }
  }
  const [text, setText] = useState(filters.q)
  const [panel, setPanel] = useState(false)
  const grid = useRef<HTMLDivElement>(null)
  useEffect(() => setText(filters.q), [filters.q])
  const set = (change: Partial<Filters>) => go('', { ...toQuery({ ...filters, ...change }), from })
  const empty = data && data.total === 0 && activeCount(filters) === 0
  const names: Record<string, string> = { ...PROVIDERS, ...STATES,
    ...Object.fromEntries([...(taxonomy?.techniques ?? []), ...(taxonomy?.goals ?? [])].map((x) => [x.id, x.name])) }
  const active = activeFilters(filters, names)
  const extra = ['orientation', 'provider', 'state', 'color', 'favorite', 'license'].filter((key) => toQuery(filters)[key]).length

  function onGridKey(event: React.KeyboardEvent) {
    const links = Array.from(grid.current?.querySelectorAll<HTMLAnchorElement>('a.plate') ?? [])
    const index = links.indexOf(document.activeElement as HTMLAnchorElement)
    if (index < 0) return
    const boxes = links.map((link) => link.getBoundingClientRect())
    const next = nextByPosition(boxes, index, event.key)
    if (next !== index) { event.preventDefault(); links[next].focus() }
  }

  // Specimens on the horizon: five pictures spread through the first page, so they do not repeat the first row.
  const pool = (data?.items ?? []).filter((item) => item.thumb)
  const hero = pool.length > 10 ? [5, 15, 25, 35, 45].map((i) => pool[Math.min(i, pool.length - 1)]).filter((item, i, all) => all.indexOf(item) === i) : pool.slice(0, 5)
  return (
    <>
      <PageHead kicker={<>Library · {data ? `${data.total} reference${data.total === 1 ? '' : 's'}` : '…'} · {taxonomy?.techniques.length ?? '…'} techniques</>}
        title="A library of ways of looking"
        aside={hero.length > 0 && <div className="specimens" aria-hidden="true">
          {hero.map((item, index) => <span key={item.id} className="specimen" style={{ height: HERO[index], aspectRatio: aspect(item) }}>
            <img src={media(item.thumb)} alt="" /></span>)}</div>} />
      <div className="under row" style={{ justifyContent: 'space-between', alignItems: 'baseline' }}>
        <p className="lede">Free-to-use pictures from open museum and archive collections, filed by the visual techniques that make them work. Every image keeps its source, its licence and the evidence behind each reading.</p>
        {hero.length > 0 && <p className="mono">Fig. 1–{hero.length}  From your library: {hero.slice(0, 3).map((item) => (item.creator || item.title)
          .replace(/^Print made by:\s*/i, '').split(/[,;(]| Published| from /)[0].trim().slice(0, 32)).join(' · ')}</p>}
      </div>
      <nav className="drawers" aria-label="Ways in">
        <a className="drawer" href="#/find"><span className="letter" aria-hidden="true">F</span><span><strong>Find images</strong>
          <span className="text">Describe what you need; the atlas searches open collections and checks permissions.</span></span></a>
        <a className="drawer" href="#/explore"><span className="letter" aria-hidden="true">E</span><span><strong>Explore techniques</strong>
          <span className="text">From a goal like “make one thing stand out” to the techniques behind it.</span></span></a>
        <a className="drawer" href="#/project"><span className="letter" aria-hidden="true">P</span><span><strong>Help with a project</strong>
          <span className="text">Paste a brief and get directions grounded in your library.</span></span></a>
        <a className="drawer" href="#/collections"><span className="letter" aria-hidden="true">C</span><span><strong>Collections</strong>
          <span className="text">Boards for projects, with credits ready to export.</span></span></a>
      </nav>

      {error ? <Failure message={error} busy={busy} retry={reload} />
        : !data ? <Loading label="Loading the library…" />
        : empty ? (
        <Empty title="Your library is empty" actions={!readOnly && <><a className="button primary" href="#/find">Find images</a>
          <a className="button" href="#/find?mode=grow">Grow my library</a></>}>
          Start with Find images, or let the atlas grow your library where technique examples are thinnest. Every image is licence-checked before it is added.
        </Empty>
      ) : (
        <section className="section" aria-labelledby="browse" style={{ marginTop: 56 }}>
          <h2 id="browse" className="sr-only">Browse the library</h2>
          <form className="filters" role="search" onSubmit={(event) => { event.preventDefault(); set({ q: text.trim() }) }}>
            <label className="field grow">Search titles, makers, evidence and techniques
              <span className="search-box">
                <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><circle cx="11" cy="11" r="6.5" /><path d="M16 16l5 5" /></svg>
                <input type="search" value={text} placeholder="lighthouse, fog, gaze, a technique…" onChange={(event) => setText(event.target.value)} />
              </span>
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
            <label className="field">Sort
              <select value={filters.sort} onChange={(event) => set({ sort: event.target.value })}>
                <option value="newest">Newest</option><option value="oldest">Oldest</option><option value="title">Title</option>
                <option value="maker">Maker</option><option value="techniques">Most techniques</option>
                <option value="colorful">Most colourful</option><option value="bright">Lightest</option><option value="dark">Darkest</option>
              </select>
            </label>
            <button type="button" aria-expanded={panel} aria-controls="more-filters" onClick={() => setPanel(!panel)}>
              <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M4 6h16M7 12h10M10 18h4" /></svg>
              More filters{extra ? <span className="mono" style={{ color: 'inherit' }}>{extra}</span> : null}</button>
            <button type="submit" className="sr-only">Search</button>
          </form>
          {panel && <div className="panel" id="more-filters">
            <div className="filters">
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
                  <option value="">Any state</option>
                  {Object.entries(STATES).map(([id, name]) => <option key={id} value={id}>{name}</option>)}
                </select>
              </label>
            </div>
            <fieldset><legend>Main colour</legend>
              <div className="row">
                {COLORS.map(([name, hex]) => (
                  <button key={name} type="button" className="swatch" title={name} aria-label={`Colour: ${name}`} aria-pressed={filters.color === name}
                    style={{ background: hex }} onClick={() => set({ color: filters.color === name ? '' : name })} />
                ))}
                <label className="choice plain" style={{ marginLeft: 12 }}><input type="checkbox" checked={filters.favorite} onChange={(event) => set({ favorite: event.target.checked })} /> Favourites only</label>
              </div>
            </fieldset>
          </div>}
          <div className="active-filters">
            {active.length > 0 && <span className="mono">Filtered by</span>}
            {active.map((filter) => <button key={filter.label} type="button" aria-label={`Remove filter: ${filter.label}`} onClick={() => set(filter.clear)}>{filter.label} ×</button>)}
            {active.length > 0 && <button type="button" className="clear" onClick={() => go('', { ...toQuery({ ...EMPTY, sort: filters.sort }), from })}>Clear all</button>}
            <span className="mono" style={{ marginLeft: 'auto' }} aria-live="polite">Showing {items.length} of {data.total}</span>
          </div>
          {!readOnly && !!data.waiting?.length && <p className="notice" role="status" style={{ marginTop: 16 }}>
            {data.waiting.length} downloaded image{data.waiting.length === 1 ? ' is' : 's are'} waiting for analysis (a job stopped at its budget or was interrupted).{' '}
            {queued ? <a href={href(`jobs/${queued}`)}>Analysis started — see progress</a>
              : <button type="button" className="small" onClick={() => analyseWaiting(data.waiting!)}>Analyse them now</button>}</p>}
          {data.total === 0 ? <Empty title="Nothing matches these filters" actions={<>
              <button type="button" onClick={() => go('', { ...toQuery({ ...EMPTY, sort: filters.sort }), from })}>Clear filters</button>
              {!readOnly && <a className="button" href={href('find', { goal: filters.q, technique: filters.technique })}>Find new images like this</a>}</>}>
              {active.length} filter{active.length === 1 ? ' is' : 's are'} on.
            </Empty>
            : <div className="justified" ref={grid} onKeyDown={onGridKey}>
              {items.map((item) => {
                const picked = compare.some((p) => p.id === item.id)
                return (
                  <article key={item.id} className="plate-item" style={{ '--a': aspect(item) } as React.CSSProperties}>
                    <a className="plate" href={href(`image/${item.id}`, { from })}>
                      <span className="plate-frame"><img src={media(item.thumb)} alt={`${item.title}${item.creator ? `, ${item.creator}` : ''}`} loading="lazy" decoding="async" /></span>
                      <span className="fig">Fig. {item.id}{plateState(item) ? `  ${plateState(item)}` : ''}</span>
                      <span className="plate-title">{item.title}</span>
                      <span className="maker">{[item.creator, item.date_text].filter(Boolean).join(', ') || 'Unknown maker'}</span>
                      <span className="techs">{item.techniques.slice(0, 3).map((t) => t.name.replace(/ \(.*\)$/, '')).join(' · ') || (item.status === 'pending' ? 'Waiting for analysis' : 'No technique yet')}</span>
                    </a>
                    <button type="button" className="pick" aria-pressed={picked} aria-label={`${picked ? 'Remove from' : 'Add to'} comparison: ${item.title}`}
                      onClick={() => toggleCompare({ id: item.id, title: item.title, thumb: item.thumb })}>{picked ? '✓ Comparing' : '+ Compare'}</button>
                  </article>
                )
              })}
            </div>}
          {items.length < data.total && !mine.done && <div className="row" style={{ justifyContent: 'center', margin: '56px 0 0', gap: 20 }}>
            <button type="button" disabled={loadingMore} onClick={showMore}>{loadingMore ? 'Loading…' : `Show the next ${Math.min(PAGE, data.total - items.length)}`}</button>
            <span className="mono">Showing {items.length} of {data.total}</span></div>}
        </section>
      )}
    </>
  )
}
