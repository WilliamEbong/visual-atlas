// Ask the atlas: a brief in, techniques that fit and references with reasons out. Ordinary code, no AI, so it
// answers at once. The same engine answers agents through the CLI and the MCP server (atlas/desk.py).
import { useEffect, useState } from 'react'
import { readOnly } from '../lib/client'
import { useData } from '../lib/hooks'
import { go, href, useRoute } from '../lib/router'
import type { DeskAnswer, DeskRef } from '../lib/types'
import { Empty, Failure, Loading, PageHead } from './ui'

const EXAMPLES = ['A calm opening slide: one small figure in a lot of empty space',
  'Make one product stand out on a dark poster', 'Show how big the mountains are for a travel talk',
  'A surprising image for an essay about cities']
const LAYER_NAMES: Record<string, string> = { library: 'Your library', generated: 'Generated examples', 'design-system': 'Design systems' }

export function layerLabel(ref: DeskRef): string {
  if (ref.layer === 'design-system') return `Design system · ${ref.system}`
  return ref.layer === 'generated' ? 'Generated example' : 'Library'
}

function refLink(ref: DeskRef, from: string): string {
  return ref.layer === 'library' && ref.image_id ? href(`image/${ref.image_id}`, { from }) : href('ref', { id: ref.ref, from })
}

function aspect(ref: DeskRef): number {
  return ref.width && ref.height ? Math.min(2.4, Math.max(0.5, ref.width / ref.height)) : 1.3
}

export default function Ask() {
  const route = useRoute()
  const asked = route.query.get('q') ?? ''
  const use = route.query.get('use') === 'publish' ? 'publish' : 'reference'
  const off = (route.query.get('off') ?? '').split(',').filter(Boolean)
  const [text, setText] = useState(asked)
  useEffect(() => setText(asked), [asked])
  const query = new URLSearchParams({ brief: asked, use, limit: '12' })
  const wanted = Object.keys(LAYER_NAMES).filter((layer) => !off.includes(layer))
  if (off.length) query.set('layers', wanted.join(','))
  const answer = useData<DeskAnswer>(!readOnly && asked.trim() ? `desk?${query}` : null)
  const set = (changes: Record<string, string>) => go('ask', { q: asked, use, off: off.join(','), ...changes })
  const from = window.location.hash

  if (readOnly) return <><PageHead kicker="Ask the atlas" title="What should the picture do?" />
    <div className="slip under" style={{ marginTop: 32 }}><p>Asking works in the downloaded app, where it reads your whole
      library. <a href="https://github.com/WilliamEbong/visual-atlas/releases/latest">Download Visual Atlas</a>.</p></div></>

  return (
    <>
      <PageHead kicker="Ask the atlas" title="What should the picture do?" />
      <form className="ask-form under" onSubmit={(event) => { event.preventDefault(); set({ q: text.trim() }) }}>
        <label className="field ask-brief">Describe the picture you need and what it is for
          <textarea rows={3} value={text} maxLength={4000} onChange={(event) => setText(event.target.value)}
            placeholder="For example: a calm opening slide with one small figure in a lot of empty space"
            onKeyDown={(event) => { if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) set({ q: text.trim() }) }} />
        </label>
        <div className="ask-controls">
          <fieldset>
            <legend>How you will use it</legend>
            <div className="segments">
              {([['reference', 'As a reference'], ['publish', 'In published work']] as const).map(([value, label]) => (
                <label key={value} className="choice"><input type="radio" name="use" checked={use === value}
                  onChange={() => set({ use: value })} />{label}</label>))}
            </div>
          </fieldset>
          <button type="submit" className="primary" disabled={!text.trim()}>Ask</button>
        </div>
        {!asked && <div className="examples" aria-label="Examples">
          <span className="mono">Try</span>
          {EXAMPLES.map((example) => <button key={example} type="button" className="quiet" onClick={() => set({ q: example })}>{example}</button>)}
        </div>}
      </form>
      {asked && answer.error && <Failure message={answer.error} busy={answer.busy} retry={answer.reload} />}
      {asked && !answer.data && !answer.error && <Loading label="Reading your brief…" />}
      {answer.data && <Answer data={answer.data} use={use} off={off} from={from} toggle={(layer) =>
        set({ off: (off.includes(layer) ? off.filter((l) => l !== layer) : [...off, layer]).join(',') })} />}
      {!asked && <p className="lede" style={{ marginTop: 40 }}>The atlas reads your brief, names the techniques that could serve it,
        and shows pictures that use them, each with the reason it was chosen and its licence. Nothing is sent to an AI service.</p>}
    </>
  )
}

