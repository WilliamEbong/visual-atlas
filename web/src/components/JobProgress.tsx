import { useCallback, useState } from 'react'
import { media, post } from '../lib/client'
import { date, useData, usePoll } from '../lib/hooks'
import { href } from '../lib/router'
import type { Job } from '../lib/types'
import { PROVIDERS } from '../lib/types'
import { Failure, Loading, useNotice } from './ui'

const STAGES = [['searching', 'Search'], ['checking', 'Check permissions'], ['analyzing', 'Analyse'], ['done', 'Ready']] as const
const ORDER = ['queued', 'planning', 'searching', 'checking', 'analyzing', 'done']
const ACTIVE = ['queued', 'running', 'cancelling']
const SKIP_LABELS: Record<string, string> = {
  ineligible: 'without a usable free licence', duplicate: 'duplicates of images you already have',
  low_quality: 'too small, damaged or unclear', no_technique: 'with no clear technique', filtered: 'outside your shape or colour filter',
  failed: 'failed (network or answer problems)', skipped: 'not needed, or skipped before download',
}
const OUTCOME: Record<string, [string, string]> = {
  added: ['Added', 'ok'], ineligible: ['Skipped · licence not accepted', ''], duplicate: ['Skipped · already in the library', ''],
  low_quality: ['Skipped · too small or unclear', ''], no_technique: ['Not added · no clear technique', ''], filtered: ['Skipped · shape or colour', ''],
  failed: ['Failed', 'warn'], skipped: ['Skipped', ''], downloaded: ['Analysing…', 'warn'], eligible: ['Free to use · waiting', ''], found: ['Checking…', ''],
}
const KIND: Record<string, string> = { find: 'Find', grow: 'Grow', verify: 'Second-model check', analyze: 'Analysis', compare: 'Comparison', directions: 'Directions' }

export function stageIndex(job: Job): number {
  if (job.state === 'done') return 3
  const index = ORDER.indexOf(job.stage)
  return index <= 2 ? 0 : index - 2
}

