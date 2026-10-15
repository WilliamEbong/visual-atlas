import { useEffect, useState } from 'react'
import { del, media, post, readOnly, request } from '../lib/client'
import { date, useApp, useData } from '../lib/hooks'
import { go, href } from '../lib/router'
import type { Annotation, Collection, ImageDetail, Settings } from '../lib/types'
import { PROVIDERS, STATE_LABEL } from '../lib/types'

function backendName(name: string) {
  return { codex: 'Codex', claude: 'Claude Code', fake: 'Practice mode (no model)' }[name] ?? name
}

function who(changedBy: string) {
  if (changedBy === 'human') return 'you'
  const [, rest = changedBy] = changedBy.split(':')
  const [backend, model] = rest.split('/')
  return `${backendName(backend)}${model ? ` (${model})` : ''}`
}

export default function ImagePage({ id }: { id: number }) {
  const { data, error, reload, setData } = useData<ImageDetail>(`images/${id}`)
  const { taxonomy, compare, toggleCompare } = useApp()
  const [message, setMessage] = useState<string | null>(null)
  const [editing, setEditing] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  useEffect(() => { if (data) document.title = `${data.image.title} · Visual Atlas` }, [data])
  if (error) return <div className="empty"><h1>Not found</h1><p className="notice error" role="alert">{error}</p><a href="#/">Back to the library</a></div>
  if (!data) return <p className="mono" aria-live="polite">Loading…</p>
  const { image, rights, metrics, analysis } = data
  const picked = compare.some((p) => p.id === image.id)

  async function act<T>(work: () => Promise<T>, done?: string) {
    try { const result = await work(); if (done) setMessage(done); return result } catch (reason) { setMessage((reason as Error).message) }
  }
  async function decide(annotation: Pick<Annotation, 'technique_id'>, state: 'human_reviewed' | 'rejected', extra: Record<string, unknown> = {}) {
    const updated = await act(() => post<ImageDetail>(`images/${id}/annotations`, { technique_id: annotation.technique_id, state, ...extra }),
      state === 'rejected' ? 'Marked as rejected. Your decision is kept even if the image is analysed again.' : 'Saved as confirmed by you.')
    if (updated) { setData(updated); setEditing(null); setAdding(false) }
  }
  async function startJob(kind: 'analyze' | 'verify') {
    const settings = await act(() => request<Settings>('settings'))
    const backend = kind === 'verify' ? (settings?.verify_with === 'none' ? 'claude' : settings?.verify_with) : settings?.backend
    const job = await act(() => post<{ id: string }>('jobs', { kind, spec: { image_ids: [id], backend } }))
    if (job) go(`jobs/${job.id}`)
  }

  return (
    <div className="split">
      <section className="main-col stack">
        <div className="hero"><img src={media(image.display)} alt={`${image.title}${image.creator ? ` by ${image.creator}` : ''}`} /></div>
        <p className="mono">Fig. {image.id} · {image.width} × {image.height} px{metrics ? ` · ${metrics.orientation} · mostly ${metrics.color_family}` : ''}
          {image.original && !readOnly && <> · <a href={media(image.original)} target="_blank" rel="noreferrer">open original file</a></>}</p>
        {metrics && <div className="palette" role="img" aria-label={`Measured palette: ${metrics.palette.map((p) => p.name).join(', ')}`}>
          {metrics.palette.map((swatch) => <span key={swatch.hex} title={`${swatch.name} ${Math.round(swatch.share * 100)}%`}
            style={{ background: swatch.hex, width: Math.max(12, swatch.share * 240), height: 18 }} />)}</div>}

        <h2 style={{ marginTop: 18 }}>What you can see</h2>
        {analysis ? (
          <>
            <ol className="observations">
              {analysis.observations.map((o) => <li key={o.id}>{o.text} <span className="mono">{o.region}</span></li>)}
            </ol>
            {analysis.ambiguities.length > 0 && <p className="muted"><strong>Left open:</strong> {analysis.ambiguities.join(' ')}</p>}
            <p className="mono">Described by {backendName(analysis.backend)} ({analysis.model}) on {date(analysis.created_at)}.
              Observations are a model's description of the pixels, not a catalogue record.{analysis.subjects.length ? ` Subjects: ${analysis.subjects.join(', ')}.` : ''}</p>
            {analysis.creator_intent && <p><strong>Documented intent</strong> (from the source's {analysis.creator_intent.metadata_field} field): {analysis.creator_intent.statement}</p>}
          </>
        ) : <p className="muted">Not analysed yet.{!readOnly && <> <button type="button" onClick={() => startJob('analyze')}>Analyse this image</button></>}</p>}

        {data.related.length > 0 && <>
          <h2 style={{ marginTop: 18 }}>Related images</h2>
          <div className="thumbs">
            {data.related.map((r) => (
              <a key={r.id} href={href(`image/${r.id}`)}>
                <div className="frame"><img src={media(r.thumb)} alt={r.title} loading="lazy" /></div>
                <span>{r.title}</span>
                <span className="mono">shares {r.via.map((t) => taxonomy?.techniques.find((x) => x.id === t)?.name ?? t).slice(0, 2).join(', ')}</span>
              </a>
            ))}
          </div>
        </>}
      </section>

      <aside className="side-col stack">
        <div>
          <h1 style={{ fontSize: 'clamp(30px, 4vw, 44px)' }}>{image.title}</h1>
          <p className="muted" style={{ marginTop: 8 }}>{[image.creator || 'Unknown maker', image.date_text, image.medium].filter(Boolean).join(' · ')}</p>
          <p className="mono">{PROVIDERS[image.provider] ?? image.provider}</p>
        </div>
        {message && <p className="notice" role="status">{message}</p>}
        <div className="row">
          {!readOnly && <SaveToCollection imageId={image.id} member={data.collections} onDone={(text) => { setMessage(text); reload() }} />}
          <button type="button" aria-pressed={picked} onClick={() => toggleCompare({ id: image.id, title: image.title, thumb: image.thumb })}>{picked ? '✓ In comparison' : 'Compare'}</button>
          {!readOnly && <button type="button" aria-pressed={!!image.favorite} onClick={() => act(() => post(`images/${id}/favorite`, { favorite: !image.favorite })).then(reload)}>
            {image.favorite ? '★ Favourite' : '☆ Favourite'}</button>}
          <a className="button" href={href('connections', { focus: `image:${image.id}` })}>See connections</a>
        </div>

        <div className="page-head"><h2>Why it may work</h2>
          {!readOnly && <button type="button" className="quiet" onClick={() => setAdding(!adding)}>{adding ? 'Close' : 'Add a technique'}</button>}</div>
        {data.goals.length > 0 && <p className="mono">Serves: {data.goals.map((g, i) => <span key={g.id}>{i ? ', ' : ''}<a href={href(`explore/goal/${g.id}`)}>{g.name}</a></span>)}</p>}
        {adding && <TechniqueForm title="Add a technique you can see" techniques={taxonomy?.techniques.filter((t) => !data.annotations.some((a) => a.technique_id === t.id)) ?? []}
          onSave={(techniqueId, evidence, effect) => decide({ technique_id: techniqueId }, 'human_reviewed', { evidence, effect })} />}
        {data.annotations.length === 0 && <p className="muted">No technique recorded yet.</p>}
        {data.annotations.map((a) => (
          <article key={a.technique_id} className={`technique-card ${a.role} ${a.state}`}>
            <div className="page-head">
              <a href={href(`technique/${a.technique_id}`)} style={{ fontFamily: 'var(--label)', fontSize: 18 }}>{a.name}</a>
              <span className={`state ${a.state}`}>{STATE_LABEL[a.state]}</span>
            </div>
            <p><span className="muted">Evidence:</span> {a.evidence.join(' ') || '—'}</p>
            <p><span className="muted">Possible effect:</span> {a.effect || '—'}</p>
            <p className="mono">{a.role === 'primary' ? 'Main technique · ' : ''}{a.proposed_backend
              ? `proposed by ${backendName(a.proposed_backend)} (${a.proposed_model}) · confidence ${Math.round(a.confidence * 100)}%` : 'added by you'}
              {a.changed_by !== 'human' && a.proposed_backend && !a.changed_by.includes(`:${a.proposed_backend}/`) ? ` · checked by ${who(a.changed_by)}` : ''}
              {a.changed_by === 'human' && a.proposed_backend ? ' · decided by you' : ''}{a.note ? ` · ${a.note}` : ''}</p>
            {!readOnly && (editing === a.technique_id
              ? <TechniqueForm title="Correct this reading" fixed={a.technique_id} initialEvidence={a.evidence.join('\n')} initialEffect={a.effect}
                  onSave={(_, evidence, effect) => decide(a, 'human_reviewed', { evidence, effect })} onCancel={() => setEditing(null)} />
              : <div className="row">
                  {a.state !== 'human_reviewed' && <button type="button" onClick={() => decide(a, 'human_reviewed')}>✓ Confirm</button>}
                  {a.state !== 'rejected' && <button type="button" onClick={() => decide(a, 'rejected')}>✕ Reject</button>}
                  <button type="button" onClick={() => setEditing(a.technique_id)}>Edit</button>
                </div>)}
          </article>
        ))}
        {!readOnly && data.annotations.some((a) => a.state === 'proposed') &&
          <p><button type="button" className="quiet" onClick={() => startJob('verify')}>Ask a second model to check the proposed readings</button></p>}
        {data.history.length > 0 && <p><button type="button" className="quiet" aria-expanded={showHistory} onClick={() => setShowHistory(!showHistory)}>{showHistory ? 'Hide' : 'Show'} annotation history ({data.history.length})</button></p>}
        {showHistory && <div className="scroll-x"><table className="plain"><thead><tr><th>When</th><th>Technique</th><th>State</th><th>By</th><th>Note</th></tr></thead>
          <tbody>{data.history.map((h, i) => <tr key={i}><td className="mono">{date(h.created_at)}</td><td>{h.technique_id === '*' ? 'all' : taxonomy?.techniques.find((t) => t.id === h.technique_id)?.name ?? h.technique_id}</td>
            <td>{h.state}</td><td>{who(h.changed_by)}</td><td>{h.note}</td></tr>)}</tbody></table></div>}

        {rights && <section className="credit-card" aria-labelledby="credits">
          <h2 id="credits" style={{ fontSize: 26 }}>Usage and credits</h2>
          <p className="credit"><strong>{rights.label}</strong><br />{rights.required_attribution}</p>
          <p style={{ fontSize: 14 }}>Licence: {rights.license_code}{rights.license_version ? ` ${rights.license_version}` : ''} — <a href={rights.license_url} target="_blank" rel="noreferrer">licence text</a>.
            Checked {date(rights.verified_at)} against the {PROVIDERS[image.provider] ?? image.provider} record
            ({Object.entries(rights.evidence).filter(([k]) => !/url|Url|image/i.test(k)).map(([k, v]) => `${k} = ${String(v).slice(0, 40)}`).join('; ')}).</p>
          {rights.restrictions && <p style={{ fontSize: 14 }}><strong>Notes:</strong> {rights.restrictions}</p>}
          <p style={{ fontSize: 14 }}>Allowed here: {rights.permitted_mode}. Labels describe what was checked; they are not legal advice. Check the source before publishing.</p>
          <div className="row">
            <a href={image.source_url} target="_blank" rel="noreferrer">Source page</a>
            <button type="button" className="quiet" onClick={() => navigator.clipboard.writeText(rights.required_attribution).then(() => setMessage('Credit copied.'))}>Copy credit</button>
            {!readOnly && <RemoveButton onRemove={() => act(() => del(`images/${id}`)).then(() => go(''))} />}
          </div>
          <p className="mono">File SHA-256 {image.file_sha256.slice(0, 16)}… · retrieved {date(rights.retrieved_at)}</p>
        </section>}
      </aside>
    </div>
  )
}

function TechniqueForm({ title, techniques = [], fixed, initialEvidence = '', initialEffect = '', onSave, onCancel }: {
  title: string; techniques?: { id: string; name: string }[]; fixed?: string; initialEvidence?: string; initialEffect?: string
  onSave: (techniqueId: string, evidence: string[], effect: string) => void; onCancel?: () => void
}) {
  const [technique, setTechnique] = useState(fixed ?? '')
  const [evidence, setEvidence] = useState(initialEvidence)
  const [effect, setEffect] = useState(initialEffect)
  return (
    <form className="stack notice" onSubmit={(event) => { event.preventDefault(); onSave(technique, evidence.split('\n').map((s) => s.trim()).filter(Boolean), effect) }}>
      <h3>{title}</h3>
      {!fixed && <label className="field">Technique
        <select required value={technique} onChange={(event) => setTechnique(event.target.value)}>
          <option value="">Choose…</option>{techniques.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select></label>}
      <label className="field">What you can see that shows it (one point per line)
        <textarea rows={3} required value={evidence} onChange={(event) => setEvidence(event.target.value)} /></label>
      <label className="field">Possible effect on a viewer
        <input value={effect} onChange={(event) => setEffect(event.target.value)} placeholder="may draw the eye to…" /></label>
      <div className="row"><button type="submit" className="primary">Save as confirmed by you</button>{onCancel && <button type="button" onClick={onCancel}>Cancel</button>}</div>
    </form>
  )
}

function SaveToCollection({ imageId, member, onDone }: { imageId: number; member: { id: number; name: string }[]; onDone: (text: string) => void }) {
  const [open, setOpen] = useState(false)
  const { data, reload } = useData<Collection[]>(open ? 'collections' : null)
  const [name, setName] = useState('')
  async function toggle(collection: { id: number; name: string }, add: boolean) {
    try { await post(`collections/${collection.id}/items`, { image_id: imageId, add }); onDone(add ? `Saved to “${collection.name}”.` : `Removed from “${collection.name}”.`); reload() }
    catch (reason) { onDone((reason as Error).message) }
  }
  async function create(event: React.FormEvent) {
    event.preventDefault()
    try { const made = await post<{ id: number }>('collections', { name }); await toggle({ id: made.id, name }, true); setName('') }
    catch (reason) { onDone((reason as Error).message) }
  }
  return (
    <>
      <button type="button" className="primary" aria-expanded={open} onClick={() => setOpen(!open)}>Save to collection</button>
      {open && <div className="notice stack" style={{ flexBasis: '100%' }}>
        {data?.length ? data.map((c) => {
          const inside = member.some((m) => m.id === c.id)
          return <label key={c.id} className="choice"><input type="checkbox" checked={inside} onChange={() => toggle(c, !inside)} /> {c.name} <span className="mono">{c.size}</span></label>
        }) : <p className="muted">No collections yet.</p>}
        <form className="row" onSubmit={create}><label className="field grow">New collection<input value={name} required maxLength={80} onChange={(e) => setName(e.target.value)} /></label>
          <button type="submit" style={{ alignSelf: 'end' }}>Create and save</button></form>
      </div>}
    </>
  )
}

function RemoveButton({ onRemove }: { onRemove: () => void }) {
  const [asking, setAsking] = useState(false)
  if (!asking) return <button type="button" className="quiet" onClick={() => setAsking(true)}>Remove from library</button>
  return (
    <span className="row" role="group" aria-label="Confirm removal">
      <span>Delete this image, its copies and annotations? It will not be collected again.</span>
      <button type="button" className="danger" onClick={onRemove}>Remove</button>
      <button type="button" onClick={() => setAsking(false)}>Keep</button>
    </span>
  )
}
