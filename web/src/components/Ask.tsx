// Ask the atlas: a brief in, techniques that fit and references with reasons out. Ordinary code, no AI, so it
// answers at once. The same engine answers agents through the CLI and the MCP server (atlas/desk.py).
import { useEffect, useRef, useState } from 'react'
import { protectedImage, readOnly } from '../lib/client'
import { useApp, useData } from '../lib/hooks'
import { cleanMaker, cleanTitle, shortDate } from '../lib/library'
import { go, href, useRoute } from '../lib/router'
import type { DeskAnswer, DeskDirections, DeskRef, DeskSimilar } from '../lib/types'
import { Empty, Failure, Loading, PageHead } from './ui'

const EXAMPLES = ['A calm opening slide: one small figure in a lot of empty space',
  'Make one product stand out on a dark poster', 'Show how big the mountains are for a travel talk',
  'A surprising image for an essay about cities']
/** A reference picture; layer pictures sit behind the launch token, so they are fetched rather than linked. */
function RefImage({ src, alt }: { src: string | null; alt: string }) {
  const [shown, setShown] = useState<string | undefined>(src && !src.startsWith('/api/') ? src : undefined)
  const [failed, setFailed] = useState(!src)
  useEffect(() => {
    setFailed(!src)
    if (!src || !src.startsWith('/api/')) { setShown(src ?? undefined); return }
    let live = true
    let url: string | undefined
    protectedImage(src).then((value) => { url = value; if (live) setShown(value); else URL.revokeObjectURL(value) })
      .catch(() => { if (live) { setShown(undefined); setFailed(true) } })
    return () => { live = false; if (url) URL.revokeObjectURL(url) }
  }, [src])
  if (failed) return <span className="picture-missing mono" role="img" aria-label={`${alt} (picture unavailable)`}>Picture unavailable</span>
  return shown ? <img src={shown} alt={alt} loading="lazy" decoding="async" onError={() => setFailed(true)} />
    : <span className="sr-only">{alt}</span>
}

const LAYER_NAMES: Record<string, string> = { library: 'Your library', generated: 'Generated examples', 'design-system': 'Design systems' }

/** Licence in plain words for the grid; the exact licence stays on the reference page. */
export function plainLicence(ref: DeskRef): string {
  if (ref.layer === 'design-system') return 'Private design system: reference only'
  switch (ref.licence.code) {
    case 'cc0': case 'pd': return 'Free to use; credit appreciated'
    case 'cc-by': return 'Free to use with credit'
    case 'generated': return 'No licence asserted'
    default: return 'Licence unclear: check the source'
  }
}

export function layerLabel(ref: DeskRef): string {
  if (ref.layer === 'design-system') return `Design system · ${ref.system}`
  return ref.layer === 'generated' ? 'Generated example' : 'Library'
}

/** Links keep the publication mode, so "More like this" on the next page stays within publishable pictures. */
function refLink(ref: DeskRef, from: string, use = 'reference'): string {
  const keep = use === 'publish' ? { use } : {}
  return ref.layer === 'library' && ref.image_id ? href(`image/${ref.image_id}`, { from, ...keep })
    : href('ref', { id: ref.ref, from, ...keep })
}

const STATE_MARK: Record<string, string> = { 'confirmed by you': '●', 'agreed by a second model': '◐', 'proposed by a model': '○',
  'intended by the prompt, checked by eye': '◇' }

/** "Shows Silhouette (agreed by a second model): A small bird…" as the technique, its evidence and a state mark. */
export function Reason({ text }: { text: string }) {
  const match = /^(?:Shows (.+?)|Serves “(.+?)” through (.+?)) \(([^)]+)\)(?:: (.*))?$/s.exec(text)
  if (!match) return <>{text}</>
  const [, shows, goal, via, state, evidence] = match
  return <><strong>{shows ?? `${via}, for “${goal}”`}</strong>{' '}
    <span className="state-mark" title={state} aria-label={state}>{STATE_MARK[state] ?? '○'}</span>{evidence ? ` ${evidence}` : ''}</>
}

