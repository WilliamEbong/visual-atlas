import { useEffect, useState } from 'react'
import { del, media, post, put, readOnly, request } from '../lib/client'
import { date, useData } from '../lib/hooks'
import { go, href } from '../lib/router'
import type { Brief, Job, ReadingCorrection, Settings } from '../lib/types'
import JobProgress from './JobProgress'
import ReadingEditor from './ReadingEditor'
import { Empty, Failure, Loading, PageHead, useNotice } from './ui'

const RULES = ['rule-rust', 'rule-blue', 'rule-green', 'rule-ochre', 'rule-ink']
const THUMB_HEIGHTS = [70, 58, 86, 64, 100]

export default function Project({ id }: { id?: number }) {
  const list = useData<Brief[]>('briefs')
  if (id) return <BriefPage id={id} onChange={list.reload} />
  return (
    <>
      <PageHead kicker="My project · directions grounded in your library" title="Help with my project" />
      <div className="split" style={{ marginTop: 40 }}>
        <section className="main-col stack" aria-labelledby="new-brief">
          <h2 id="new-brief">A new brief</h2>
          <p className="muted">Describe a project. The atlas suggests a few visual directions, each built on techniques and images already in your library, with how to execute them and what to watch out for.</p>
          {readOnly ? <p className="slip">Suggestions need the downloaded app.</p> : <BriefForm onSaved={(briefId) => { list.reload(); go(`project/${briefId}`) }} />}
        </section>
        <aside className="side-col" aria-labelledby="briefs">
          <h2 id="briefs">Your briefs</h2>
          {list.error ? <Failure message={list.error} busy={list.busy} retry={list.reload} /> : !list.data ? <Loading plates={false} />
            : list.data.length === 0 ? <p className="muted" style={{ marginTop: 12 }}>None yet. Briefs and their suggestions are saved, so reopening one costs nothing.</p>
            : <nav className="drawers" aria-label="Your briefs" style={{ gridTemplateColumns: '1fr', marginTop: 16 }}>
              {list.data.map((b, index) => <a key={b.id} className="drawer" href={href(`project/${b.id}`)}>
                <span className="letter" aria-hidden="true">{index + 1}</span>
                <span><strong>{b.title}</strong><span className="text">{b.text.slice(0, 110)}{b.text.length > 110 ? '…' : ''}</span>
                  <span className="mono" style={{ display: 'block', marginTop: 6 }}>{date(b.updated_at)}</span></span></a>)}
            </nav>}
        </aside>
      </div>
    </>
  )
}

function BriefForm({ brief, onSaved, onCancel }: { brief?: Brief; onSaved: (id: number) => void; onCancel?: () => void }) {
  const [title, setTitle] = useState(brief?.title ?? '')
  const [text, setText] = useState(brief?.text ?? '')
  const { fail } = useNotice()
  async function save(event: React.FormEvent) {
    event.preventDefault()
    try {
      if (brief) { await put(`briefs/${brief.id}`, { title, text }); onSaved(brief.id) }
      else onSaved((await post<{ id: number }>('briefs', { title, text })).id)
    } catch (reason) { fail(reason) }
  }
  return (
    <form className="stack slip" onSubmit={save}>
      <label className="field">Project name<input required maxLength={120} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Solitude talk — poster" /></label>
      <label className="field">The brief: audience, message, format, mood, constraints
        <textarea required rows={6} maxLength={4000} value={text} onChange={(e) => setText(e.target.value)} style={{ fontFamily: 'var(--mono)' }}
          placeholder="A poster for a public talk about solitude and attention. Calm, a little melancholy, not lonely-sad. A2 portrait, title at the top, lots of room for text." /></label>
      <div className="row"><button type="submit" className="primary">{brief ? 'Save brief' : 'Save and continue'}</button>
        {onCancel && <button type="button" onClick={onCancel}>Cancel</button>}</div>
    </form>
  )
}

