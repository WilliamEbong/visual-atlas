import { useState } from 'react'
import { del, media, post, put, readOnly, request } from '../lib/client'
import { date, useData } from '../lib/hooks'
import { go, href } from '../lib/router'
import type { Brief, Job, Settings } from '../lib/types'
import JobProgress from './JobProgress'

export default function Project({ id }: { id?: number }) {
  const list = useData<Brief[]>('briefs')
  if (id) return <BriefPage id={id} onChange={list.reload} />
  return (
    <div className="split">
      <section className="main-col stack">
        <h1>Help with my project</h1>
        <p className="lede">Describe a project. The atlas suggests a few visual directions, each built on techniques and on images already in your library, with how to execute them and what to watch out for.</p>
        {readOnly ? <p className="notice">Suggestions need the downloaded app.</p> : <BriefForm onSaved={(briefId) => { list.reload(); go(`project/${briefId}`) }} />}
      </section>
      <aside className="side-col panel stack">
        <h2>Your briefs</h2>
        {list.data?.length ? <ul>{list.data.map((b) => <li key={b.id}><a href={href(`project/${b.id}`)}>{b.title}</a> <span className="mono">{date(b.updated_at)}</span></li>)}</ul>
          : <p className="muted">None yet. Briefs and their suggestions are saved, so reopening one costs nothing.</p>}
      </aside>
    </div>
  )
}

function BriefForm({ brief, onSaved }: { brief?: Brief; onSaved: (id: number) => void }) {
  const [title, setTitle] = useState(brief?.title ?? '')
  const [text, setText] = useState(brief?.text ?? '')
  const [error, setError] = useState<string | null>(null)
  async function save(event: React.FormEvent) {
    event.preventDefault()
    try {
      if (brief) { await put(`briefs/${brief.id}`, { title, text }); onSaved(brief.id) }
      else onSaved((await post<{ id: number }>('briefs', { title, text })).id)
    } catch (reason) { setError((reason as Error).message) }
  }
  return (
    <form className="stack" onSubmit={save}>
      <label className="field">Project name<input required maxLength={120} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Solitude talk — poster" /></label>
      <label className="field">The brief: audience, message, format, mood, constraints
        <textarea required rows={6} maxLength={4000} value={text} onChange={(e) => setText(e.target.value)}
          placeholder="A poster for a public talk about solitude and attention. Calm, a little melancholy, not lonely-sad. A2 portrait, title at the top, lots of room for text." /></label>
      {error && <p className="notice error" role="alert">{error}</p>}
      <div className="row"><button type="submit" className="primary">{brief ? 'Save brief' : 'Save and continue'}</button></div>
    </form>
  )
}

function BriefPage({ id, onChange }: { id: number; onChange: () => void }) {
  const { data, error, reload } = useData<Brief>(`briefs/${id}`)
  const [jobId, setJobId] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  if (error) return <p className="notice error" role="alert">{error}</p>
  if (!data) return <p className="mono">Loading…</p>
  async function suggest() {
    try {
      const settings = await request<Settings>('settings')
      const job = await post<Job>('jobs', { kind: 'directions', spec: { brief_id: id, backend: settings.backend } })
      setJobId(job.id)
    } catch (reason) { setMessage((reason as Error).message) }
  }
  async function setState(directionId: number, state: string) {
    await post(`directions/${directionId}`, { state }); reload()
  }
  const kept = data.directions?.filter((d) => d.state === 'kept') ?? []
  const proposed = data.directions?.filter((d) => d.state === 'proposed') ?? []
  return (
    <div className="stack">
      <p><a href="#/project">← All briefs</a></p>
      <div className="page-head"><h1>{data.title}</h1>
        {!readOnly && <div className="row"><button type="button" onClick={() => setEditing(!editing)}>{editing ? 'Close' : 'Edit brief'}</button>
          <button type="button" className="quiet" onClick={async () => { await del(`briefs/${id}`); onChange(); go('project') }}>Delete</button></div>}</div>
      {editing ? <BriefForm brief={data} onSaved={() => { setEditing(false); reload(); onChange() }} /> : <p className="lede" style={{ whiteSpace: 'pre-line' }}>{data.text}</p>}
      {data.reading && <p className="mono" aria-label="How the brief was read">Read as: {[
        ...data.reading.goals.map((g) => g.name), ...data.reading.techniques.map((t) => t.name + (t.exact ? '' : ' (maybe)')),
        ...data.reading.subject_terms].join(' · ') || 'no techniques or goals named; directions will lean on subject words and recent references'}</p>}
      {message && <p className="notice error" role="alert">{message}</p>}
      {!readOnly && <div className="row"><button type="button" className="primary" onClick={suggest}>{proposed.length || kept.length ? 'Suggest new directions' : 'Suggest directions'}</button>
        <span className="mono">Suggestions cite only images and techniques in your library. Kept directions stay when you ask again.</span></div>}
      {jobId && <div className="notice"><JobProgress jobId={jobId} compact /><button type="button" onClick={() => { setJobId(null); reload() }}>Show the results</button></div>}
      <hr className="horizon" />
      {data.directions?.length === 0 && <p className="muted">No suggestions yet.</p>}
      <div className="compare-grid">
        {[...kept, ...proposed].map((d, index) => (
          <article key={d.id} className={`technique-card ${d.state === 'kept' ? 'primary' : ''}`}>
            <span className="mono">Direction {index + 1}{d.state === 'kept' ? ' · kept' : ''}</span>
            <h2>{d.title}</h2>
            <p>{d.idea}</p>
            <p className="muted"><strong>Why it suits the brief:</strong> {d.rationale}</p>
            <p style={{ color: 'var(--accent)' }}>{d.techniques.map((t, i) => <span key={t.id}>{i ? ' · ' : ''}<a href={href(`technique/${t.id}`)}>{t.name}</a></span>)}</p>
            {d.images.length > 0 ? <div className="thumbs">{d.images.map((img) => <a key={img.id} href={href(`image/${img.id}`)}><div className="frame"><img src={media(img.thumb)} alt={img.title} /></div></a>)}</div>
              : <p className="mono">No reference in your library yet — try Find images for this direction.</p>}
            <h3>How to do it</h3><ul>{d.execution.map((e) => <li key={e}>{e}</li>)}</ul>
            <h3>Tradeoffs</h3><ul>{d.tradeoffs.map((e) => <li key={e}>{e}</li>)}</ul>
            <p className="mono">Suggested by {d.backend} ({d.model_version ?? d.model})</p>
            {!readOnly && <div className="row">{d.state !== 'kept' && <button type="button" onClick={() => setState(d.id, 'kept')}>Keep</button>}
              <button type="button" onClick={() => setState(d.id, 'dismissed')}>Dismiss</button>
              {d.images.length > 0 && <a className="button" href={href('compare', { ids: d.images.slice(0, 4).map((i) => i.id).join(',') })}>Compare references</a>}</div>}
          </article>))}
      </div>
    </div>
  )
}