function Answer({ data, use, off, from, toggle }: { data: DeskAnswer; use: string; off: string[]; from: string; toggle: (layer: string) => void }) {
  const reading = [...data.reading.goals, ...data.reading.techniques].map((t) => t.name)
  const available = ['library', ...(data.layers.generated ? ['generated'] : []), ...(data.layers['design-system'].length ? ['design-system'] : [])]
  return (
    <>
      <section className="reading-line" aria-label="How the atlas read your brief">
        <p><span className="mono">Read as </span>{reading.length ? reading.join(' · ') : 'no goal or technique the atlas knows yet'}
          {data.reading.subject_terms.length > 0 && <span className="muted">, about {data.reading.subject_terms.join(', ')}</span>}</p>
        {data.route.system && data.layers['design-system'].length > 0 && <p className="mono">Design system: {data.route.system.name}. {data.route.system.why}.</p>}
        {available.length > 1 && <div className="row layer-toggles" role="group" aria-label="Where to look">
          {available.map((layer) => <label key={layer} className="choice plain"><input type="checkbox" checked={!off.includes(layer)}
            onChange={() => toggle(layer)} />{LAYER_NAMES[layer]}</label>)}
        </div>}
      </section>
      {data.guidance.length > 0 && <section className="section guidance" aria-labelledby="guidance-title" style={{ marginTop: 40 }}>
        <h2 id="guidance-title">Techniques that could do it</h2>
        <div className="trays" style={{ marginTop: 20 }}>
          {data.guidance.map((g, index) => <div key={g.id} className={`tray-col ${['rule-blue', 'rule-green', 'rule-ochre', 'rule-rust'][index % 4]}`}>
            <h3><a href={href(`technique/${g.id}`)}>{g.name}</a></h3>
            <p className="guide-def">{g.definition}</p>
            <p className="mono" style={{ marginTop: 12 }}>Look for</p>
            <ul>{g.look_for.slice(0, 3).map((cue) => <li key={cue}>{cue}</li>)}</ul>
            {g.not_to_confuse_with[0] && <p className="muted guide-note">Not the same as {g.not_to_confuse_with[0].technique}: {g.not_to_confuse_with[0].how_to_tell}</p>}
          </div>)}
        </div>
      </section>}
      <section className="section" aria-labelledby="refs-title" style={{ marginTop: 56 }}>
        <div className="section-title">
          <h2 id="refs-title">References</h2>
          <p className="mono">{data.results.length ? `${data.results.length} of ${data.total_matches} matches` : ''}
            {use === 'publish' ? ' · free to publish with credit' : ''}</p>
        </div>
        {data.results.length === 0 ? <Empty title="Nothing in the atlas fits yet" actions={<a className="button primary"
          href={href('find', { goal: data.reading.subject_terms.join(' ') })}>Find new images</a>}>
          Try other words, say what the picture should do (stand out, feel calm, show scale), or find new images from open collections.</Empty>
          : <div className="justified desk-results">
            {data.results.map((ref) => <article key={ref.ref} className="plate-item" style={{ '--a': aspect(ref) } as React.CSSProperties}>
              <a className="plate" href={refLink(ref, from)}>
                <span className="plate-frame"><img src={ref.thumb ?? undefined} alt={`${ref.title}${ref.creator ? `, ${ref.creator}` : ''}`} loading="lazy" decoding="async" /></span>
                <span className={`fig layer-tag ${ref.layer}`}>{layerLabel(ref)}</span>
                <span className="plate-title">{ref.title}</span>
                {ref.creator && <span className="maker">{ref.creator}{ref.date ? `, ${ref.date}` : ''}</span>}
              </a>
              <ul className="reasons">{ref.reasons.slice(0, 2).map((reason) => <li key={reason}>{reason}</li>)}</ul>
              <p className="licence-line">{ref.licence.label}</p>
            </article>)}
          </div>}
      </section>
      <p className="mono" style={{ marginTop: 40, maxWidth: 760 }}>{data.note}</p>
    </>
  )
}

