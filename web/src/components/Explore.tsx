import { media, readOnly } from '../lib/client'
import { useApp, useData } from '../lib/hooks'
import { href, type Route } from '../lib/router'
import type { TechniqueDetail } from '../lib/types'
import { STATE_LABEL } from '../lib/types'

const RELATION: Record<string, string> = { often_combined: 'often combined with', opposite_strategy: 'the opposite strategy',
  similar_purpose: 'similar purpose', builds_on: 'builds on', can_create: 'can create', related: 'related' }

export default function Explore({ route }: { route: Route }) {
  const [, kind, id] = route.path
  if (kind === 'technique' && id) return <TechniquePage id={id} />
  if (kind === 'goal' && id) return <GoalPage id={id} />
  return <ExploreIndex />
}

function ExploreIndex() {
  const { taxonomy } = useApp()
  if (!taxonomy) return <p className="mono">Loading…</p>
  return (
    <div className="stack">
      <h1>Explore</h1>
      <p className="lede">Start from what you want an image to do. Each goal leads to the techniques that can achieve it, and each technique to real examples in your library.</p>
      <h2 style={{ marginTop: 16 }}>Goals</h2>
      <div className="drawers" style={{ marginTop: 0 }}>
        {taxonomy.goals.map((goal) => (
          <a key={goal.id} className="drawer" href={href(`explore/goal/${goal.id}`)}>
            <strong>{goal.name}</strong><span>{goal.description}</span>
            <span className="mono">{taxonomy.techniques.filter((t) => t.goals.includes(goal.id)).length} techniques</span>
          </a>))}
      </div>
      <hr className="horizon" />
      <div className="page-head"><h2>All techniques</h2><a href={href('connections', { focus: `goal:${taxonomy.goals[0]?.id}` })}>See connections as a map</a></div>
      <div className="scroll-x"><table className="plain">
        <thead><tr><th>Technique</th><th>What it is</th><th>Operations</th><th>Examples</th></tr></thead>
        <tbody>{taxonomy.techniques.map((t) => (
          <tr key={t.id}><td><a href={href(`technique/${t.id}`)}>{t.name}</a></td><td>{t.definition}</td>
            <td className="mono">{t.operations.map((o) => taxonomy.operations.find((x) => x.id === o)?.name ?? o).join(', ')}</td>
            <td className="mono">{t.examples}</td></tr>))}</tbody>
      </table></div>
      <h2 style={{ marginTop: 24 }}>Operations and domains</h2>
      <p className="muted">Operations are what a technique does (contrast, isolate, repeat…). Domains are the visual variable it works on (colour, scale, light…). Style, medium, subject and period are kept separate: they describe an image, not how it works.</p>
      <div className="split">
        <ul className="main-col">{taxonomy.operations.map((o) => <li key={o.id}><strong>{o.name}</strong> — {o.description}</li>)}</ul>
        <ul className="side-col">{taxonomy.domains.map((d) => <li key={d.id}><strong>{d.name}</strong> — {d.variables.join(', ')}</li>)}</ul>
      </div>
    </div>
  )
}

function GoalPage({ id }: { id: string }) {
  const { data, error } = useData<{ id: string; name: string; description: string; techniques: { id: string; name: string; definition: string; examples: number; thumb?: string }[] }>(`goals/${id}`)
  if (error) return <p className="notice error" role="alert">{error}</p>
  if (!data) return <p className="mono">Loading…</p>
  return (
    <div className="stack">
      <p><a href="#/explore">← Explore</a></p>
      <div className="page-head"><h1>{data.name}</h1><a href={href('connections', { focus: `goal:${id}` })}>See connections</a></div>
      <p className="lede">{data.description} These techniques can serve this goal; each one works differently.</p>
      <div className="plates">
        {data.techniques.map((t) => (
          <a key={t.id} className="plate" href={href(`technique/${t.id}`)}>
            <div className="frame">{t.thumb ? <img src={media(t.thumb)} alt={`Example of ${t.name}`} loading="lazy" /> : <span className="mono">No example yet</span>}</div>
            <span className="title">{t.name}</span><span className="maker">{t.definition}</span>
            <span className="mono">{t.examples} example{t.examples === 1 ? '' : 's'}</span>
          </a>))}
      </div>
    </div>
  )
}

