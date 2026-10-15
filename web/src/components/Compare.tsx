import { useState } from 'react'
import { media, post, readOnly, request } from '../lib/client'
import { useApp, useData } from '../lib/hooks'
import { go, href } from '../lib/router'
import type { ImageDetail, Job, Settings, State } from '../lib/types'
import JobProgress from './JobProgress'
import { Empty, Failure, Loading, PageHead, useNotice } from './ui'

interface Saved { shared: string[]; differences: string[]; per_image: { image_id: number; note: string }[]
  technique_notes: { technique_id: string; comment: string }[]; backend: string; model: string; model_version: string | null }

const MARK: Record<State, string> = { model_reviewed: '■', human_reviewed: '●', proposed: '□', rejected: '×' }

export default function Compare({ ids }: { ids: number[] }) {
  const { taxonomy, clearCompare, toggleCompare } = useApp()
  const { fail } = useNotice()
  const valid = ids.slice(0, 4)
  const { data, error, busy, reload } = useData<{ images: ImageDetail[]; comparison: Saved | null }>(valid.length ? `compare?ids=${valid.join(',')}` : null)
  const [jobId, setJobId] = useState<string | null>(null)
  if (valid.length < 2) return <><PageHead kicker="Compare · two to four images" title="Compare" />
    <Empty title="Choose at least two images" actions={<a className="button primary" href="#/">Go to the library</a>}>Use “+ Compare” on any picture in the library, then come back here.</Empty></>
  if (error) return <><PageHead kicker="Compare" title="Compare" /><Failure message={error} busy={busy} retry={reload} /></>
  if (!data) return <><PageHead kicker="Compare" title="Compare" /><Loading /></>
  const used = taxonomy?.techniques.filter((t) => data.images.some((d) => d.annotations.some((a) => a.technique_id === t.id && a.state !== 'rejected'))) ?? []
  const shared = used.filter((t) => data.images.every((d) => d.annotations.some((a) => a.technique_id === t.id && a.state !== 'rejected')))
  async function ask() {
    try {
      const settings = await request<Settings>('settings')
      const job = await post<Job>('jobs', { kind: 'compare', spec: { image_ids: valid, backend: settings.backend } })
      setJobId(job.id)
    } catch (reason) { fail(reason) }
  }
  function drop(imageId: number, title: string) {
    toggleCompare({ id: imageId, title })
    go('compare', { ids: valid.filter((x) => x !== imageId).join(',') })
  }
  const columns = { '--n': data.images.length } as React.CSSProperties
  return (
    <>
      <PageHead kicker={`Compare · ${data.images.length} of up to 4 images`} title="Compare" asideClass="actions"
        aside={<><a className="button" href="#/">Add an image</a><button type="button" onClick={() => { clearCompare(); go('') }}>Clear</button></>} />
      <section className="baseline" aria-label="Images side by side" style={{ ...columns, marginTop: 32 }}>
        {data.images.map((d) => <figure key={d.image.id}><img src={media(d.image.display)} alt={d.image.title} /></figure>)}
      </section>
      <div className="baseline-captions" style={columns}>
        {data.images.map((d) => (
          <div key={d.image.id} className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'nowrap' }}>
            <div>
              <p className="mono">Fig. {d.image.id}</p>
              <h2 style={{ fontSize: 24, lineHeight: 1.1, marginTop: 2 }}><a href={href(`image/${d.image.id}`)}>{d.image.title}</a></h2>
              <p className="muted" style={{ fontSize: 14, marginTop: 2 }}>{[d.image.creator, d.image.date_text].filter(Boolean).join(', ')}{d.rights ? ` · ${d.rights.license_code}` : ''}</p>
              {data.comparison?.per_image.find((n) => n.image_id === d.image.id) && <p style={{ fontSize: 14, marginTop: 8 }}>{data.comparison.per_image.find((n) => n.image_id === d.image.id)!.note}</p>}
            </div>
            <button type="button" className="small" aria-label={`Remove ${d.image.title} from the comparison`} onClick={() => drop(d.image.id, d.image.title)}>×</button>
          </div>))}
      </div>

      <section className="section" aria-labelledby="matrix" style={{ marginTop: 48 }}>
        <h2 id="matrix">Techniques</h2>
        <p className="mono" style={{ margin: '8px 0 12px' }}>■ agreed by a second model · ● confirmed by you · □ proposed · — not seen{shared.length ? ` · shared by all: ${shared.map((t) => t.name.replace(/ \(.*\)$/, '')).join(', ')}` : ''}</p>
        <div className="scroll-x"><table className="plain">
          <thead><tr><th scope="col" style={{ width: '34%' }}>Technique</th>{data.images.map((d) => <th key={d.image.id} scope="col">Fig. {d.image.id}</th>)}</tr></thead>
          <tbody>
            {used.map((t) => <tr key={t.id}><th scope="row"><a href={href(`technique/${t.id}`)}>{t.name}</a></th>
              {data.images.map((d) => {
                const a = d.annotations.find((x) => x.technique_id === t.id && x.state !== 'rejected')
                return <td key={d.image.id} className="mark" aria-label={a ? a.state.replace('_', ' ') : 'not seen'}>{a ? MARK[a.state] : '—'}</td>
              })}</tr>)}
            <tr><th scope="row" className="mono">Palette</th>
              {data.images.map((d) => <td key={d.image.id}><span className="palette" role="img" aria-label={`Palette: ${d.metrics?.palette.map((p) => p.name).join(', ') ?? 'not measured'}`}>
                {d.metrics?.palette.map((p) => <span key={p.hex} style={{ background: p.hex, flex: `${p.share} 1 0` }} />)}</span></td>)}</tr>
            <tr><th scope="row" className="mono">Shape · contrast · colourfulness</th>
              {data.images.map((d) => <td key={d.image.id} className="mono" style={{ color: 'var(--ink)' }}>{d.metrics ? `${d.metrics.orientation} · ${Math.round(d.metrics.contrast)} · ${Math.round(d.metrics.colorfulness)}` : '—'}</td>)}</tr>
          </tbody>
        </table></div>
      </section>

      <section className="section split" aria-labelledby="reading" style={{ marginTop: 48 }}>
        {data.comparison ? <div className="main-col slip">
          <div className="section-title"><h2 id="reading" style={{ fontSize: 28 }}>What they share, what differs</h2>
            <span className="mono">Saved comparison · {data.comparison.backend} ({data.comparison.model_version ?? data.comparison.model})</span></div>
          <div className="trays" style={{ marginTop: 16, gap: 24 }}>
            <div className="tray-col rule-green"><h3>In common</h3><ul>{data.comparison.shared.map((s) => <li key={s}><span>{s}</span></li>)}</ul></div>
            <div className="tray-col rule-rust"><h3>Differences</h3><ul>{data.comparison.differences.map((s) => <li key={s}><span>{s}</span></li>)}</ul></div>
          </div>
          {data.comparison.technique_notes.length > 0 && <ul style={{ marginTop: 16, fontSize: 15 }}>{data.comparison.technique_notes.map((n) =>
            <li key={n.technique_id}><strong>{taxonomy?.techniques.find((t) => t.id === n.technique_id)?.name}:</strong> {n.comment}</li>)}</ul>}
        </div> : <div className="main-col"><h2 id="reading" style={{ fontSize: 28 }}>No written comparison yet</h2>
          <p className="muted" style={{ marginTop: 8 }}>An assistant can write what these share and how they differ. It is saved, so it is asked only once.</p></div>}
        <div className="side-col stack" style={{ alignItems: 'flex-start' }}>
          {!readOnly && !data.comparison && <button type="button" className="primary" onClick={ask}>Ask an assistant to compare them</button>}
          {jobId && <div className="slip" style={{ width: '100%' }}><JobProgress jobId={jobId} compact />
            <button type="button" style={{ marginTop: 12 }} onClick={() => { setJobId(null); reload() }}>Show the comparison</button></div>}
          <p className="mono">One AI call. Browsing and the matrix above never call a model.</p>
        </div>
      </section>
    </>
  )
}
