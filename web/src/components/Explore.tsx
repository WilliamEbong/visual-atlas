import { media, readOnly } from '../lib/client'
import { useApp, useData } from '../lib/hooks'
import { aspect } from '../lib/library'
import { href, type Route } from '../lib/router'
import type { TechniqueDetail } from '../lib/types'
import { STATE_LABEL } from '../lib/types'
import { Empty, Failure, Loading, PageHead } from './ui'

const RELATION: Record<string, string> = { often_combined: 'Often with', opposite_strategy: 'Opposite strategy',
  similar_purpose: 'Similar purpose', builds_on: 'Builds on', can_create: 'Can create', related: 'Related' }
const STRIP = [150, 176, 210, 160, 236, 190]
const short = (name: string) => name.replace(/ \(.*\)$/, '')

export default function Explore({ route }: { route: Route }) {
  const [, kind, id] = route.path
  if (kind === 'technique' && id) return <TechniquePage id={id} />
  if (kind === 'goal' && id) return <GoalPage id={id} />
  return <ExploreIndex />
}

function ExploreIndex() {
  const { taxonomy } = useApp()
  if (!taxonomy) return <><PageHead kicker="Explore" title="Ways of looking" /><Loading plates={false} /></>
  return (
    <>
      <PageHead kicker={`Explore · ${taxonomy.goals.length} goals · ${taxonomy.techniques.length} techniques`} title="Ways of looking"
        aside={<a className="button" href={href('connections', { focus: `goal:${taxonomy.goals[0]?.id}` })}>See connections as a map</a>} asideClass="actions" />
      <p className="lede under">Start from what you want an image to do. Each goal leads to the techniques that can achieve it, and each technique to real examples in your library.</p>
      <section className="section" aria-labelledby="goals" style={{ marginTop: 40 }}>
        <h2 id="goals">Goals</h2>
        <nav className="drawers" aria-label="Goals" style={{ marginTop: 16 }}>
          {taxonomy.goals.map((goal, index) => (
            <a key={goal.id} className="drawer" href={href(`explore/goal/${goal.id}`)}>
              <span className="letter" aria-hidden="true">{index + 1}</span>
              <span><strong>{goal.name}</strong><span className="text">{goal.description}</span>
                <span className="mono" style={{ display: 'block', marginTop: 6 }}>{taxonomy.techniques.filter((t) => t.goals.includes(goal.id)).length} techniques</span></span>
            </a>))}
        </nav>
      </section>
      <section className="section" aria-labelledby="all">
        <h2 id="all">All techniques</h2>
        <div className="scroll-x" style={{ marginTop: 12 }}><table className="plain">
          <thead><tr><th scope="col">Technique</th><th scope="col">What it is</th><th scope="col">Operations</th><th scope="col">Examples</th></tr></thead>
          <tbody>{taxonomy.techniques.map((t) => (
            <tr key={t.id}><th scope="row"><a href={href(`technique/${t.id}`)} style={{ fontFamily: 'var(--display)', fontSize: 21 }}>{t.name}</a></th><td>{t.definition}</td>
              <td className="mono">{t.operations.map((o) => taxonomy.operations.find((x) => x.id === o)?.name ?? o).join(', ')}</td>
              <td className="mono">{t.examples}</td></tr>))}</tbody>
        </table></div>
      </section>
      <section className="section trays" aria-label="Operations and domains">
        <div className="tray-col rule-blue"><h2>Operations</h2><p className="muted" style={{ fontSize: 14, marginBottom: 12 }}>What a technique does.</p>
          <ul>{taxonomy.operations.map((o) => <li key={o.id}><strong>{o.name}</strong><span>{o.description}</span></li>)}</ul></div>
        <div className="tray-col rule-green"><h2>Domains</h2><p className="muted" style={{ fontSize: 14, marginBottom: 12 }}>The visual variable it works on. Style, medium, subject and period describe an image, not how it works.</p>
          <ul>{taxonomy.domains.map((d) => <li key={d.id}><strong>{d.name}</strong><span>{d.variables.join(', ')}</span></li>)}</ul></div>
      </section>
    </>
  )
}

