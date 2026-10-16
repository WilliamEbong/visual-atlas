import { useEffect, useMemo, useState } from 'react'
import { del, media, post, readOnly, request } from '../lib/client'
import { date, useApp, useData } from '../lib/hooks'
import { aspect } from '../lib/library'
import { regionBox, regionLabel } from '../lib/regions'
import { go, href, useRoute } from '../lib/router'
import type { Annotation, Collection, ImageDetail, Settings } from '../lib/types'
import { PROVIDERS, STATE_LABEL } from '../lib/types'
import { Failure, Loading, useNotice } from './ui'

function backendName(name: string) {
  return { codex: 'Codex', 'codex-interactive': 'Codex curation agent', claude: 'Claude Code', fake: 'Practice mode (no model)' }[name] ?? name
}

function who(changedBy: string) {
  if (changedBy === 'human') return 'you'
  const [, rest = changedBy] = changedBy.split(':')
  const [backend, model] = rest.split('/')
  return `${backendName(backend)}${model ? ` (${model})` : ''}`
}

// History rows keep earlier readings; a superseded one is no longer current evidence.
const HISTORY_STATE: Record<string, string> = {
  proposed: 'proposed', model_reviewed: 'agreed by a second model', human_reviewed: 'confirmed by you', rejected: 'rejected',
  superseded: 'superseded (no longer current)', verify: 'second-model check',
}

function readTrail(): { query: string; ids: number[] } {
  try { return JSON.parse(sessionStorage.getItem('trail') ?? '') } catch { return { query: '', ids: [] } }
}

