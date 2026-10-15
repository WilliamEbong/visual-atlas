import { useEffect, useRef, useState } from 'react'
import { media } from '../lib/client'
import { adjacency, layout, route } from '../lib/graph'
import { useApp, useData } from '../lib/hooks'
import { go, href } from '../lib/router'
import type { GraphData } from '../lib/types'
import { Failure, Loading, PageHead } from './ui'

const KIND_LABEL = { goal: 'Goal', technique: 'Technique', image: 'Image' } as Record<string, string>

export default function Connections({ focus }: { focus: string }) {
  const { taxonomy } = useApp()
  const start = focus || (taxonomy ? `goal:${taxonomy.goals[0].id}` : '')
  const { data, error, busy, reload } = useData<GraphData>(start ? `graph?focus=${encodeURIComponent(start)}` : null)
  const [view, setView] = useState<'map' | 'list'>(() => (window.matchMedia?.('(max-width: 640px)').matches ? 'list' : 'map'))
  const box = useRef<HTMLDivElement>(null)
  const cy = useRef<import('cytoscape').Core | null>(null)

  useEffect(() => {
    if (!data || view !== 'map' || !box.current) return
    let cancelled = false
    import('cytoscape').then(({ default: cytoscape }) => {
      if (cancelled || !box.current) return
      const ink = getComputedStyle(document.documentElement).getPropertyValue('--ink').trim() || '#1D1C1A'
      const nodes = layout(data).map((node) => ({ data: { id: node.id, label: node.label.length > 34 ? `${node.label.slice(0, 32)}…` : node.label,
        kind: node.kind, thumb: media(node.thumb) ?? '' }, position: { x: node.x, y: node.y }, classes: `${node.kind}${node.id === data.focus ? ' focus' : ''}` }))
      const edges = data.edges.map((edge, index) => ({ data: { id: `e${index}`, source: edge.source, target: edge.target } }))
      cy.current = cytoscape({
        container: box.current, elements: [...nodes, ...edges], layout: { name: 'preset', fit: true, padding: 40 },
        minZoom: 0.25, maxZoom: 3, autoungrabify: true,
        style: [
          { selector: 'node', style: { label: 'data(label)', 'font-family': 'Libre Franklin Variable, sans-serif', 'font-size': 12, color: ink,
            'text-wrap': 'wrap', 'text-max-width': '120px', 'text-valign': 'bottom', 'text-margin-y': 6 } },
          { selector: 'node.goal', style: { shape: 'rectangle', width: 26, height: 26, 'background-color': '#A2573B' } },
          { selector: 'node.technique', style: { shape: 'ellipse', width: 24, height: 24, 'background-color': '#236292' } },
          { selector: 'node.image', style: { shape: 'rectangle', width: 64, height: 64, 'background-color': '#8B867B', 'background-image': 'data(thumb)',
            'background-fit': 'contain', 'background-opacity': 0.25, 'font-size': 10 } },
          { selector: 'node.focus', style: { 'border-width': 4, 'border-color': ink, 'font-size': 15, 'font-weight': 'bold' } },
          { selector: 'edge', style: { width: 1, 'line-color': '#8B867B', opacity: 0.7, 'curve-style': 'straight' } },
        ],
      })
      cy.current.on('tap', 'node', (event) => {
        const id = event.target.id() as string
        if (id === data.focus) window.location.hash = route(id)
        else go('connections', { focus: id })
      })
    })
    return () => { cancelled = true; cy.current?.destroy(); cy.current = null }
  }, [data, view])

  const focusNode = data?.nodes.find((node) => node.id === data.focus)
  const head = <PageHead kicker={<><a href="#/explore">Explore</a> / connections</>} title="See connections" asideClass="actions"
    aside={<div className="segments" role="group" aria-label="View">
      <button type="button" className={view === 'map' ? 'primary' : ''} aria-pressed={view === 'map'} onClick={() => setView('map')}>Map</button>
      <button type="button" className={view === 'list' ? 'primary' : ''} aria-pressed={view === 'list'} onClick={() => setView('list')}>List</button></div>} />
  if (error) return <>{head}<Failure message={error} busy={busy} retry={reload} /></>
  return (
    <div className="stack">
      {head}
      <p className="lede under">One focus at a time: {focusNode ? <><strong>{KIND_LABEL[focusNode.kind]}: {focusNode.label}</strong> and what it connects to.</> : 'loading…'} Select a node to refocus the map on it; select the centre to open it.</p>
      <label className="field" style={{ maxWidth: 420 }}>Focus on
        <select value={start} onChange={(event) => go('connections', { focus: event.target.value })}>
          <optgroup label="Goals">{taxonomy?.goals.map((g) => <option key={g.id} value={`goal:${g.id}`}>{g.name}</option>)}</optgroup>
          <optgroup label="Techniques">{taxonomy?.techniques.map((t) => <option key={t.id} value={`technique:${t.id}`}>{t.name}</option>)}</optgroup>
          {start.startsWith('image:') && <option value={start}>{focusNode?.label ?? 'This image'}</option>}
        </select>
      </label>
      {view === 'map' ? <>
        <div className="row">
          <button type="button" onClick={() => cy.current?.zoom({ level: (cy.current.zoom() ?? 1) * 1.25, renderedPosition: { x: (box.current?.clientWidth ?? 0) / 2, y: (box.current?.clientHeight ?? 0) / 2 } })}>Zoom in</button>
          <button type="button" onClick={() => cy.current?.zoom({ level: (cy.current.zoom() ?? 1) / 1.25, renderedPosition: { x: (box.current?.clientWidth ?? 0) / 2, y: (box.current?.clientHeight ?? 0) / 2 } })}>Zoom out</button>
          <button type="button" onClick={() => cy.current?.fit(undefined, 40)}>Fit</button>
          <span className="legend"><span className="g">Goal</span><span className="t">Technique</span><span className="i">Image</span></span>
        </div>
        <div className="graph-box" ref={box} role="img" aria-label={`Connection map centred on ${focusNode?.label ?? 'the focus'}. Use the List view for a keyboard-friendly version.`} />
      </> : !data ? <Loading plates={false} /> : (
        <div className="stack">
          {adjacency(data).map((node) => (
            <section key={node.id} aria-label={`${KIND_LABEL[node.kind]} ${node.label}`}>
              <h3><span className="mono">{KIND_LABEL[node.kind]}</span> <a href={node.id === data.focus ? route(node.id) : href('connections', { focus: node.id })}>{node.label}</a>
                {node.id !== data.focus && <> · <a className="mono" href={route(node.id)}>open</a></>}</h3>
              <ul className="mono">{node.links.map((link) => <li key={link.id}>{link.kind === 'serves' ? 'serves / served by' : link.kind === 'example' ? 'example link' : 'related'}: {link.label}</li>)}</ul>
            </section>))}
        </div>
      )}
    </div>
  )
}