function GoalPage({ id }: { id: string }) {
  const { data, error, busy, reload } = useData<{ id: string; name: string; description: string; techniques: { id: string; name: string; definition: string; examples: number; thumb?: string }[] }>(`goals/${id}`)
  if (error) return <><PageHead kicker={<a href="#/explore">Explore</a>} title="Goal" /><Failure message={error} busy={busy} retry={reload} /></>
  if (!data) return <><PageHead kicker={<a href="#/explore">Explore</a>} title="…" /><Loading /></>
  return (
    <>
      <PageHead kicker={<><a href="#/explore">Explore</a> / goal</>} title={data.name}
        aside={<a className="button" href={href('connections', { focus: `goal:${id}` })}>See connections</a>} asideClass="actions" />
      <p className="lede under">{data.description} These techniques can serve this goal; each one works differently.</p>
      <div className="cards" style={{ marginTop: 32 }}>
        {data.techniques.map((t) => (
          <a key={t.id} className="plate" href={href(`technique/${t.id}`)}>
            <span className="card-frame">{t.thumb ? <img src={media(t.thumb)} alt={`Example of ${t.name}`} loading="lazy" /> : <span className="mono">No example yet</span>}</span>
            <span className="fig">{t.examples} example{t.examples === 1 ? '' : 's'}</span>
            <span className="plate-title">{t.name}</span><span className="maker">{t.definition}</span>
          </a>))}
      </div>
    </>
  )
}

