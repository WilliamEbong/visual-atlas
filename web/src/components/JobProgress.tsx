import { useCallback, useState } from 'react'
import { media, post } from '../lib/client'
import { date, useData, usePoll } from '../lib/hooks'
import { href } from '../lib/router'
import type { Job } from '../lib/types'
import { PROVIDERS } from '../lib/types'

const STAGES = [['searching', 'Searching'], ['checking', 'Checking permissions'], ['analyzing', 'Analyzing'], ['done', 'Ready']] as const
const ORDER = ['queued', 'planning', 'searching', 'checking', 'analyzing', 'done']
const ACTIVE = ['queued', 'running', 'cancelling']
const SKIP_LABELS: Record<string, string> = {
  ineligible: 'without a usable free licence', duplicate: 'duplicates of images you already have',
  low_quality: 'too small, damaged or unclear', no_technique: 'with no clear technique', filtered: 'outside your shape or colour filter',
  failed: 'failed (network or answer problems)', skipped: 'not needed once the target was reached',
}

export function stageIndex(job: Job): number {
  if (job.state === 'done') return 3
  const index = ORDER.indexOf(job.stage)
  return index <= 2 ? 0 : index - 2
}

export default function JobProgress({ jobId, compact = false }: { jobId: string; compact?: boolean }) {
  const { data: job, error, reload } = useData<Job>(`jobs/${jobId}`)
  const [busy, setBusy] = useState(false)
  const active = !!job && ACTIVE.includes(job.state)
  usePoll(useCallback(reload, [reload]), active, 1500)
  if (error) return <p className="notice error" role="alert">{error}</p>
  if (!job) return <p className="mono">Loading job…</p>
  const discovery = job.kind === 'find' || job.kind === 'grow'
  const now = stageIndex(job)
  const counts = job.counts
  const candidates = Object.values(counts).reduce((a, b) => a + b, 0)
  const checked = candidates - (counts.found ?? 0)
  const free = (counts.eligible ?? 0) + (counts.downloaded ?? 0) + (counts.added ?? 0) + (counts.no_technique ?? 0) + (counts.duplicate ?? 0)
    + (counts.low_quality ?? 0) + (counts.filtered ?? 0)
  const skipped = Object.entries(counts).filter(([state]) => state in SKIP_LABELS && state !== 'skipped')

  async function control(action: string) {
    setBusy(true)
    try { await post(`jobs/${job!.id}/${action}`); reload() } finally { setBusy(false) }
  }

  return (
    <section className="stack" aria-label="Job progress" aria-live="polite">
      <div className="page-head">
        <h2>{job.state === 'done' ? 'Ready' : job.state === 'cancelled' ? 'Cancelled' : job.state === 'failed' ? 'Stopped'
          : job.state === 'paused' ? 'Paused' : 'Working on it'}</h2>
        <span className="mono">{job.kind} · {job.backend}{job.spec.verify_with ? ` + ${job.spec.verify_with} check` : ''} · {date(job.created_at)}</span>
      </div>
      {discovery && <ol className="stages">
        {STAGES.map(([key, label], index) => {
          const state = index < now || job.state === 'done' ? 'done' : index === now && active ? 'now' : ''
          const detail = key === 'searching' ? `${job.searches} search${job.searches === 1 ? '' : 'es'}`
            : key === 'checking' ? `${checked} checked · ${free} free to use`
            : key === 'analyzing' ? ((job.spec.targets as string[] | undefined)?.length
              ? `${job.matching} of ${String(job.spec.target_new_images ?? '')} show what you asked · ${counts.added ?? 0} added`
              : `${counts.added ?? 0} added of ${String(job.spec.target_new_images ?? '')}`) : ''
          return <li key={key}><span className={`dot ${state}`} aria-hidden="true" />{state === 'now' ? <strong>{label}</strong> : label}
            {detail && <span className="mono">{detail}</span>}<span className="sr-only">{state === 'done' ? '(done)' : state === 'now' ? '(in progress)' : ''}</span></li>
        })}
      </ol>}
      <p className={job.state === 'failed' || (job.state === 'paused' && job.error_code) ? 'notice error' : 'muted'}>{job.message}</p>
      {discovery && !!job.spec.verify_with && (counts.added ?? 0) > 0 &&
        <p className="mono">{job.checked} of {counts.added} checked by a second model</p>}
      <div className="row">
        {(job.state === 'running' || job.state === 'queued') && <button type="button" disabled={busy} onClick={() => control('pause')}>Pause</button>}
        {(job.state === 'paused' || job.state === 'failed') && <button type="button" className="primary" disabled={busy} onClick={() => control('resume')}>Resume</button>}
        {['running', 'queued', 'paused'].includes(job.state) && <button type="button" disabled={busy} onClick={() => control('cancel')}>Cancel</button>}
        {compact && <a href={href(`jobs/${job.id}`)}>Details</a>}
      </div>
      {job.added.length > 0 && <div className="thumbs">
        {job.added.map((image) => <a key={image.id} href={href(`image/${image.id}`)}><div className="frame"><img src={media(image.thumb)} alt={image.title} /></div><span>{image.title}</span></a>)}
      </div>}
      {skipped.length > 0 && <details>
        <summary>{skipped.reduce((sum, [, n]) => sum + n, 0)} not added — see why</summary>
        <ul className="mono">{skipped.map(([state, n]) => <li key={state}>{n} {SKIP_LABELS[state]}</li>)}</ul>
        {!compact && job.items && <div className="scroll-x"><table className="plain"><thead><tr><th>Item</th><th>Source</th><th>Result</th><th>Reason</th></tr></thead>
          <tbody>{job.items.filter((item) => item.kind === 'candidate' && item.state !== 'added').map((item) => (
            <tr key={item.id}><td>{item.title ?? '—'}</td><td>{PROVIDERS[item.provider] ?? item.provider}</td><td>{item.state}</td><td>{item.reason}</td></tr>))}</tbody></table></div>}
      </details>}
      {!compact && job.items && job.items.some((item) => item.kind === 'query') && <details>
        <summary>Searches</summary>
        <ul className="mono">{job.items.filter((item) => item.kind === 'query').map((item) => <li key={item.id}>{PROVIDERS[item.provider]}: “{item.query}” — {item.state}{item.reason ? ` (${item.reason})` : ''}</li>)}</ul>
      </details>}
    </section>
  )
}