export default function ImagePage({ id }: { id: number }) {
  const { query } = useRoute()
  const from = query.get('from')?.startsWith('#/connections?') ? query.get('from') : null
  const { data, error, busy, reload, setData } = useData<ImageDetail>(`images/${id}`)
  const { taxonomy, compare, toggleCompare } = useApp()
  const { notify, fail, confirm } = useNotice()
  const [editing, setEditing] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)
  const [lit, setLit] = useState<string | null>(null)
  const [allRegions, setAllRegions] = useState(false)
  const [tab, setTab] = useState<string | null>(null)
  const trail = useMemo(readTrail, [])
  const position = trail.ids.indexOf(id)
  const previous = position > 0 ? trail.ids[position - 1] : null
  const next = position >= 0 && position < trail.ids.length - 1 ? trail.ids[position + 1] : null
  useEffect(() => { if (data) document.title = `${data.image.title} · Visual Atlas` }, [data])
  useEffect(() => { setLit(null); setTab(null); setEditing(null); setAdding(false) }, [id])
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const target = event.target as HTMLElement
      if (event.altKey || event.ctrlKey || event.metaKey || target.closest('input, textarea, select, [contenteditable], dialog[open], .tabs')) return
      if (event.key === 'ArrowLeft' && previous) go(`image/${previous}`, { from })
      if (event.key === 'ArrowRight' && next) go(`image/${next}`, { from })
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [previous, next, from])

  if (error) return <><Crumbs trail={trail} position={position} previous={previous} next={next} from={from} /><Failure message={error} busy={busy} retry={reload} /></>
  if (!data || data.image.id !== id) return <><Crumbs trail={trail} position={position} previous={previous} next={next} from={from} /><Loading label="Loading the image…" plates={false} /></>
  const { image, rights, metrics, analysis } = data
  const picked = compare.some((p) => p.id === image.id)
  const ratio = image.width && image.height ? image.width / image.height : 1.4
  const relatedTechniques = [...new Set(data.related.flatMap((r) => r.via))]
  const shown = tab ?? relatedTechniques[0] ?? null
  const related = shown ? data.related.filter((r) => r.via.includes(shown)) : data.related
  const nameOf = (techniqueId: string) => taxonomy?.techniques.find((t) => t.id === techniqueId)?.name ?? techniqueId

  async function decide(annotation: Pick<Annotation, 'technique_id'>, state: 'human_reviewed' | 'rejected', extra: Record<string, unknown> = {}) {
    try {
      setData(await post<ImageDetail>(`images/${id}/annotations`, { technique_id: annotation.technique_id, state, ...extra }))
      setEditing(null); setAdding(false)
      notify(state === 'rejected' ? 'Marked as rejected. Your decision is kept even if the image is analysed again.' : 'Saved as confirmed by you.')
    } catch (reason) { fail(reason) }
  }
  async function startJob(kind: 'analyze' | 'verify') {
    try {
      const settings = await request<Settings>('settings')
      const backend = kind === 'verify' ? (settings.verify_with === 'none' ? 'claude' : settings.verify_with) : settings.backend
      const job = await post<{ id: string }>('jobs', { kind, spec: { image_ids: [id], backend } })
      go(`jobs/${job.id}`)
    } catch (reason) { fail(reason) }
  }
  async function favourite(on: boolean) {
    try {
      await post(`images/${id}/favorite`, { favorite: on }); reload()
      notify(on ? 'Added to favourites.' : 'Removed from favourites.', { undo: async () => { await post(`images/${id}/favorite`, { favorite: !on }); reload() } })
    } catch (reason) { fail(reason) }
  }
  async function remove() {
    const sure = await confirm({ title: 'Remove this image from the library?', danger: true, confirm: 'Remove',
      body: `Its files, readings${data!.collections.length ? ` and places in ${data!.collections.length} collection${data!.collections.length === 1 ? '' : 's'}` : ''} go. A note stays so later searches skip it. This cannot be undone.` })
    if (!sure) return
    try { await del(`images/${id}`); notify(`Removed “${image.title}” from the library.`); go('', { from }) } catch (reason) { fail(reason) }
  }

  return (
    <>
      <Crumbs trail={trail} position={position} previous={previous} next={next} from={from} />
      <section className="image-head" aria-labelledby="image-title">
        <figure className={`figure${allRegions ? ' regions-on' : ''}`} style={{ aspectRatio: ratio, flexBasis: `min(900px, calc(76vh * ${ratio.toFixed(3)}))` }}>
          <img src={media(image.display)} alt={`${image.title}${image.creator ? ` by ${image.creator}` : ''}`} />
          {analysis?.observations.map((o) => {
            const box = regionBox(o.region)
            return box && <div key={o.id} aria-hidden="true" className={`region${lit === o.id ? ' lit' : ''}`}
              style={{ left: `${box.x}%`, top: `${box.y}%`, width: `${box.w}%`, height: `${box.h}%` }}>
              <span className="region-tag">{o.id.toUpperCase()}</span></div>
          })}
        </figure>
        <div className="image-title">
          <p className="mono">Fig. {image.id} · {PROVIDERS[image.provider] ?? image.provider}{image.medium ? ` · ${image.medium}` : ''}</p>
          <h1 id="image-title">{image.title}</h1>
          <p className="muted">{[image.creator || 'Unknown maker', image.date_text].filter(Boolean).join(' · ')}</p>
          {rights && <p className="mono" style={{ color: 'var(--green)' }}>{rights.label} · {date(rights.verified_at)}</p>}
          <div className="row" style={{ marginTop: 6 }}>
            {!readOnly && <SaveToCollection imageId={image.id} member={data.collections} onDone={reload} />}
            <button type="button" aria-pressed={picked} onClick={() => toggleCompare({ id: image.id, title: image.title, thumb: image.thumb })}>{picked ? '✓ Comparing' : 'Compare'}</button>
            {!readOnly && <button type="button" aria-pressed={!!image.favorite} onClick={() => favourite(!image.favorite)}>{image.favorite ? '★ Favourite' : '☆ Favourite'}</button>}
            <a className="button" href={image.source_url} target="_blank" rel="noreferrer">Open at the source ↗</a>
          </div>
        </div>
      </section>
      <p className="mono under">Fig. {image.id}  {image.width} × {image.height} px{metrics ? ` · ${metrics.orientation} · mostly ${metrics.color_family}` : ''}
        {analysis?.observations.some((o) => regionBox(o.region)) && <> · <button type="button" className="quiet small" aria-pressed={allRegions}
          onClick={() => setAllRegions(!allRegions)}>{allRegions ? 'Hide the marked areas' : 'Show every marked area'}</button></>}
        {image.original && !readOnly && <> · <a href={media(image.original)} target="_blank" rel="noreferrer">open the original file</a></>}</p>

      <div className="three">
        <section className="see" aria-labelledby="see">
          <h2 id="see" className="ruled-title rule-blue">What you can see</h2>
          {analysis ? <>
            <ol className="observations">
              {analysis.observations.map((o) => (
                <li key={o.id} onMouseEnter={() => setLit(o.id)} onMouseLeave={() => setLit(null)}>
                  <button type="button" aria-pressed={lit === o.id} onClick={() => setLit(lit === o.id ? null : o.id)}
                    onFocus={() => setLit(o.id)} aria-label={`${o.id.toUpperCase()}: ${o.text} Area: ${regionLabel(o.region)}.`}>
                    <span className="obs-id" aria-hidden="true">{o.id.toUpperCase()}</span><span aria-hidden="true">{o.text}</span>
                  </button>
                </li>))}
            </ol>
            {analysis.ambiguities.length > 0 && <p className="muted" style={{ marginTop: 12 }}><strong>Left open:</strong> {analysis.ambiguities.join(' ')}</p>}
            <p className="mono" style={{ marginTop: 12 }}>Described by {backendName(analysis.backend)} ({analysis.model}) on {date(analysis.created_at)}. A model's description of the pixels, not a catalogue record.</p>
          </> : <div className="stack" style={{ marginTop: 14 }}><p className="muted">Not analysed yet.</p>
            {!readOnly && <div><button type="button" className="primary" onClick={() => startJob('analyze')}>Analyse this image</button></div>}</div>}
        </section>

        <section className="why" aria-labelledby="why">
          <div className="ruled-title rule-rust section-title"><h2 id="why">Why it may work</h2>
            {!readOnly && <button type="button" className="quiet small" aria-expanded={adding} onClick={() => setAdding(!adding)}>{adding ? 'Close' : 'Add a technique'}</button>}</div>
          {data.goals.length > 0 && <p className="mono" style={{ marginTop: 10 }}>Serves: {data.goals.map((g, i) => <span key={g.id}>{i ? ', ' : ''}<a href={href(`explore/goal/${g.id}`, { from })}>{g.name}</a></span>)}</p>}
          {adding && <TechniqueForm title="Add a technique you can see" techniques={taxonomy?.techniques.filter((t) => !data.annotations.some((a) => a.technique_id === t.id)) ?? []}
            onSave={(techniqueId, evidence, effect) => decide({ technique_id: techniqueId }, 'human_reviewed', { evidence, effect })} />}
          {data.annotations.length === 0 && <p className="muted" style={{ marginTop: 14 }}>No technique recorded yet.</p>}
          {data.annotations.map((a) => (
            <article key={a.technique_id} className={`technique-card ${a.state}`}>
              <div className="card-top">
                <h3><a href={href(`technique/${a.technique_id}`, { from })}>{a.name}</a></h3>
                <span className={`state ${a.state}`}>{STATE_LABEL[a.state]}</span>
              </div>
              <p style={{ fontSize: 15 }}>{a.effect || 'No effect recorded.'}</p>
              <p style={{ fontSize: 14 }} className="muted">{a.evidence.join(' ') || '—'}</p>
              <p className="mono">{a.role === 'primary' ? 'Main technique · ' : ''}{a.proposed_backend
                ? `proposed by ${backendName(a.proposed_backend)}` : 'added by you'}
                {a.changed_by !== 'human' && a.proposed_backend && !a.changed_by.includes(`:${a.proposed_backend}/`) ? ` · checked by ${who(a.changed_by)}` : ''}
                {a.changed_by === 'human' && a.proposed_backend ? ' · decided by you, kept on re-analysis' : ''}{a.note ? ` · ${a.note}` : ''}</p>
              {!readOnly && (editing === a.technique_id
                ? <TechniqueForm title="Correct this reading" fixed={a.technique_id} initialEvidence={a.evidence.join('\n')} initialEffect={a.effect}
                    onSave={(_, evidence, effect) => decide(a, 'human_reviewed', { evidence, effect })} onCancel={() => setEditing(null)} />
                : <div className="row">
                    {a.state !== 'human_reviewed' && <button type="button" className="small" onClick={() => decide(a, 'human_reviewed')}>Confirm</button>}
                    {a.state !== 'rejected' && <button type="button" className="small" onClick={() => decide(a, 'rejected')}>Reject</button>}
                    <button type="button" className="quiet small" onClick={() => setEditing(a.technique_id)}>Edit evidence</button>
                  </div>)}
            </article>
          ))}
          {!readOnly && data.annotations.some((a) => a.state === 'proposed') &&
            <p style={{ marginTop: 12 }}><button type="button" className="quiet small" onClick={() => startJob('verify')}>Ask a second model to check the proposed readings</button></p>}
        </section>

        {rights && <aside className="use" aria-labelledby="use">
          <h2 id="use" className="ruled-title rule-green">Usage and credits</h2>
          <div className="slip" style={{ marginTop: 16 }}>
            <p className="credit">{rights.required_attribution}</p>
            <button type="button" className="small" style={{ marginTop: 14, background: 'var(--ground)' }}
              onClick={() => navigator.clipboard.writeText(rights.required_attribution).then(() => notify('Credit copied.'), fail)}>Copy credit</button>
          </div>
          <dl className="facts">
            <dt>Licence</dt><dd><a href={rights.license_url} target="_blank" rel="noreferrer">{rights.license_code}{rights.license_version ? ` ${rights.license_version}` : ''}</a></dd>
            <dt>Checked</dt><dd>{date(rights.verified_at)} against the {PROVIDERS[image.provider] ?? image.provider} record
              ({Object.entries(rights.evidence).filter(([k]) => !/url|Url|image/i.test(k)).map(([k, v]) => `${k} = ${String(v).slice(0, 40)}`).join('; ')})</dd>
            <dt>Allowed</dt><dd>{rights.permitted_mode}</dd>
            {rights.restrictions && <><dt>Notes</dt><dd>{rights.restrictions}</dd></>}
            <dt>File</dt><dd className="mono">SHA-256 {image.file_sha256.slice(0, 16)}…</dd>
          </dl>
          <p className="mono" style={{ marginTop: 12 }}>Labels say what was checked; they are not legal advice. Check the source before publishing.</p>
          {image.description && <details style={{ marginTop: 16, borderTop: '1px solid var(--hair)', paddingTop: 8 }}>
            <summary>From the source record</summary>
            <p style={{ fontSize: 14 }} className="muted">The institution's own words, not an analysis: {image.description}</p>
          </details>}
          {!readOnly && <p style={{ marginTop: 16 }}><button type="button" className="quiet small danger" style={{ color: 'var(--danger)' }} onClick={remove}>Remove from library…</button></p>}
        </aside>}
      </div>

      {data.related.length > 0 && <section className="section" aria-labelledby="related">
        <div className="section-title">
          <h2 id="related">{shown ? `Also shows ${nameOf(shown).replace(/ \(.*\)$/, '').toLowerCase()}` : 'Related images'}</h2>
          {relatedTechniques.length > 1 && <div className="tabs" role="tablist" aria-label="Related by technique">
            {relatedTechniques.slice(0, 5).map((t) => <button key={t} type="button" role="tab" aria-selected={t === shown} onClick={() => setTab(t)}>{nameOf(t).replace(/ \(.*\)$/, '')}</button>)}
          </div>}
        </div>
        <div className="strip" style={{ marginTop: 20 }}>
          {related.map((r, index) => (
            <a key={r.id} href={href(`image/${r.id}`, { from })} className="specimen" style={{ height: [200, 150, 176, 220, 132, 190][index % 6], aspectRatio: aspect(r) }} aria-label={r.title}>
              <img src={media(r.thumb)} alt="" /></a>))}
        </div>
        <p className="mono strip-caption">{related.slice(0, 6).map((r) => r.title).join(' · ')}</p>
      </section>}

      <section className="section" aria-label="See also" style={{ marginTop: 40 }}>
        <div className="row"><a className="button small" href={href('connections', { focus: `image:${image.id}`, from })}>See connections</a></div>
        {data.history.length > 0 && <details style={{ marginTop: 24, borderTop: '1px solid var(--hair)', paddingTop: 10 }}>
          <summary>History · {data.history.length} entr{data.history.length === 1 ? 'y' : 'ies'}</summary>
          <div className="scroll-x"><table className="plain"><thead><tr><th>When</th><th>Technique</th><th>State</th><th>By</th><th>Note</th></tr></thead>
            <tbody>{data.history.map((h, i) => <tr key={i}><td className="mono">{date(h.created_at)}</td><td>{h.technique_id === '*' ? 'all' : nameOf(h.technique_id)}</td>
              <td>{HISTORY_STATE[h.state] ?? h.state}</td><td>{who(h.changed_by)}</td><td>{h.note}</td></tr>)}</tbody></table></div>
        </details>}
      </section>
    </>
  )
}