function TechniquePage({ id }: { id: string }) {
  const { taxonomy } = useApp()
  const { data, error, busy, reload } = useData<TechniqueDetail>(`techniques/${id}`)
  if (error) return <><PageHead kicker={<a href="#/explore">Explore</a>} title="Technique" /><Failure message={error} busy={busy} retry={reload} /></>
  if (!data) return <><PageHead kicker={<a href="#/explore">Explore</a>} title="…" /><Loading /></>
  const index = taxonomy?.techniques.findIndex((t) => t.id === id) ?? -1
  const lens = data.examples.find((e) => e.state === 'human_reviewed') ?? data.examples[0]
  const confirmed = data.examples.filter((e) => e.state === 'human_reviewed').length
  return (
    <>
      <section className="horizon-head" aria-labelledby="technique-title">
        <div className="head-text">
          <p className="kicker"><a href="#/explore">Explore</a>{data.goals[0] && <> / <a href={href(`explore/goal/${data.goals[0].id}`)}>{data.goals[0].name}</a></>}
            {index >= 0 && taxonomy && <> / technique {index + 1} of {taxonomy.techniques.length}</>}</p>
          <h1 id="technique-title" style={{ fontSize: 'clamp(44px, 6vw, 84px)', lineHeight: .98 }}>{data.name}</h1>
        </div>
        {lens && <a className="lens" href={href(`image/${lens.id}`)} aria-label={`Example: ${lens.title}`}>
          <img src={media(lens.display ?? lens.thumb)} alt="" /></a>}
      </section>
      <div className={lens ? 'beside-lens under' : 'under'}>
        <p style={{ fontFamily: 'var(--display)', fontSize: 26, lineHeight: 1.25, maxWidth: 760 }}>{data.definition}</p>
        <p className="muted" style={{ marginTop: 12, maxWidth: 760 }}>{data.explanation}</p>
        {data.aliases.length > 0 && <p className="mono" style={{ marginTop: 10 }}>Also called {data.aliases.join(', ')}</p>}
      </div>
      {lens && <p className="mono" style={{ textAlign: 'right', marginTop: 8 }}>Through the lens: {lens.title}{lens.creator ? `, ${lens.creator}` : ''}</p>}

      <div className="trays section" style={{ marginTop: 48 }}>
        <section className="tray-col rule-blue" aria-labelledby="spot"><h2 id="spot">How to spot it</h2>
          <ul>{data.observable_cues.map((cue) => <li key={cue}><span>{cue}</span></li>)}</ul></section>
        <section className="tray-col rule-green" aria-labelledby="helps"><h2 id="helps">When it helps</h2>
          <ul>{data.when_it_helps.map((item) => <li key={item}><span>{item}</span></li>)}</ul></section>
        <section className="tray-col rule-ochre" aria-labelledby="confused"><h2 id="confused">Easily confused with</h2>
          <ul>{data.confusions.map((c) => <li key={c.technique}><strong><a href={href(`technique/${c.technique}`)}>{short(c.name)}</a></strong><span>{c.how_to_tell}</span></li>)}</ul></section>
        <section className="tray-col rule-rust" aria-labelledby="limits"><h2 id="limits">Limits</h2>
          <ul><li><span>{data.limitations}</span></li><li><strong>Not this</strong><span>{data.counterexample}</span></li></ul></section>
      </div>

      <section className="section" aria-labelledby="examples">
        <div className="section-title">
          <h2 id="examples">In your library <span className="mono" style={{ fontSize: 14 }}>{data.examples.length} example{data.examples.length === 1 ? '' : 's'}{confirmed ? ` · ${confirmed} confirmed by you` : ''}</span></h2>
          <div className="row">
            {!readOnly && <a className="button primary" href={href('find', { technique: data.id })}>Find more examples</a>}
            <a className="button" href={href('', { technique: data.id })}>Show in the library</a>
            {data.examples.length >= 2 && <a className="button" href={href('compare', { ids: data.examples.slice(0, 4).map((e) => e.id).join(',') })}>Compare them</a>}
          </div>
        </div>
        {data.examples.length === 0 ? <Empty title="No examples yet" actions={!readOnly && <a className="button primary" href={href('find', { technique: data.id })}>Find examples</a>}>
          Find a few, and they will appear here with the evidence for each reading.</Empty> : <>
          <div className="strip" style={{ marginTop: 22 }}>
            {data.examples.slice(0, 12).map((e, i) => (
              <a key={e.id} href={href(`image/${e.id}`)} className="specimen" style={{ height: STRIP[i % STRIP.length], aspectRatio: aspect(e) }} aria-label={e.title}>
                <img src={media(e.thumb)} alt="" loading="lazy" /></a>))}
          </div>
          <ol className="strip-caption mono">{data.examples.slice(0, 12).map((e, i) => <li key={e.id}>Fig. {i + 1}  {e.title} · <span className={`state ${e.state}`}>{STATE_LABEL[e.state].replace(/^\S+ /, '')}</span></li>)}</ol>
        </>}
      </section>

      <section className="section split" aria-label="Nearby in the atlas">
        <div className="main-col">
          <h2>Nearby in the atlas</h2>
          <ul style={{ listStyle: 'none', padding: 0, marginTop: 12 }}>
            {data.related.map((r) => (
              <li key={r.id} className="row" style={{ padding: '14px 0', borderBottom: '1px solid var(--hair)', alignItems: 'baseline', gap: 20 }}>
                <span className="mono" style={{ minWidth: 130 }}>{RELATION[r.relation] ?? r.relation}</span>
                <a href={href(`technique/${r.id}`)} style={{ fontFamily: 'var(--display)', fontSize: 23 }}>{short(r.name)}</a>
              </li>))}
          </ul>
        </div>
        <aside className="side-col slip">
          <p className="mono" style={{ color: 'var(--ink)' }}>Serves these goals</p>
          <ul style={{ listStyle: 'none', padding: 0, margin: '10px 0 0', display: 'flex', flexDirection: 'column', gap: 6 }}>
            {data.goals.map((g) => <li key={g.id}><a href={href(`explore/goal/${g.id}`)}>{g.name}</a></li>)}</ul>
          <p className="mono" style={{ marginTop: 14 }}>Operation: {data.operations.map((o) => o.name).join(', ')} · Domain: {data.domains.map((d) => d.name).join(', ')}</p>
          <p className="mono" style={{ marginTop: 14 }}>{data.working_definition ? 'Working definition written for Visual Atlas. Background reading: ' : 'Sources: '}
            {data.sources.map((s, i) => <span key={s.url}>{i ? '; ' : ''}<a href={s.url} target="_blank" rel="noreferrer">{s.citation}</a></span>)}</p>
          <p style={{ marginTop: 14 }}><a href={href('connections', { focus: `technique:${data.id}` })}>See the connections map →</a></p>
        </aside>
      </section>
    </>
  )
}
