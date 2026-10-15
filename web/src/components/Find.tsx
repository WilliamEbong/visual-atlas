import { useEffect, useState } from 'react'
import { post, readOnly } from '../lib/client'
import { useApp, useData } from '../lib/hooks'
import { useRoute } from '../lib/router'
import type { Job, Settings } from '../lib/types'
import { PROVIDERS } from '../lib/types'
import JobProgress from './JobProgress'

const COLORS = ['', 'red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'pink', 'brown', 'neutral', 'monochrome']
const ASSISTANTS: [string, string][] = [['codex:claude', 'Codex analyses, Claude Code checks (recommended)'], ['codex:none', 'Codex only'],
  ['claude:codex', 'Claude Code analyses, Codex checks'], ['claude:none', 'Claude Code only'], ['fake:none', 'Practice mode (offline, no real analysis)']]

export default function Find() {
  const route = useRoute()
  const { taxonomy } = useApp()
  const settings = useData<Settings>(readOnly ? null : 'settings')
  const coverage = useData<{ id: string; name: string; examples: number }[]>(readOnly ? null : 'coverage')
  const [mode, setMode] = useState<'find' | 'grow'>(route.query.get('mode') === 'grow' ? 'grow' : 'find')
  const [goal, setGoal] = useState(route.query.get('goal') ?? '')
  const [goalId, setGoalId] = useState('')
  const [technique, setTechnique] = useState(route.query.get('technique') ?? '')
  const [subject, setSubject] = useState('')
  const [use, setUse] = useState('')
  const [orientation, setOrientation] = useState('')
  const [color, setColor] = useState('')
  const [count, setCount] = useState(6)
  const [providers, setProviders] = useState<string[]>(Object.keys(PROVIDERS))
  const [assistant, setAssistant] = useState('codex:claude')
  const [jobId, setJobId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [growTechniques, setGrowTechniques] = useState<string[]>([])
  useEffect(() => {
    if (settings.data) setAssistant(`${settings.data.backend}:${settings.data.verify_with}`)
  }, [settings.data])
  useEffect(() => {
    if (coverage.data && growTechniques.length === 0) setGrowTechniques(coverage.data.slice(0, 4).map((t) => t.id))
  }, [coverage.data, growTechniques.length])
  if (readOnly) return <div className="empty"><h1>Find images</h1><p>Finding and analysing images needs the downloaded app (it uses your own Claude Code or Codex sign-in). <a href="https://github.com/WilliamEbong/visual-atlas/releases/latest">Download Visual Atlas</a>.</p></div>

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    const [backend, verifier] = assistant.split(':')
    const goalName = taxonomy?.goals.find((g) => g.id === goalId)?.name
    const spec = mode === 'find'
      ? { goal: [goal, goalName ? `Goal: ${goalName}` : ''].filter(Boolean).join('. '), subject, intended_use: use, orientation: orientation || null,
          color: color || null, technique_ids: technique ? [technique] : [], target_new_images: count, providers, backend,
          verify_with: verifier === 'none' ? null : verifier }
      : { technique_ids: growTechniques, target_new_images: count, providers, backend, verify_with: verifier === 'none' ? null : verifier }
    try {
      const job = await post<Job>('jobs', { kind: mode, spec })
      setJobId(job.id)
    } catch (reason) { setError((reason as Error).message) }
  }

  return (
    <div className="split">
      <form className="main-col stack" onSubmit={submit}>
        <h1>{mode === 'find' ? 'Find images' : 'Grow my library'}</h1>
        <div className="row" role="radiogroup" aria-label="What to do">
          <label className="choice"><input type="radio" name="mode" checked={mode === 'find'} onChange={() => setMode('find')} /> Find images for a request</label>
          <label className="choice"><input type="radio" name="mode" checked={mode === 'grow'} onChange={() => setMode('grow')} /> Fill gaps in technique coverage</label>
        </div>
        {mode === 'find' ? <>
          <label className="field">Describe what you want to see
            <textarea rows={3} value={goal} onChange={(event) => setGoal(event.target.value)}
              placeholder="a quiet image where one small figure stands alone in a big empty landscape" /></label>
          <div className="filters">
            <label className="field">Goal<select value={goalId} onChange={(event) => setGoalId(event.target.value)}><option value="">Any</option>
              {taxonomy?.goals.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}</select></label>
            <label className="field">Technique<select value={technique} onChange={(event) => setTechnique(event.target.value)}><option value="">Any</option>
              {taxonomy?.techniques.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</select></label>
            <label className="field grow">Subject<input value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="lighthouse, hands, harbour…" /></label>
            <label className="field grow">Intended use<input value={use} onChange={(event) => setUse(event.target.value)} placeholder="poster for a talk, slide background…" /></label>
          </div>
          <fieldset className="row"><legend>Shape</legend>
            {[['', 'Any'], ['landscape', 'Landscape'], ['portrait', 'Portrait'], ['square', 'Square']].map(([value, label]) =>
              <label key={value} className="choice"><input type="radio" name="orientation" checked={orientation === value} onChange={() => setOrientation(value)} /> {label}</label>)}
          </fieldset>
          <label className="field" style={{ maxWidth: 260 }}>Main colour<select value={color} onChange={(event) => setColor(event.target.value)}>
            {COLORS.map((c) => <option key={c} value={c}>{c || 'Any'}</option>)}</select></label>
        </> : <fieldset className="stack"><legend>Techniques to find more examples of (fewest examples first)</legend>
          <div className="row">{coverage.data?.slice(0, 12).map((t) => (
            <label key={t.id} className="choice"><input type="checkbox" checked={growTechniques.includes(t.id)}
              onChange={(event) => setGrowTechniques(event.target.checked ? [...growTechniques, t.id] : growTechniques.filter((x) => x !== t.id))} />
              {t.name} <span className="mono">{t.examples}</span></label>))}</div>
          <p className="mono">Searches use each technique's curated search hints; no AI is used for planning.</p>
        </fieldset>}
        <div className="filters">
          <label className="field">How many new images<input type="number" min={1} max={40} value={count} onChange={(event) => setCount(Number(event.target.value))} /></label>
          <label className="field grow">Who analyses<select value={assistant} onChange={(event) => setAssistant(event.target.value)}>
            {ASSISTANTS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        </div>
        <fieldset className="row"><legend>Collections searched (each item's licence is checked)</legend>
          {Object.entries(PROVIDERS).map(([id, name]) => (
            <label key={id} className="choice"><input type="checkbox" checked={providers.includes(id)}
              onChange={(event) => setProviders(event.target.checked ? [...providers, id] : providers.filter((p) => p !== id))} /> {name}</label>))}
        </fieldset>
        {error && <p className="notice error" role="alert">{error}</p>}
        <div className="row"><button type="submit" className="primary">{mode === 'find' ? 'Find images' : 'Grow my library'}</button>
          <span className="mono">Runs in the background; you can keep browsing.</span></div>
      </form>
      <aside className="side-col panel">
        {jobId ? <JobProgress jobId={jobId} /> : <div className="stack">
          <h2>How it works</h2>
          <ol className="observations">
            <li>Your words become a few short searches across open collections.</li>
            <li>Each result's licence is checked in code against the museum's own record. Unclear means skipped.</li>
            <li>Duplicates, tiny images and near-copies are filtered out before any AI is used.</li>
            <li>An assistant describes what it sees and proposes techniques; a second one can check the reading.</li>
            <li>Only images with a clear technique are added, labelled honestly as proposed or checked.</li>
          </ol>
        </div>}
      </aside>
    </div>
  )
}