function aspect(ref: DeskRef): number {
  return ref.width && ref.height ? Math.min(2.4, Math.max(0.5, ref.width / ref.height)) : 1.3
}

export default function Ask() {
  const route = useRoute()
  const asked = route.query.get('q') ?? ''
  const use = route.query.get('use') === 'publish' ? 'publish' : 'reference'
  const off = (route.query.get('off') ?? '').split(',').filter(Boolean)
  const goals = (route.query.get('goals') ?? '').split(',').filter(Boolean)
  const [text, setText] = useState(asked)
  const [changing, setChanging] = useState(false)
  const [moreOpen, setMoreOpen] = useState(false)
  const focusFrom = useRef(0)  // after loading more, focus the first new picture
  useEffect(() => { setText(asked); setChanging(false); setMoreOpen(false) }, [asked])
  const limit = Math.min(40, Math.max(12, Number(route.query.get('limit')) || 12))
  const query = new URLSearchParams({ brief: asked, use })
  const wanted = Object.keys(LAYER_NAMES).filter((layer) => !off.includes(layer))
  if (off.length) query.set('layers', wanted.join(','))
  if (goals.length) query.set('goals', goals.join(','))
  const live = !readOnly && asked.trim()
  const answer = useData<DeskAnswer>(live ? `desk?${query}&limit=${limit}` : null)
  const ways = useData<DeskDirections>(live ? `desk/directions?${query}` : null)
  useEffect(() => {
    if (!focusFrom.current || !answer.data) return
    const links = document.querySelectorAll<HTMLAnchorElement>('section[aria-labelledby="refs-title"] a.plate')
    const target = links[focusFrom.current - 1] ?? links[links.length - 1]
    focusFrom.current = 0
    target?.focus()
  }, [answer.data])
  const set = (changes: Record<string, string>) => go('ask', { q: asked, use, off: off.join(','), goals: goals.join(','), limit: '', ...changes })
  const from = /^#\/?$/.test(window.location.hash) ? '#/ask' : window.location.hash  // the front page is Ask

  if (readOnly) return <><PageHead kicker="Ask the atlas" title="What should the picture do?" />
    <div className="slip under" style={{ marginTop: 32 }}><p>Asking works in the downloaded app, where it reads your whole
      library. <a href="https://github.com/WilliamEbong/visual-atlas/releases/latest">Download Visual Atlas</a>.</p></div></>

  return (
    <>
      <PageHead kicker="Ask the atlas" title="What should the picture do?" />
      {!asked && <p className="lede under">You get ways to do it and pictures that show them, each with its reason and licence, chosen from your library without AI.</p>}
      {asked && !changing ? <div className="asked under">
        <p className="asked-brief">“{asked}”</p>
        <button type="button" className="quiet small" onClick={() => setChanging(true)}>Change the brief</button>
        <div className="segments small-segments" role="radiogroup" aria-label="How you will use it">
          {([['reference', 'As a reference'], ['publish', 'In published work']] as const).map(([value, label]) => (
            <label key={value} className="choice"><input type="radio" name="use-line" checked={use === value} onChange={() => set({ use: value })} />{label}</label>))}
        </div>
      </div>
      : <form className="ask-form under" onSubmit={(event) => { event.preventDefault()
        if (!text.trim()) { (event.currentTarget.querySelector('textarea') as HTMLTextAreaElement | null)?.focus(); return }
        set({ q: text.trim(), goals: '' }) }}>
        <label className="field ask-brief">Describe the picture you need and what it is for
          <textarea rows={3} value={text} maxLength={4000} onChange={(event) => setText(event.target.value)}
            placeholder="For example: a calm opening slide with one small figure in a lot of empty space"
            onKeyDown={(event) => { if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) set({ q: text.trim(), goals: '' }) }} />
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
          <button type="submit" className="primary">Ask</button>
        </div>
        {!asked && <div className="examples" role="group" aria-label="Examples">
          <span className="mono">Try</span>
          <div className="example-links">{EXAMPLES.map((example) => <button key={example} type="button" className="quiet" onClick={() => set({ q: example, goals: '' })}>{example}</button>)}</div>
        </div>}
      </form>}
      {asked && answer.error && <Failure message={answer.error} busy={answer.busy} retry={answer.reload} />}
      {asked && !answer.data && !answer.error && <Loading label="Reading your brief…" />}
      {answer.data && <Answer asked={asked} data={answer.data} ways={ways.error ? { reading: answer.data.reading, directions: [], note: '' } : ways.data} goals={goals} use={use} off={off} from={from}
        choose={(goal) => set({ goals: (goals.includes(goal) ? goals.filter((g) => g !== goal) : [...goals, goal]).join(',') })} more={limit < 40 && answer.data.total_matches > limit
        ? () => { focusFrom.current = document.querySelectorAll('section[aria-labelledby="refs-title"] a.plate').length + 1; set({ limit: String(limit + 12) }) } : undefined}
        moreOpen={moreOpen} setMoreOpen={setMoreOpen} toggle={(layer) =>
        set({ off: (off.includes(layer) ? off.filter((l) => l !== layer) : [...off, layer]).join(',') })} />}
      {!asked && <SampleAnswer brief={EXAMPLES[0]} use={use} from={from} open={() => set({ q: EXAMPLES[0], goals: '' })} />}

    </>
  )
}

