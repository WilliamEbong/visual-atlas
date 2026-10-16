import { useEffect, useRef, useState } from 'react'
import { media } from '../lib/client'
import { adjacency, layout, route } from '../lib/graph'
import { useApp, useData } from '../lib/hooks'
import { go, href, useRoute } from '../lib/router'
import { STATE_LABEL, type GraphData } from '../lib/types'
import { Failure, Loading, PageHead } from './ui'

const KIND: Record<string, string> = { goal: 'Goal', operation: 'Operation', domain: 'Domain', technique: 'Technique', image: 'Example' }
const RELATION: Record<string, string> = { serves: 'Can serve a goal', operation: 'Uses an operation', domain: 'Works in a domain', related: 'Related technique', example: 'Recorded reading' }

export default function Connections({ focus }: { focus: string }) {
  const { taxonomy, compare, toggleCompare } = useApp()
  const { query } = useRoute()
  const start = focus || 'goal:draw-attention'
  const view = query.get('view') ?? (window.matchMedia?.('(max-width: 640px)').matches ? 'list' : 'map')
  const limit = Math.min(200, Math.max(6, Number(query.get('limit')) || 6))
  const trail = (query.get('trail') ?? '').split('|').filter(Boolean).slice(-8)
  const context = href('connections', { focus: start, view, limit, trail: trail.join('|') })
  const { data, error, busy, reload } = useData<GraphData>(`graph?focus=${encodeURIComponent(start)}&limit=${limit}`)
  const [selected, setSelected] = useState<GraphData['edges'][number] | null>(null)
  const box = useRef<HTMLDivElement>(null)
  const cy = useRef<import('cytoscape').Core | null>(null)
  const navigate = (id: string) => href('connections', { focus: id, view, trail: [...trail, start].slice(-8).join('|') })
  const open = (id: string) => `${route(id)}${route(id).includes('?') ? '&' : '?'}from=${encodeURIComponent(context)}`
  const label = (id: string) => {
    const [kind, key] = id.split(':')
    const entries = kind === 'goal' ? taxonomy?.goals : kind === 'operation' ? taxonomy?.operations : kind === 'domain' ? taxonomy?.domains : taxonomy?.techniques
    return entries?.find((x) => x.id === key)?.name ?? data?.nodes.find((n) => n.id === id)?.label ?? id
  }
  const points = data ? layout(data) : []
  const height = Math.max(460, ...points.map((p) => p.y + 100))
  useEffect(() => {
    setSelected(null)
    if (!data || view !== 'map' || !box.current) return
    let cancelled = false
    import('cytoscape').then(({ default: cytoscape }) => {
      if (cancelled || !box.current) return
      const css = getComputedStyle(document.documentElement)
      const ink = css.getPropertyValue('--ink').trim(), paper = css.getPropertyValue('--paper').trim()
      const nodes = layout(data).map((node) => ({ data: { id: node.id, label: `${KIND[node.kind]}\n${node.label}`, thumb: media(node.thumb) ?? '' },
        position: { x: node.x, y: node.y }, classes: `${node.kind}${node.id === data.focus ? ' focus' : ''}` }))
      const edges = data.edges.map((edge, index) => ({ data: { id: `e${index}`, source: edge.source, target: edge.target, index },
        classes: `${edge.kind} ${edge.state ?? ''} ${edge.role ?? ''}` }))
      cy.current = cytoscape({ container: box.current, elements: [...nodes, ...edges], layout: { name: 'preset', fit: false },
        zoom: 1, pan: { x: 0, y: 0 }, minZoom: 0.5, maxZoom: 2, autoungrabify: true, userZoomingEnabled: false,
        style: [
          { selector: 'node', style: { label: 'data(label)', 'font-family': 'Libre Franklin Variable, sans-serif', 'font-size': 13, color: ink,
            'text-wrap': 'wrap', 'text-max-width': '190px', 'text-valign': 'bottom', 'text-margin-y': 8, 'text-background-color': paper,
            'text-background-opacity': 0.92, 'text-background-padding': '3px', width: 22, height: 22, 'background-color': '#8B867B' } },
          { selector: 'node.goal', style: { shape: 'rectangle', 'background-color': '#A2573B' } },
          { selector: 'node.operation', style: { shape: 'diamond', 'background-color': '#236292' } },
          { selector: 'node.domain', style: { shape: 'hexagon', 'background-color': '#647B61' } },
          { selector: 'node.technique', style: { shape: 'ellipse', 'background-color': '#236292' } },
          { selector: 'node.image', style: { shape: 'rectangle', width: 90, height: 70, 'background-image': 'data(thumb)', 'background-fit': 'contain' } },
          { selector: 'node.focus', style: { 'border-width': 3, 'border-color': ink, 'font-weight': 'bold' } },
          { selector: 'edge', style: { width: 1.5, 'line-color': '#8B867B', opacity: 0.65, 'curve-style': 'bezier' } },
          { selector: 'edge.operation', style: { 'line-color': '#236292', 'line-style': 'dashed' } },
          { selector: 'edge.domain', style: { 'line-color': '#647B61', 'line-style': 'dotted' } },
          { selector: 'edge.related', style: { 'line-style': 'dashed', 'target-arrow-shape': 'triangle', 'target-arrow-color': '#8B867B' } },
          { selector: 'edge.primary', style: { width: 3 } },
          { selector: 'edge.proposed', style: { 'line-style': 'dotted' } },
        ],
      })
      cy.current.on('tap', 'node', (event) => { window.location.hash = navigate(event.target.id()) })
      cy.current.on('tap', 'edge', (event) => setSelected(data.edges[event.target.data('index')]))
    })
    return () => { cancelled = true; cy.current?.destroy(); cy.current = null }
    // Navigation context is encoded in the URL and refreshes with the focus/view/limit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, view, context])
  const focusNode = data?.nodes.find((node) => node.id === data.focus)
  const techniques = taxonomy?.techniques.filter((t) => Object.hasOwn(data?.example_counts ?? {}, t.id)) ?? []
  const examples = data?.nodes.filter((n) => n.kind === 'image') ?? []
  return <div className="connections stack">
    <PageHead kicker={<><a href="#/explore">Explore</a> / connections</>} title="Follow a visual idea" asideClass="actions"
      aside={<div className="segments" role="group" aria-label="View">{['map', 'list'].map((v) => <button key={v} type="button" aria-pressed={view === v}
        className={view === v ? 'primary' : ''} onClick={() => go('connections', { focus: start, view: v, limit, trail: trail.join('|') })}>{v === 'map' ? 'Map' : 'List'}</button>)}</div>} />
    <nav className="reasoning-trail mono" aria-label="Exploration trail"><a href="#/explore">Explore</a>{trail.map((id, i) =>
      <span key={`${id}-${i}`}> → <a href={href('connections', { focus: id, view, trail: trail.slice(0, i).join('|') })}>{label(id)}</a></span>)}
      <span> → {focusNode?.label ?? label(start)}</span></nav>
    <div className="connection-controls">
      <label className="field">Start or focus on<select value={start} onChange={(e) => go('connections', { focus: e.target.value, view })}>
        {([['Goals', 'goal', taxonomy?.goals], ['Operations', 'operation', taxonomy?.operations], ['Domains', 'domain', taxonomy?.domains], ['Techniques', 'technique', taxonomy?.techniques]] as const).map(([name, kind, entries]) =>
          <optgroup key={kind} label={name}>{entries?.map((item) => <option key={item.id} value={`${kind}:${item.id}`}>{item.name}</option>)}</optgroup>)}
        {start.startsWith('image:') && <option value={start}>{focusNode?.label ?? 'This image'}</option>}
      </select></label>
      <p className="muted">Goals describe the effect. Operations describe what changes; domains describe what it changes in. A technique can belong to several of each.</p>
    </div>
    {error ? <Failure message={error} busy={busy} retry={reload} /> : !data ? <Loading plates={false} /> : <>
      <div className="connection-workbench"><section className="reasoning-context" aria-label="Reasoning context">
        <div><p className="mono">{KIND[focusNode!.kind]}</p><h2>{focusNode!.label}</h2>
          <p>{focusNode?.description ?? taxonomy?.techniques.find((t) => `technique:${t.id}` === start)?.definition}</p>
          {['technique', 'image', 'goal'].includes(focusNode!.kind) && <a href={open(start)}>Open {focusNode!.kind === 'image' ? 'image and evidence' : 'full explanation'}</a>}</div>
        <div className="stack"><p className="mono">{start.startsWith('technique:') ? 'Recorded memberships' : 'Explore through the techniques shown here'}</p>
          {(['operation', 'domain'] as const).map((kind) => <div key={kind}><strong>{kind === 'operation' ? 'Operations' : 'Domains'} </strong>
            <span className="row">{(kind === 'operation' ? taxonomy?.operations : taxonomy?.domains)?.filter((entry) => techniques.some((t) => t[kind === 'operation' ? 'operations' : 'domains'].includes(entry.id))).map((entry) =>
              <a key={entry.id} href={navigate(`${kind}:${entry.id}`)} title={entry.description}>{entry.name}</a>)}</span></div>)}
          <p className="mono">These are shared technique memberships, not a single-parent hierarchy. Select a technique to see its own path and examples.</p></div>
      </section>
      <div className="stack">{view === 'map' ? <>
        <div className="row graph-legend"><span>Solid: goal / recorded reading</span><span>– – operation</span><span>··· domain / proposed reading</span><span>→ related technique</span><span>Thick: main technique in this reading</span></div>
        <p className="mono">Select a node to explore; select a line for its explanation. Scroll the canvas to see more. Every connection is also in the List view.</p>
        {selected && <p className="slip" role="status"><strong>{RELATION[selected.kind]}: </strong>{selected.explanation}
          {selected.evidence?.length ? <> Visible evidence: {selected.evidence.join(' ')}</> : null}
          {selected.state && <> · {selected.role === 'primary' ? 'Main technique in this reading' : 'Supporting technique in this reading'} · {STATE_LABEL[selected.state]}</>}</p>}
        <div className="graph-scroll" tabIndex={0} role="region" aria-label="Scrollable connections map">
          <div className="graph-box" ref={box} style={{ height }} role="img" aria-label={`Connection map: ${focusNode!.label}. Use List view for keyboard navigation.`} />
        </div>
      </> : <div className="connection-list">{adjacency(data).map((node) => <section key={node.id}>
        <h3><span className="mono">{KIND[node.kind]} </span><a href={navigate(node.id)}>{node.label}</a></h3>
        <ul>{node.links.map((link) => <li key={`${link.source}-${link.target}-${link.kind}`}><a href={navigate(link.id)}>{link.label}</a> — {link.explanation ?? RELATION[link.kind]}
          {link.state && <span className="mono"> · {link.role === 'primary' ? 'Main technique' : 'Supporting technique'} · {STATE_LABEL[link.state]}</span>}</li>)}</ul>
      </section>)}</div>}</div></div>
      <section className="stack" aria-label="Example counts">
        <h2>Examples in this exploration</h2>
        {techniques.map((t) => { const shown = data.edges.filter((e) => e.kind === 'example' && e.source === `technique:${t.id}`).length
          const total = data.example_counts?.[t.id] ?? 0
          return <div className="row" key={t.id}><a href={navigate(`technique:${t.id}`)}>{t.name}</a><span className="mono">{shown} of {total} shown</span>
            {shown < total && (start === `technique:${t.id}` && limit < 200 ? <button type="button" className="small" onClick={() => go('connections', { focus: start, view, limit: Math.min(200, limit + 12), trail: trail.join('|') })}>Show more examples</button>
              : <a href={navigate(`technique:${t.id}`)}>Explore examples</a>)}
            <a href={href('', { technique: t.id, from: context })}>View all {total} in library</a></div>
        })}
        {!examples.length && <p>No examples yet. <a href={href('find', { technique: start.startsWith('technique:') ? start.slice(10) : undefined })}>Find images</a> to grow this part of your library.</p>}
      </section>
      <div className="connection-examples">{examples.map((node) => {
        const id = Number(node.id.split(':')[1]); const picked = compare.some((p) => p.id === id)
        return <article key={id}><a href={open(node.id)}><img src={media(node.thumb)} alt={node.label} loading="lazy" /></a>
          <h3><a href={open(node.id)}>{node.label}</a></h3>
          {data.edges.filter((e) => e.kind === 'example' && e.target === node.id).map((edge) => <div key={edge.source} className="example-reading">
            <a href={navigate(edge.source)}>{label(edge.source)}</a><p className="mono">{edge.role === 'primary' ? 'Main technique in this reading' : 'Supporting technique in this reading'} · {edge.state ? STATE_LABEL[edge.state] : 'Review state unavailable'}</p>
            <p>{edge.explanation}</p>{edge.evidence?.length ? <details><summary>Visible evidence</summary><ul>{edge.evidence.map((e, i) => <li key={i}>{e}</li>)}</ul></details> : null}</div>)}
          <button type="button" className="small" aria-pressed={picked} disabled={!picked && compare.length >= 4}
            onClick={() => toggleCompare({ id, title: node.label, thumb: node.thumb ?? undefined })}>{picked ? 'Remove from compare' : '+ Compare'}</button></article>
      })}</div>
      <p className="mono">Main and supporting describe the saved annotation, not certainty. Proposed readings are unconfirmed; model agreement is not confirmation by you. Browsing never calls AI.</p>
    </>}
  </div>
}