export function RefPage({ id }: { id: string }) {
  const route = useRoute()
  const ref = useData<DeskRef>(id ? `desk/ref?ref=${encodeURIComponent(id)}` : null)
  const back = route.query.get('from')
  if (ref.error) return <Failure message={ref.error} retry={ref.reload} />
  if (!ref.data) return <Loading label="Opening the reference…" />
  const r = ref.data
  return (
    <>
      <div className="crumbs">{back ? <a href={back}>← Back to your answer</a> : <a href="#/ask">← Ask the atlas</a>}
        <span className="mono">{layerLabel(r)}</span></div>
      <div className="image-head">
        <figure className="figure" style={{ aspectRatio: aspect(r) }}><img src={r.image ?? undefined} alt={r.title} /></figure>
        <div className="image-title">
          <p className="kicker">{layerLabel(r)}</p>
          <h1>{r.title}</h1>
          {r.creator && <p className="muted">{r.creator}{r.date ? `, ${r.date}` : ''}</p>}
        </div>
      </div>
      <div className="three">
        <section className="see">
          <h2 className="ruled-title rule-blue">What it shows</h2>
          {r.techniques.length > 0 && <ul className="observations">{r.techniques.map((t) => <li key={t.id} style={{ padding: '12px 0' }}>
            <a href={href(`technique/${t.id}`)}>{t.name ?? t.id}</a> <span className="state">{t.state_means ?? t.state}</span></li>)}</ul>}
          {r.notes && <p style={{ marginTop: 14 }}>{r.notes}</p>}
          {r.subjects && r.subjects.length > 0 && <p className="mono" style={{ marginTop: 14 }}>Subjects: {r.subjects.join(', ')}</p>}
        </section>
        <section className="why">
          <h2 className="ruled-title rule-green">{r.generated ? 'How it was made' : 'Where it comes from'}</h2>
          {r.prompt && <><p className="mono" style={{ marginTop: 14 }}>Prompt</p><p className="slip-text" style={{ whiteSpace: 'pre-line' }}>{r.prompt}</p></>}
          {r.studied && r.studied.length > 0 && <><p className="mono" style={{ marginTop: 14 }}>Works studied for craft (not copied)</p>
            <ul>{r.studied.map((s) => <li key={s.title}><a href={s.source_url} rel="noreferrer noopener" target="_blank">{s.title}</a>, {s.creator}{s.lesson ? `: ${s.lesson}` : ''}</li>)}</ul></>}
          {r.source_url?.startsWith('https://') && <p style={{ marginTop: 14 }}><a href={r.source_url} rel="noreferrer noopener" target="_blank">Source record</a></p>}
        </section>
        <section className="use">
          <h2 className="ruled-title rule-ochre">Usage and credit</h2>
          <p style={{ marginTop: 14 }}>{r.licence.label}</p>
          {r.licence.note && <p className="mono" style={{ marginTop: 8 }}>{r.licence.note}</p>}
          {r.credit && <p className="credit" style={{ marginTop: 14 }}>{r.credit}</p>}
          {r.layer === 'design-system' && <p className="muted" style={{ marginTop: 14, fontSize: 14 }}>From a private design-system library on this computer. It is not part of Visual Atlas and is never shared or exported by it.</p>}
        </section>
      </div>
    </>
  )
}
