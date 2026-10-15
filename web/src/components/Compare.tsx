import { useState } from 'react'
import { media, post, readOnly, request } from '../lib/client'
import { useApp, useData } from '../lib/hooks'
import { href } from '../lib/router'
import type { ImageDetail, Job, Settings } from '../lib/types'
import { STATE_LABEL } from '../lib/types'
import JobProgress from './JobProgress'

interface Saved { shared: string[]; differences: string[]; per_image: { image_id: number; note: string }[]
  technique_notes: { technique_id: string; comment: string }[]; backend: string; model: string; model_version: string | null }

export default function Compare({ ids }: { ids: number[] }) {
  const { taxonomy, clearCompare } = useApp()
  const valid = ids.slice(0, 4)
  const { data, error, reload } = useData<{ images: ImageDetail[]; comparison: Saved | null }>(valid.length ? `compare?ids=${valid.join(',')}` : null)
  const [jobId, setJobId] = useState<string | null>(null)
  if (valid.length < 2) return <div className="empty"><h1>Compare</h1><p>Choose two to four images with “+ Compare” in the library, then come back here.</p><a className="button" href="#/">Go to the library</a></div>
  if (error) return <p className="notice error" role="alert">{error}</p>
  if (!data) return <p className="mono">Loading…</p>
  const shared = taxonomy?.techniques.filter((t) => data.images.every((d) => d.annotations.some((a) => a.technique_id === t.id && a.state !== 'rejected'))) ?? []
  async function ask() {
    const settings = await request<Settings>('settings')
    const job = await post<Job>('jobs', { kind: 'compare', spec: { image_ids: valid, backend: settings.backend } })
    setJobId(job.id)
  }
  return (
    <div className="stack">
      <div className="page-head"><h1>Compare</h1><button type="button" className="quiet" onClick={clearCompare}>Clear selection</button></div>
      <p className="muted">Shared techniques: {shared.length ? shared.map((t, i) => <span key={t.id}>{i ? ', ' : ''}<a href={href(`technique/${t.id}`)}>{t.name}</a></span>) : 'none recorded in all of them'}.</p>
      <div className="compare-grid">
        {data.images.map((d) => (
          <section key={d.image.id} className="stack" aria-label={d.image.title}>
            <div className="hero" style={{ minHeight: 200 }}><img src={media(d.image.display)} alt={d.image.title} style={{ maxHeight: 340 }} /></div>
            <h2 style={{ fontSize: 22 }}><a href={href(`image/${d.image.id}`)}>{d.image.title}</a></h2>
            <p className="mono">{[d.image.creator, d.image.date_text].filter(Boolean).join(', ')} · {d.metrics?.orientation} · {d.metrics?.color_family} · contrast {Math.round(d.metrics?.contrast ?? 0)}</p>
            <ul>{d.annotations.filter((a) => a.state !== 'rejected').map((a) => <li key={a.technique_id}>{shared.some((s) => s.id === a.technique_id) ? <strong>{a.name}</strong> : a.name} <span className={`state ${a.state}`}>{STATE_LABEL[a.state]}</span></li>)}</ul>
            {data.comparison?.per_image.find((n) => n.image_id === d.image.id) && <p className="notice">{data.comparison.per_image.find((n) => n.image_id === d.image.id)!.note}</p>}
          </section>))}
      </div>
      <hr className="horizon" />
      {data.comparison ? <section className="stack">
        <h2>How they compare</h2>
        <div className="split"><div className="main-col"><h3>In common</h3><ul>{data.comparison.shared.map((s) => <li key={s}>{s}</li>)}</ul></div>
          <div className="side-col"><h3>Differences</h3><ul>{data.comparison.differences.map((s) => <li key={s}>{s}</li>)}</ul></div></div>
        {data.comparison.technique_notes.length > 0 && <ul>{data.comparison.technique_notes.map((n) => <li key={n.technique_id}><strong>{taxonomy?.techniques.find((t) => t.id === n.technique_id)?.name}:</strong> {n.comment}</li>)}</ul>}
        <p className="mono">Written by {data.comparison.backend} ({data.comparison.model_version ?? data.comparison.model}); saved, so it is not asked again.</p>
      </section> : !readOnly && <p><button type="button" className="primary" onClick={ask}>Ask an assistant to compare them</button> <span className="mono">Optional. Saved once written.</span></p>}
      {jobId && <div className="notice"><JobProgress jobId={jobId} compact /><button type="button" onClick={() => { setJobId(null); reload() }}>Show the comparison</button></div>}
    </div>
  )
}