export default function JobProgress({ jobId, compact = false }: { jobId: string; compact?: boolean }) {
  const { data: job, error, busy: unavailable, reload } = useData<Job>(`jobs/${jobId}`)
  const { fail } = useNotice()
  const [busy, setBusy] = useState(false)
  const active = !!job && ACTIVE.includes(job.state)
  usePoll(useCallback(reload, [reload]), active, 1500)
  if (error) return <Failure message={error} busy={unavailable} retry={reload} />
  if (!job) return <Loading label="Loading the job…" plates={false} />
  const discovery = job.kind === 'find' || job.kind === 'grow'
  const now = stageIndex(job)
  const counts = job.counts
  const candidates = Object.values(counts).reduce((a, b) => a + b, 0)
  const free = (counts.eligible ?? 0) + (counts.downloaded ?? 0) + (counts.added ?? 0) + (counts.no_technique ?? 0) + (counts.duplicate ?? 0)
    + (counts.low_quality ?? 0) + (counts.filtered ?? 0)
  const skipped = Object.entries(counts).filter(([state]) => state in SKIP_LABELS)
  const targets = (job.spec.targets as string[] | undefined)?.length
  // A finished Find/Grow job that did not reach the number asked for is not presented as a plain success.
  const reached = targets ? job.matching : counts.added ?? 0
  const wanted = Number(job.spec.target_new_images ?? 0)
  const short = discovery && job.state === 'done' && reached < wanted
  const title = short ? 'Stopped short' : job.state === 'done' ? (job.message.startsWith('Ready') ? 'Ready' : 'Finished') : job.state === 'cancelled' ? 'Cancelled'
    : job.state === 'failed' ? 'Stopped' : job.state === 'paused' ? 'Paused' : 'Working on it'
  const thumbs = Object.fromEntries(job.added.map((image) => [image.id, image.thumb]))
  const outcomes = (job.items ?? []).filter((item) => item.kind === 'candidate' && item.state !== 'found').slice(-8).reverse()

  async function control(action: string) {
    setBusy(true)
    try { await post(`jobs/${job!.id}/${action}`); reload() } catch (reason) { fail(reason) } finally { setBusy(false) }
  }

  return (
    <section className="stack" aria-label="Job progress" style={{ gap: 0 }}>
      <div className="section-title">
        <h2>{title}</h2>
        <span className="mono">{KIND[job.kind] ?? job.kind} · {job.backend}{job.spec.verify_with ? ` + ${job.spec.verify_with} check` : ''} · {date(job.created_at)}</span>
      </div>
      {typeof job.spec.goal === 'string' && job.spec.goal && <p className="mono" style={{ marginTop: 6 }}>“{job.spec.goal.slice(0, 120)}”</p>}
      {discovery && <ol className="timeline" aria-label="Progress">
        {STAGES.map(([key, label], index) => {
          const state = index < now || job.state === 'done' ? 'done' : index === now && active ? 'now' : ''
          const detail = key === 'searching' ? `${job.searches} search${job.searches === 1 ? '' : 'es'} · ${candidates} found`
            : key === 'checking' ? `${free} free to use`
            : key === 'analyzing' ? (targets ? `${job.matching} of ${wanted} show what you asked` : `${counts.added ?? 0} of ${wanted} added`)
            : job.state === 'done' ? 'done' : ''
          return <li key={key}><span className={`dot ${state}`} aria-hidden="true" /><span className="step">{label}</span>
            <span className="mono">{detail}</span><span className="sr-only">{state === 'done' ? '(done)' : state === 'now' ? '(in progress)' : '(waiting)'}</span></li>
        })}
      </ol>}
      {discovery && <dl className="counts">
        {[['Found', candidates], ['Free to use', free], ['Analysed', (counts.added ?? 0) + (counts.no_technique ?? 0)], ['Added', counts.added ?? 0],
          ...(targets ? [['Show what you asked', job.matching]] : [])].map(([label, n]) =>
          <div key={label}><dt>{label}</dt><dd>{n}</dd></div>)}
      </dl>}
      <p className={job.state === 'failed' || (job.state === 'paused' && job.error_code) ? 'notice error' : 'muted'} role="status" style={{ marginTop: 16 }}>{job.message}</p>
      {discovery && !!job.spec.verify_with && (counts.added ?? 0) > 0 &&
        <p className="mono" style={{ marginTop: 8 }}>{job.checked} of {counts.added} checked by a second model</p>}
      {discovery && outcomes.length > 0 && <ul className="outcomes" style={{ marginTop: 12 }} aria-label="Latest results">
        {outcomes.map((item) => {
          const [label, tone] = OUTCOME[item.state] ?? [item.state, '']
          const thumb = item.image_id ? thumbs[item.image_id] : undefined
          return <li key={item.id}>
            <span className="thumb">{thumb && <img src={media(thumb)} alt="" />}</span>
            <span className="what"><span>{item.image_id && item.state === 'added' ? <a href={href(`image/${item.image_id}`)}>{item.title ?? 'Untitled'}</a> : item.title ?? 'Untitled'}</span>
              <span className="mono">{PROVIDERS[item.provider] ?? item.provider}</span></span>
            <span className={`result ${tone}`} title={item.reason}>{label}</span>
          </li>
        })}
      </ul>}
      <div className="row" style={{ marginTop: 18 }}>
        {(job.state === 'running' || job.state === 'queued') && <button type="button" disabled={busy} onClick={() => control('pause')}>Pause</button>}
        {(job.state === 'paused' || job.state === 'failed') && <button type="button" className="primary" disabled={busy} onClick={() => control('resume')}>Resume</button>}
        {['running', 'queued', 'paused'].includes(job.state) && <button type="button" disabled={busy} onClick={() => control('cancel')}>Stop and keep what's added</button>}
        {compact && <a href={href(`jobs/${job.id}`)}>Details</a>}
      </div>
      {!discovery && job.added.length > 0 && <div className="strip" style={{ marginTop: 18 }}>
        {job.added.map((image) => <a key={image.id} className="specimen" href={href(`image/${image.id}`)} style={{ height: 120 }} aria-label={image.title}>
          <img src={media(image.thumb)} alt="" style={{ height: '100%', width: 'auto', maxWidth: 'none' }} /></a>)}</div>}
      {skipped.length > 0 && <details style={{ marginTop: 18 }}>
        <summary>{skipped.reduce((sum, [, n]) => sum + n, 0)} not added — see why</summary>
        <ul className="mono">{skipped.map(([state, n]) => <li key={state}>{n} {SKIP_LABELS[state]}</li>)}</ul>
        {!compact && job.items && <div className="scroll-x"><table className="plain"><thead><tr><th>Item</th><th>Source</th><th>Result</th><th>Reason</th></tr></thead>
          <tbody>{job.items.filter((item) => item.kind === 'candidate' && item.state !== 'added').map((item) => (
            <tr key={item.id}><td>{item.title ?? '—'}</td><td>{PROVIDERS[item.provider] ?? item.provider}</td><td>{item.state}</td><td>{item.reason}</td></tr>))}</tbody></table></div>}
      </details>}
      {!compact && job.items && job.items.some((item) => item.kind === 'query') && <details>
        <summary>Searches</summary>
        <ul className="mono">{job.items.filter((item) => item.kind === 'query').map((item) => <li key={item.id}>{PROVIDERS[item.provider] ?? item.provider}: “{item.query}” — {item.state}{item.reason ? ` (${item.reason})` : ''}</li>)}</ul>
      </details>}
    </section>
  )
}