function Crumbs({ trail, position, previous, next, from }: { trail: { query: string; ids: number[] }; position: number; previous: number | null; next: number | null; from: string | null }) {
  return (
    <nav className="crumbs" aria-label="Results">
      <a href={href('', { ...Object.fromEntries(new URLSearchParams(trail.query)), from })} className="mono" style={{ color: 'var(--graphite)', textDecoration: 'none' }}>← Library</a>
      {position >= 0 && <div className="row">
        <span className="mono">{position + 1} of {trail.ids.length} · ← → to move</span>
        <a className="button small" aria-disabled={!previous} href={previous ? href(`image/${previous}`, { from }) : undefined}>← Previous</a>
        <a className="button small" aria-disabled={!next} href={next ? href(`image/${next}`, { from }) : undefined}>Next →</a>
      </div>}
    </nav>
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
    <form className="stack panel" onSubmit={(event) => { event.preventDefault(); onSave(technique, evidence.split('\n').map((s) => s.trim()).filter(Boolean), effect) }}>
      <h3 className="label">{title}</h3>
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

function SaveToCollection({ imageId, member, onDone }: { imageId: number; member: { id: number; name: string }[]; onDone: () => void }) {
  const [open, setOpen] = useState(false)
  const { data, reload } = useData<Collection[]>(open ? 'collections' : null)
  const { notify, fail } = useNotice()
  const [name, setName] = useState('')
  async function toggle(collection: { id: number; name: string }, add: boolean) {
    try {
      // A removal answers with the image's position, so Undo puts it back where it was, not at the end.
      const { position } = await post<{ position: number | null }>(`collections/${collection.id}/items`, { image_id: imageId, add })
      reload(); onDone()
      notify(add ? `Saved to “${collection.name}”.` : `Removed from “${collection.name}”.`, {
        undo: async () => {
          await post(`collections/${collection.id}/items`, { image_id: imageId, add: !add, ...(add ? {} : { position }) })
          reload(); onDone()
        } })
    } catch (reason) { fail(reason) }
  }
  async function create(event: React.FormEvent) {
    event.preventDefault()
    try { const made = await post<{ id: number }>('collections', { name }); await toggle({ id: made.id, name }, true); setName('') }
    catch (reason) { fail(reason) }
  }
  return (
    <>
      <button type="button" className="primary" aria-expanded={open} onClick={() => setOpen(!open)}>Save to a collection</button>
      {open && <div className="panel" style={{ flexBasis: '100%' }}>
        {data?.length ? <div className="stack" style={{ gap: 4 }}>{data.map((c) => {
          const inside = member.some((m) => m.id === c.id)
          return <label key={c.id} className="choice plain"><input type="checkbox" checked={inside} onChange={() => toggle(c, !inside)} /> {c.name} <span className="mono">{c.size}</span></label>
        })}</div> : <p className="muted">No collections yet.</p>}
        <form className="filters" onSubmit={create}><label className="field grow">New collection<input value={name} required maxLength={80} onChange={(e) => setName(e.target.value)} /></label>
          <button type="submit">Create and save</button></form>
      </div>}
    </>
  )
}