function BriefPage({ id, onChange }: { id: number; onChange: () => void }) {
  const { data, error, busy, reload } = useData<Brief>(`briefs/${id}`)
  const { notify, fail, confirm } = useNotice()
  const [jobId, setJobId] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [correction, setCorrection] = useState<ReadingCorrection | null>(null)
  useEffect(() => { setCorrection(null) }, [id, data?.text, data?.title])
  if (error) return <><PageHead kicker={<a href="#/project">All briefs</a>} title="Brief" /><Failure message={error} busy={busy} retry={reload} /></>
  if (!data) return <><PageHead kicker={<a href="#/project">All briefs</a>} title="…" /><Loading plates={false} /></>
  async function suggest() {
    try {
      const settings = await request<Settings>('settings')
      const job = await post<Job>('jobs', { kind: 'directions', spec: { brief_id: id, backend: settings.backend,
        reading_correction: correction } })
      setJobId(job.id)
    } catch (reason) { fail(reason) }
  }
  async function setState(directionId: number, state: string, title: string, previous: string) {
    try {
      await post(`directions/${directionId}`, { state }); reload()
      notify(state === 'dismissed' ? `Dismissed “${title}”.` : `Kept “${title}”.`, { undo: async () => { await post(`directions/${directionId}`, { state: previous }); reload() } })
    } catch (reason) { fail(reason) }
  }
  async function remove() {
    const sure = await confirm({ title: 'Delete this brief?', danger: true, confirm: 'Delete',
      body: 'The brief and its suggested directions are deleted. Images in your library stay. This cannot be undone.' })
    if (!sure) return
    try { await del(`briefs/${id}`); onChange(); notify(`Deleted “${data!.title}”.`); go('project') } catch (reason) { fail(reason) }
  }
  const kept = data.directions?.filter((d) => d.state === 'kept') ?? []
  const proposed = data.directions?.filter((d) => d.state === 'proposed') ?? []
  const directions = [...kept, ...proposed]
  const reading = data.reading
  return (
    <>
      <PageHead kicker={<><a href="#/project">All briefs</a> / written {date(data.created_at)}</>} title={data.title} asideClass="actions"
        aside={!readOnly && <><button type="button" onClick={() => setEditing(!editing)}>{editing ? 'Close' : 'Edit brief'}</button>
          <button type="button" className="primary" onClick={suggest}>{directions.length ? 'Suggest new directions' : 'Suggest directions'}</button></>} />
      <div className="split under" style={{ gap: 40 }}>
        <div className="main-col" style={{ flex: '1 1 420px' }}>
          {editing ? <BriefForm brief={data} onSaved={() => { setEditing(false); reload(); onChange(); notify('Brief saved.') }} onCancel={() => setEditing(false)} />
            : <div className="slip"><p className="mono" style={{ marginBottom: 8 }}>The brief</p><p className="slip-text">{data.text}</p></div>}
        </div>
        {reading && <div className="side-col" aria-label="How the brief was read">
          <ReadingEditor reading={reading} value={correction} onChange={setCorrection} />
        </div>}
      </div>
      <p className="mono" style={{ marginTop: 14 }}>These suggestions rank references without requiring every image to match. Subject matches keep a place too. Suggest directions uses AI and sends your full original brief with the selected references. Corrections apply to this run; editing the brief resets them.</p>
      {jobId && <div className="slip" style={{ marginTop: 24 }}><JobProgress jobId={jobId} compact />
        <button type="button" style={{ marginTop: 12 }} onClick={() => { setJobId(null); reload() }}>Show the results</button></div>}

      <section className="section" aria-labelledby="directions">
        <div className="section-title"><h2 id="directions">{directions.length ? `${directions.length} direction${directions.length === 1 ? '' : 's'}` : 'Directions'}</h2>
          <span className="mono">Cite only images and techniques in your library · kept directions stay when you ask again</span></div>
        {directions.length === 0 ? <Empty title={data.directions ? 'No suggestions yet' : 'Your library can’t support directions yet'}
          actions={!readOnly && <><button type="button" className="primary" onClick={suggest}>Suggest directions</button>
            <a className="button" href={href('find', { goal: data.text.slice(0, 200) })}>Find images for this brief</a></>}>
            Ask for directions. If your library lacks examples of what the brief needs, the atlas says so instead of inventing them.</Empty>
          : <div className="trays" style={{ marginTop: 22, gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 24 }}>
            {directions.map((d, index) => (
              <article key={d.id} className={`tray-col ${RULES[index % RULES.length]}`} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <p className="mono">Direction {index + 1}{d.state === 'kept' ? ' · kept' : ''}</p>
                <h3 className="direction-title">{d.title}</h3>
                {d.images.length > 0 ? <div className="contact" style={{ height: 104, gap: 8 }}>
                  {d.images.slice(0, 3).map((img, i) => <a key={img.id} href={href(`image/${img.id}`)} aria-label={img.title}>
                    <img src={media(img.thumb)} alt="" style={{ height: THUMB_HEIGHTS[i] }} /></a>)}</div>
                  : <p className="mono">No reference in your library yet — try Find images for this direction.</p>}
                <p style={{ fontSize: 15 }}>{d.idea}</p>
                <p style={{ fontSize: 14 }} className="muted"><span className="label" style={{ fontSize: 14, color: 'var(--ink)' }}>Why it suits the brief </span>{d.rationale}</p>
                <p className="mono">{d.techniques.map((t, i) => <span key={t.id}>{i ? ' · ' : ''}<a href={href(`technique/${t.id}`)}>{t.name.replace(/ \(.*\)$/, '')}</a></span>)}</p>
                <details><summary>How to do it, and tradeoffs</summary>
                  <ul style={{ fontSize: 14, paddingLeft: 18 }}>{d.execution.map((e) => <li key={e}>{e}</li>)}</ul>
                  <p className="mono" style={{ marginTop: 8 }}>Tradeoffs</p>
                  <ul style={{ fontSize: 14, paddingLeft: 18 }}>{d.tradeoffs.map((e) => <li key={e}>{e}</li>)}</ul>
                </details>
                <p className="mono">Suggested by {d.backend} ({d.model_version ?? d.model})</p>
                {!readOnly && <div className="row" style={{ marginTop: 'auto' }}>
                  {d.state !== 'kept' && <button type="button" className="small" onClick={() => setState(d.id, 'kept', d.title, d.state)}>Keep</button>}
                  <button type="button" className="quiet small" onClick={() => setState(d.id, 'dismissed', d.title, d.state)}>Dismiss</button>
                  {d.images.length > 1 && <a className="quiet small button" href={href('compare', { ids: d.images.slice(0, 4).map((i) => i.id).join(',') })}>Compare</a>}</div>}
              </article>))}
          </div>}
      </section>
      {!readOnly && <p style={{ marginTop: 48 }}><button type="button" className="quiet small" style={{ color: 'var(--danger)' }} onClick={remove}>Delete this brief…</button></p>}
    </>
  )
}
