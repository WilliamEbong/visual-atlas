import { useCallback } from 'react'
import { date, useData, usePoll } from '../lib/hooks'
import { href } from '../lib/router'
import type { Job } from '../lib/types'
import JobProgress from './JobProgress'

const KIND: Record<string, string> = { find: 'Find images', grow: 'Grow my library', verify: 'Second-model check', analyze: 'Analysis',
  compare: 'Comparison', directions: 'Project directions' }

export default function Jobs({ id }: { id?: string }) {
  const { data, error, reload } = useData<Job[]>(id ? null : 'jobs?limit=50')
  usePoll(useCallback(reload, [reload]), !id && !!data?.some((job) => ['queued', 'running', 'cancelling'].includes(job.state)), 3000)
  if (id) return <><p><a href="#/jobs">← All jobs</a></p><JobProgress jobId={id} /></>
  return (
    <div className="stack">
      <h1>Jobs</h1>
      <p className="lede">Searches and analyses run here in the background, one at a time. A job survives closing the app and continues when you reopen it.</p>
      {error && <p className="notice error" role="alert">{error}</p>}
      {data && data.length === 0 && <div className="empty"><p>No jobs yet.</p><a className="button primary" href="#/find">Find images</a></div>}
      {data && data.length > 0 && <div className="scroll-x"><table className="plain">
        <thead><tr><th>Started</th><th>Job</th><th>State</th><th>Result</th><th>Assistant</th></tr></thead>
        <tbody>{data.map((job) => (
          <tr key={job.id}>
            <td className="mono">{date(job.created_at)}</td>
            <td><a href={href(`jobs/${job.id}`)}>{KIND[job.kind] ?? job.kind}</a>{typeof job.spec.goal === 'string' && job.spec.goal ? <div className="mono">“{job.spec.goal.slice(0, 80)}”</div> : null}</td>
            <td>{job.state}</td><td>{job.message}</td><td className="mono">{job.backend}</td>
          </tr>))}</tbody></table></div>}
    </div>
  )
}
