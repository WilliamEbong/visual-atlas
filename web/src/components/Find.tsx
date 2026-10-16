import { useEffect, useState } from 'react'
import { post, readOnly, request } from '../lib/client'
import { useApp, useData } from '../lib/hooks'
import { useRoute } from '../lib/router'
import type { Job, Reading, ReadingCorrection, Settings } from '../lib/types'
import JobProgress from './JobProgress'
import ReadingEditor from './ReadingEditor'
import { PageHead, useNotice } from './ui'

const COLORS = ['', 'red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'pink', 'brown', 'neutral', 'monochrome']
const ASSISTANTS: [string, string][] = [['codex:claude', 'Codex analyses, Claude Code checks (recommended)'], ['codex:none', 'Codex only'],
  ['claude:codex', 'Claude Code analyses, Codex checks'], ['claude:none', 'Claude Code only'], ['fake:none', 'Practice mode (offline, no real analysis)']]
export interface Source { id: string; name: string; status: string; rule?: string; reason?: string; label?: string; attribution?: string
  evidence_urls: string[]; checked_on: string; notes?: string; default_on?: boolean; setup?: string }

export default function Find() {
  const route = useRoute()
  const { taxonomy } = useApp()
  const { fail } = useNotice()
  const settings = useData<Settings>(readOnly ? null : 'settings')
  const coverage = useData<{ id: string; name: string; examples: number }[]>(readOnly ? null : 'coverage')
  const sources = useData<Source[]>(readOnly ? null : 'sources')
  const [mode, setMode] = useState<'find' | 'grow'>(route.query.get('mode') === 'grow' ? 'grow' : 'find')
  const [goal, setGoal] = useState(route.query.get('goal') ?? '')
  const [goalId, setGoalId] = useState('')
  const [technique, setTechnique] = useState(route.query.get('technique') ?? '')
  const [subject, setSubject] = useState('')
  const [use, setUse] = useState('')
  const [orientation, setOrientation] = useState('')
  const [color, setColor] = useState('')
  const [count, setCount] = useState(6)
  const [providers, setProviders] = useState<string[] | null>(null)
  const [assistant, setAssistant] = useState('codex:claude')
  const [jobId, setJobId] = useState<string | null>(null)
  const [growTechniques, setGrowTechniques] = useState<string[]>([])
  const [reading, setReading] = useState<Reading | null>(null)
  const [correction, setCorrection] = useState<ReadingCorrection | null>(null)
  const [readingFailed, setReadingFailed] = useState(false)
  const enabled = sources.data?.filter((s) => s.status === 'enabled') ?? []
  const chosen = providers ?? enabled.filter((s) => s.default_on !== false).map((s) => s.id)
  useEffect(() => { if (settings.data) setAssistant(`${settings.data.backend}:${settings.data.verify_with}`) }, [settings.data])
  useEffect(() => {
    if (coverage.data && growTechniques.length === 0) setGrowTechniques(coverage.data.slice(0, 4).map((t) => t.id))
  }, [coverage.data, growTechniques.length])
  useEffect(() => {  // how the request reads, refreshed as you type (ordinary code, no AI)
    if (readOnly || mode !== 'find') return
    setReading(null)
    setCorrection(null)
    setReadingFailed(false)
    let live = true  // an answer for words already changed is ignored, whichever order the answers arrive in
    const timer = window.setTimeout(() => {
      const query = new URLSearchParams({ text: `${goal} ${use}`.trim(), subject, technique, goal: goalId })
      request<Reading>(`reading?${query}`).then((value) => { if (live) setReading(value) }).catch(() => { if (live) setReadingFailed(true) })
    }, 300)
    return () => { live = false; window.clearTimeout(timer) }
  }, [goal, subject, use, technique, goalId, mode])
  if (readOnly) return <><PageHead kicker="Find" title="Find images" />
    <div className="slip under" style={{ marginTop: 32 }}><p>Finding and analysing images needs the downloaded app (it uses your own Claude Code or Codex sign-in). <a href="https://github.com/WilliamEbong/visual-atlas/releases/latest">Download Visual Atlas</a>.</p></div></>

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    const [backend, verifier] = assistant.split(':')
    const goalName = taxonomy?.goals.find((g) => g.id === goalId)?.name
    const spec = mode === 'find'
      ? { goal: [goal, goalName ? `Goal: ${goalName}` : ''].filter(Boolean).join('. '), subject, intended_use: use, orientation: orientation || null,
          color: color || null, technique_ids: correction?.technique_ids ?? (technique ? [technique] : []),
          goal_ids: correction?.goal_ids ?? (goalId ? [goalId] : []), reading_correction: correction,
          target_new_images: count, providers: chosen, backend,
          verify_with: verifier === 'none' ? null : verifier }
      : { technique_ids: growTechniques, target_new_images: count, providers: chosen, backend, verify_with: verifier === 'none' ? null : verifier }
    try {
      const job = await post<Job>('jobs', { kind: mode, spec })
      setJobId(job.id)
    } catch (reason) { fail(reason) }
  }

  return (
    <>
      <PageHead kicker="Find · searches open collections · keeps only pictures you may use" title={mode === 'find' ? 'Find images' : 'Grow my library'}
        aside={<ol className="mono" aria-label="What happens" style={{ listStyle: 'none', padding: '0 0 24px', display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <li>1  Search</li><li>2  Check permissions</li><li>3  Analyse</li><li>4  File by technique</li></ol>} />
      <div className="split" style={{ marginTop: 40 }}>
        <form className="main-col slip stack" style={{ gap: 22, padding: 28 }} onSubmit={submit}>
          <fieldset><legend className="sr-only">What to do</legend>
            <div className="segments" role="radiogroup" aria-label="What to do">
              <label className="choice"><input type="radio" name="mode" checked={mode === 'find'} onChange={() => setMode('find')} /> Find images for a request</label>
              <label className="choice"><input type="radio" name="mode" checked={mode === 'grow'} onChange={() => setMode('grow')} /> Fill gaps in technique coverage</label>
            </div>
          </fieldset>
          {mode === 'find' ? <>
            <label className="field"><span className="label" style={{ fontSize: 17, color: 'var(--ink)' }}>Describe what you need</span>
              <textarea rows={3} value={goal} onChange={(event) => setGoal(event.target.value)} style={{ fontFamily: 'var(--mono)', fontSize: 16 }}
                placeholder="a quiet image where one small figure stands alone in a big empty landscape" /></label>
            {readingFailed && <p role="status" className="mono">The automatic reading is unavailable. Choose goals, techniques and subject words below, or continue with your original request.</p>}
            <ReadingEditor reading={reading} value={correction} onChange={setCorrection} />
            <div className="filters">
              <label className="field">Goal<select value={goalId} onChange={(event) => setGoalId(event.target.value)}><option value="">Any</option>
                {taxonomy?.goals.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}</select></label>
              <label className="field">Technique to look for<select value={technique} onChange={(event) => setTechnique(event.target.value)}><option value="">Any</option>
                {taxonomy?.techniques.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</select></label>
            </div>
            <div className="filters">
              <label className="field grow">Subject<input value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="lighthouse, hands, harbour…" /></label>
              <label className="field grow">Intended use<input value={use} onChange={(event) => setUse(event.target.value)} placeholder="poster for a talk, slide background…" /></label>
            </div>
            <div className="filters">
              <fieldset><legend>Shape</legend>
                <div className="segments">{[['', 'Any'], ['landscape', 'Landscape'], ['portrait', 'Portrait'], ['square', 'Square']].map(([value, label]) =>
                  <label key={value} className="choice"><input type="radio" name="orientation" checked={orientation === value} onChange={() => setOrientation(value)} /> {label}</label>)}</div>
              </fieldset>
              <label className="field">Main colour<select value={color} onChange={(event) => setColor(event.target.value)}>
                {COLORS.map((c) => <option key={c} value={c}>{c || 'Any'}</option>)}</select></label>
            </div>
          </> : <fieldset><legend>Techniques to find more examples of (fewest examples first)</legend>
            <div className="row">{coverage.data?.slice(0, 12).map((t) => (
              <label key={t.id} className="choice plain" style={{ minWidth: 240 }}><input type="checkbox" checked={growTechniques.includes(t.id)}
                onChange={(event) => setGrowTechniques(event.target.checked ? [...growTechniques, t.id] : growTechniques.filter((x) => x !== t.id))} />
                {t.name} <span className="mono">{t.examples}</span></label>))}</div>
            <p className="mono" style={{ marginTop: 8 }}>Searches use each technique's curated search hints; no AI is used for planning.</p>
          </fieldset>}
          <div className="filters">
            <label className="field">How many new images<input type="number" min={1} max={40} value={count} onChange={(event) => setCount(Number(event.target.value))} /></label>
            <label className="field grow">Who analyses<select value={assistant} onChange={(event) => setAssistant(event.target.value)}>
              {ASSISTANTS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          </div>
          <fieldset style={{ borderTop: '1px solid var(--keyline)', paddingTop: 16 }}><legend className="label" style={{ color: 'var(--ink)', fontSize: 15 }}>Sources (each item's licence is checked)</legend>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '6px 16px' }}>
              {enabled.map((s) => (
                <label key={s.id} className="choice plain"><input type="checkbox" checked={chosen.includes(s.id)}
                  onChange={(event) => setProviders(event.target.checked ? [...chosen, s.id] : chosen.filter((p) => p !== s.id))} />
                  <span>{s.name} {s.label && <span className="mono" style={{ fontSize: 11 }}>{s.label}</span>}
                    {s.setup && <span className="mono" style={{ display: 'block', fontSize: 11 }}>{s.setup}</span>}</span></label>))}
            </div>
          </fieldset>
          <div className="row" style={{ justifyContent: 'space-between', borderTop: '1px solid var(--keyline)', paddingTop: 18 }}>
            <p className="mono" style={{ color: 'var(--graphite)' }}>Runs in the background; you can keep browsing.{settings.data ? ` Daily AI limit: ${settings.data.daily_ai_cap} calls.` : ''}</p>
            <button type="submit" className="primary" disabled={chosen.length === 0}>{mode === 'find' ? 'Start finding' : 'Grow my library'}</button>
          </div>
        </form>
        <aside className="side-col" aria-label={jobId ? 'Progress' : 'How it works'}>
          {jobId ? <JobProgress jobId={jobId} /> : <div className="trays" style={{ gridTemplateColumns: '1fr' }}>
            <div className="tray-col rule-ink"><h2>How it works</h2>
              <ul>
                <li><strong>Search</strong><span>Your words become a few short searches across open collections.</span></li>
                <li><strong>Check permissions</strong><span>Each result's licence is read in code from the source's own record. Unclear means skipped.</span></li>
                <li><strong>Filter</strong><span>Duplicates, tiny images and near-copies are dropped before any AI is used.</span></li>
                <li><strong>Analyse</strong><span>An assistant describes what it sees and proposes techniques; a second one can check the reading.</span></li>
                <li><strong>File</strong><span>Images are added with honest labels: proposed, agreed by a second model, or confirmed by you.</span></li>
              </ul></div>
          </div>}
        </aside>
      </div>
    </>
  )
}