/** The empty page shows what an answer looks like, with pictures, before anyone types. */
export function SampleAnswer({ brief, use, from, open }: { brief: string; use: string; from: string; open: () => void }) {
  const sample = useData<DeskDirections>(`desk/directions?${new URLSearchParams({ brief, use })}`)
  // The pictures chosen for the example's ways to do it: the first screen must show judgment, not every match.
  const checked = (sample.data?.directions ?? []).flatMap((way) => way.references).slice(0, 5)
  if (!checked.length) return null
  return (
    <section className="section sample" aria-labelledby="sample-title" style={{ marginTop: 40 }}>
      <div className="section-title">
        <h2 id="sample-title">For example: “{brief}”</h2>
        <button type="button" className="quiet" onClick={open}>See the whole answer</button>
      </div>
      <RefStrip refs={checked} from={from} use={use} label="Pictures from a sample answer" compact />
    </section>
  )
}

/** What the picture should do, chosen by the person: the word reader misses paraphrase, a click does not. */
function GoalChoice({ chosen, read, choose, missed }: { chosen: string[]; read: string[]; choose: (goal: string) => void; missed: boolean }) {
  const { taxonomy } = useApp()
  if (!taxonomy) return null
  const chips = <div className="chips">
    {taxonomy.goals.map((goal) => {
      const fromBrief = read.includes(goal.id)
      return <button key={goal.id} type="button" className={`chip${fromBrief ? ' from-brief' : ''}`}
        aria-pressed={chosen.includes(goal.id) || fromBrief} title={fromBrief ? 'Read from your brief: edit the brief to remove it' : goal.description}
        aria-describedby={fromBrief ? 'goal-choice-note' : undefined} disabled={fromBrief} onClick={() => choose(goal.id)}>{goal.name}</button>
    })}
  </div>
  if (missed) return (
    <div className="goal-choice" role="group" aria-labelledby="goal-choice-label">
      <p id="goal-choice-label" className="goal-ask">Pick one or two things the picture should do. The answer updates at once.</p>
      {chips}
    </div>
  )
  return (
    <details className="goal-choice" open={chosen.length > 0}>
      <summary>Change what the picture should do</summary>
      <div role="group" aria-label="What the picture should do">{chips}</div>
      {read.length > 0 && <p id="goal-choice-note" className="mono">Outlined goals were read from your brief.</p>}
    </details>
  )
}