function TechniquePage({ id }: { id: string }) {
  const { data, error } = useData<TechniqueDetail>(`techniques/${id}`)
  if (error) return <p className="notice error" role="alert">{error}</p>
  if (!data) return <p className="mono">Loading…</p>
  return (
    <div className="stack">
      <p><a href="#/explore">← Explore</a></p>
      <div className="page-head">
        <h1>{data.name}</h1>
        <div className="row">
          {!readOnly && <a className="button" href={href('find', { technique: data.id })}>Find more examples</a>}
          <a className="button" href={href('', { technique: data.id })}>Show in library</a>
          <a className="button" href={href('connections', { focus: `technique:${data.id}` })}>See connections</a>
        </div>
      </div>
      {data.aliases.length > 0 && <p className="mono">Also called: {data.aliases.join(', ')}</p>}
      <div className="split">
        <section className="main-col stack">
          <p style={{ fontSize: 20, lineHeight: 1.4 }}>{data.definition}</p>
          <p className="muted">{data.explanation}</p>
          <h2>Where to look</h2>
          <ul>{data.observable_cues.map((cue) => <li key={cue}>{cue}</li>)}</ul>
          <h2>When it may help</h2>
          <ul>{data.when_it_helps.map((item) => <li key={item}>{item}</li>)}</ul>
          <h2>Examples in your library</h2>
          {data.examples.length === 0 ? <p className="muted">None yet. {!readOnly && <a href={href('find', { technique: data.id })}>Find examples</a>}</p> : (
            <div className="plates" style={{ marginTop: 0 }}>{data.examples.map((e) => (
              <a key={e.id} className="plate" href={href(`image/${e.id}`)}>
                <div className="frame"><img src={media(e.thumb)} alt={e.title} loading="lazy" /></div>
                <span className="title">{e.title}</span><span className="maker">{[e.creator, e.date_text].filter(Boolean).join(', ')}</span>
                <span className={`state ${e.state}`}>{STATE_LABEL[e.state]}{e.role === 'primary' ? ' · main technique' : ''}</span>
              </a>))}</div>)}
        </section>
        <aside className="side-col stack">
          <h2>Don't confuse with</h2>
          <ul>{data.confusions.map((c) => <li key={c.technique}><a href={href(`technique/${c.technique}`)}>{c.name}</a>: {c.how_to_tell}</li>)}</ul>
          <h2>Limits</h2><p>{data.limitations}</p>
          <p><strong>Counterexample:</strong> {data.counterexample}</p>
          <h2>Related techniques</h2>
          <ul>{data.related.map((r) => <li key={r.id}><a href={href(`technique/${r.id}`)}>{r.name}</a> <span className="mono">{RELATION[r.relation] ?? r.relation}</span></li>)}</ul>
          <h2>Serves these goals</h2>
          <ul>{data.goals.map((g) => <li key={g.id}><a href={href(`explore/goal/${g.id}`)}>{g.name}</a></li>)}</ul>
          <p className="mono">Operation: {data.operations.map((o) => o.name).join(', ')} · Domain: {data.domains.map((d) => d.name).join(', ')}</p>
          <h2>Sources</h2>
          {data.working_definition && <p className="muted">Working definition written for Visual Atlas; the links are background reading on the idea, not the source of this wording.</p>}
          <ul>{data.sources.map((s) => <li key={s.url}><a href={s.url} target="_blank" rel="noreferrer">{s.citation}</a></li>)}</ul>
        </aside>
      </div>
    </div>
  )
}