/** Thumbnails that open their reference; shared by Ways to do it and More like this. */
function RefStrip({ refs, from, label, use, compact }: { refs: DeskRef[]; from: string; label: string; use: string; compact?: boolean }) {
  // The Library's justified rows: every picture at its true shape, rows that fill the width, one caption style.
  return (
    <ul className="justified refs-row" aria-label={label}>
      {refs.map((ref) => <li key={ref.ref} className="plate-item" style={{ '--a': aspect(ref) } as React.CSSProperties}>
        <a href={refLink(ref, from, use)} className="plate">
          <span className="plate-frame"><RefImage src={ref.thumb} alt="" /></span>
          <span className="plate-title">{cleanTitle(ref.title)}</span>{ref.creator && <span className="sr-only">, {ref.creator}</span>}</a>
        {compact ? <span className="mono strip-meta">{/^Shows (.+?) \(/.exec(ref.reasons[0] ?? '')?.[1] ?? layerLabel(ref)}</span> : <>
        {ref.reasons[0] && !ref.reasons[0].startsWith('Similar placement') && <span className="strip-reason"><Reason text={ref.reasons[0]} /></span>}
        <span className="mono strip-meta">{ref.layer !== 'library' ? `${layerLabel(ref)} · ` : ''}{plainLicence(ref)}</span></>}
      </li>)}
    </ul>
  )
}

/** "More like this": pictures whose light, dark and colour sit in the same places, from every layer. */
export function MoreLikeThis({ refId, from, use }: { refId: string; from: string; use: string }) {
  const alike = useData<DeskSimilar>(readOnly ? null : `desk/similar?ref=${encodeURIComponent(refId)}&limit=8&use=${use === 'publish' ? 'publish' : 'reference'}`)
  if (!alike.data?.results.length) return null
  return (
    <section className="section" aria-labelledby="alike-title" style={{ marginTop: 56 }}>
      <div className="section-title">
        <h2 id="alike-title">More like this</h2>
        <p className="mono">Similar placement of light, dark and colour, compared on this computer</p>
      </div>
      <RefStrip refs={alike.data.results} from={from} use={use} label="Pictures with a similar composition" />
    </section>
  )
}

function Plates({ refs, from, small, use }: { refs: DeskRef[]; from: string; small?: boolean; use: string }) {
  return (
    <div className={`justified desk-results${small ? ' small' : ''}`}>
      {refs.map((ref) => <article key={ref.ref} className="plate-item" style={{ '--a': aspect(ref) } as React.CSSProperties}>
        <a className="plate" href={refLink(ref, from, use)}>
          <span className="plate-frame"><RefImage src={ref.thumb} alt="" /></span>
          {ref.layer !== 'library' && <span className={`fig layer-tag ${ref.layer}`}>{layerLabel(ref)}</span>}
          <span className="plate-title">{cleanTitle(ref.title)}</span>
          {cleanMaker(ref.creator) && <span className="maker">{cleanMaker(ref.creator)}{ref.date ? `, ${shortDate(ref.date)}` : ''}</span>}
        </a>
        <p className="reason" title={ref.reasons.join('\n')}><Reason text={ref.reasons[0]} /></p>
        <p className="licence-line">{plainLicence(ref)}</p>
      </article>)}
    </div>
  )
}

function Answer({ asked, data, ways, goals: chosen, use, off, from, toggle, choose, more, moreOpen, setMoreOpen }: { asked: string; data: DeskAnswer
  moreOpen: boolean; setMoreOpen: (open: boolean) => void
  ways: DeskDirections | null; goals: string[]; use: string; off: string[]; from: string
  toggle: (layer: string) => void; choose: (goal: string) => void; more?: () => void }) {
  const goals = data.reading.goals.map((g) => g.name)
  const techniques = data.reading.techniques.map((t) => t.name)
  const missed = !goals.length && !techniques.length
  // the same test as the desk: evidence means a shown technique or a served goal; anything else is words only
  const wordsOnly = (ref: DeskRef) => !ref.reasons.some((reason) => reason.startsWith('Shows ') || reason.startsWith('Serves '))
  const shown = new Set((ways?.directions ?? []).flatMap((way) => way.references.map((ref) => ref.ref)))
  const rest = data.results.filter((ref) => !shown.has(ref.ref))
  // licensed library pictures first; generated examples (no licence asserted) after them
  const strong = rest.filter((ref) => !wordsOnly(ref)).sort((a, b) => Number(a.layer !== 'library') - Number(b.layer !== 'library'))
  const weak = rest.filter(wordsOnly)
  const available = ['library', ...(data.layers.generated ? ['generated'] : []), ...(data.layers['design-system'].length ? ['design-system'] : [])]
  return (
    <>
      <section className="reading-line" aria-label="How the atlas read your brief">
        <p>{!missed ? <>{goals.length > 0 && <><span className="mono">Goal </span>{goals.join(' · ')} </>}
          {techniques.length > 0 && !(ways?.directions.length || data.guidance.length) && <><span className="mono">{goals.length ? ' Techniques ' : 'Techniques '}</span>{techniques.join(' · ')}</>}
          {goals.length === 0 && techniques.length > 0 && (ways?.directions.length || data.guidance.length) ? <><span className="mono">Read as </span>{techniques.join(' · ')}</> : ''}</>
          : 'We could not tell what the picture should do.'}</p>
        {missed && data.reading.subject_terms.length > 0 && <p className="mono">Words it looked for: {data.reading.subject_terms.join(', ')}</p>}
        <GoalChoice chosen={chosen} read={data.reading.goals.map((g) => g.id).filter((g) => !chosen.includes(g))} choose={choose} missed={missed} />
        {data.route.system && data.layers['design-system'].length > 0 && <p className="mono">Design system: {data.route.system.name}. {data.route.system.why}.</p>}
        {available.length > 1 && <div className="row layer-toggles" role="group" aria-label="Where to look">
          {available.map((layer) => <label key={layer} className="choice plain"><input type="checkbox" checked={!off.includes(layer)}
            onChange={() => toggle(layer)} />{LAYER_NAMES[layer]}</label>)}
        </div>}
      </section>
      {!ways ? <div className="section" style={{ marginTop: 40 }}><Loading plates={false} label="Finding ways to do it…" /></div>
      : ways.directions.length > 0 ? <section className="section ways" aria-labelledby="ways-title" style={{ marginTop: 40 }}>
        <div className="section-title">
          <h2 id="ways-title">Ways to do it</h2>
          <p className="mono">One technique each, with pictures that show it</p>
        </div>
        <ol className="ways-list">
          {ways.directions.map((way, index) => <li key={way.technique.id} className={`way ${['rule-blue', 'rule-green', 'rule-ochre'][index % 3]}`}>
            <div className="way-text">
              <h3><span className="mono way-number">{index + 1}</span><a href={href(`technique/${way.technique.id}`)}>{way.technique.name}</a></h3>
              <div><p className="guide-def">{way.idea}</p>
                {way.serves.length > 0 && <p className="mono">Serves: {way.serves.join(' · ')}</p>}</div>
            </div>
            <RefStrip refs={way.references} from={from} use={use} label={`Pictures that show ${way.technique.name}`} />
            {way.make_sure[0] && <p className="way-first"><span className="mono">Make sure </span>{way.make_sure[0]}</p>}
            <details className="way-how"><summary className="mono">How to carry it out</summary>
              <ul>{way.make_sure.slice(1, 3).map((cue) => <li key={cue}>{cue}</li>)}</ul>
              {way.not_to_confuse_with[0] && <p className="muted guide-note">{way.not_to_confuse_with[0]}</p>}
            </details>
          </li>)}
        </ol>
      </section>
      : data.guidance.length > 0 && <section className="section guidance" aria-labelledby="guidance-title" style={{ marginTop: 40 }}>
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
          <h2 id="refs-title">{shown.size ? 'More references' : missed && strong.length === 0 ? 'Meanwhile' : 'References'}</h2>
          <p className="mono">{rest.length && !(missed && strong.length === 0) ? `${rest.length}${shown.size ? ' more' : ''} of ${data.total_matches} matches` : ''}
            {use === 'publish' ? ' · free to publish with credit' : ''}</p>
        </div>
        {missed && strong.length === 0 && shown.size === 0 ? <>
          {weak.length > 0 && <><p className="mono">Only these share your words, not a technique:</p>
            <Plates refs={weak} from={from} use={use} small /></>}</>
        : data.results.length === 0 ? <Empty title="Nothing in the atlas fits yet" actions={<a className="button primary"
          href={href('find', { goal: data.reading.subject_terms.join(' ') })}>Find new images</a>}>
          Try other words, say what the picture should do (stand out, feel calm, show scale), or find new images from open collections.</Empty>
          : shown.size > 0 ? <details className="more-refs" open={moreOpen} onToggle={(event) => setMoreOpen(event.currentTarget.open)}><summary>See {rest.length} more pictures that match</summary>
            {strong.length > 0 && <><p className="mono marks-key">● confirmed by you · ◐ agreed by a second model · ○ proposed by a model{strong.some((ref) => ref.generated) ? ' · ◇ intended in a generated example' : ''}</p>
              <Plates refs={strong} from={from} use={use} /></>}
            {weak.length > 0 && <><h3 className="weak-title mono">Matched only on words, not on a technique</h3><Plates refs={weak} from={from} use={use} small /></>}
            {more && <div className="row" style={{ marginTop: 32 }}><button type="button" onClick={more}>Show more references</button></div>}
          </details>
          : <>
            {strong.length > 0 && <><p className="mono marks-key">● confirmed by you · ◐ agreed by a second model · ○ proposed by a model{strong.some((ref) => ref.generated) ? ' · ◇ intended in a generated example' : ''}</p>
              <Plates refs={strong} from={from} use={use} /></>}
            {weak.length > 0 && (strong.length + shown.size >= 3
              ? <details className="weak"><summary className="mono">{weak.length} more matched only on words, not on a technique</summary>
                <Plates refs={weak} from={from} use={use} small /></details>
              : <><h3 className="weak-title mono">Matched only on words, not on a technique</h3><Plates refs={weak} from={from} use={use} small /></>)}
          </>}
        {more && !shown.size && <div className="row" style={{ marginTop: 32 }}><button type="button" onClick={more}>Show more references</button></div>}
      </section>
      <nav className="section next-steps" aria-label="Next steps" style={{ marginTop: 48 }}>
        {missed && strong.length === 0
          ? <><a className="button primary" href={href('find', { goal: asked })}>Find images for this brief</a>
            <a className="button" href={href('project', { text: asked })}>Start a project from this brief</a></>
          : <><a className="button primary" href={href('project', { text: asked })}>Start a project from this brief</a>
            <a className="button" href={href('find', { goal: asked })}>Find more images for this brief</a></>}
      </nav>
      <p className="muted" style={{ marginTop: 40, maxWidth: 760, fontSize: 14, lineHeight: 1.5 }}>{data.note}</p>
    </>
  )
}

/** The brief part of a generation prompt: what was asked for, without the instructions to the tool. */
function briefOf(prompt: string): string {
  const start = prompt.indexOf('BRIEF\n')
  return (start >= 0 ? prompt.slice(start + 6) : prompt).trim()
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
      <div className="crumbs">{back ? <a href={back}>← Back to your answer</a> : <a href="#/ask">← Ask the atlas</a>}</div>
      <div className="image-head">
        <figure className="figure" style={{ aspectRatio: aspect(r) }}><RefImage src={r.image} alt={r.title} /></figure>
        <div className="image-title">
          <p className="kicker">{layerLabel(r)}</p>
          <h1>{r.title}</h1>
          {r.generated ? <p className="muted">Made with an image model{r.date ? ` · ${shortDate(r.date)}` : ''}</p>
            : r.creator && <p className="muted">{r.creator}{r.date ? `, ${shortDate(r.date)}` : ''}</p>}
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
          {r.prompt && <><p className="mono" style={{ marginTop: 14 }}>Brief given to the image model</p>
            <p className="slip-text" style={{ whiteSpace: 'pre-line' }}>{briefOf(r.prompt)}</p>
            <details style={{ marginTop: 8 }}><summary className="mono">Full prompt, with the tool instructions</summary>
              <p className="slip-text" style={{ whiteSpace: 'pre-line', fontSize: 13 }}>{r.prompt}</p></details></>}
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
      <MoreLikeThis refId={r.ref} from={window.location.hash} use={route.query.get('use') ?? 'reference'} />
    </>
  )
}
