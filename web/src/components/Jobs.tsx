import { useCallback } from 'react'
import { date, useData, usePoll } from '../lib/hooks'
import { href } from '../lib/router'
import type { Job } from '../lib/types'
import JobProgress from './JobProgress'
import { Empty, Failure, Loading, PageHead } from './ui'

const KIND: Record<string, string> = { find: 'Find images', grow: 'Grow my library', verify: 'Second-model check', analyze: 'Analysis',
  compare: 'Comparison', directions: 'Project directions' }

export default function Jobs({ id }: { id?: string }) {
  const { data, error, busy, reload } = useData<Job[]>(id ? null : 'jobs?limit=50')
  usePoll(useCallback(reload, [reload]), !id && !!data?.some((job) => ['queued', 'running', 'cancelling'].includes(job.state)), 3000)
  if (id) return <><PageHead kicker={<><a href="#/jobs">Jobs</a> / {id.slice(0, 8)}</>} title="Job" /><div style={{ marginTop: 32, maxWidth: 900 }}><JobProgress jobId={id} /></div></>
  return (
    <>
      <PageHead kicker="Jobs · one at a time, in the background" title="Jobs" />
      <p className="lede under">Searches and analyses run here in the background, one at a time. A job survives closing the app and continues when you reopen it.</p>
      {error ? <Failure message={error} busy={busy} retry={reload} /> : !data ? <Loading plates={false} />
        : data.length === 0 ? <Empty title="No jobs yet" actions={<a className="button primary" href="#/find">Find images</a>}>Find images or ask for project directions, and the work appears here.</Empty>
        : <div className="scroll-x" style={{ marginTop: 32 }}><table className="plain">
          <thead><tr><th scope="col">Started</th><th scope="col">Job</th><th scope="col">State</th><th scope="col">Result</th><th scope="col">Assistant</th></tr></thead>
          <tbody>{data.map((job) => (
            <tr key={job.id}>
              <td className="mono">{date(job.created_at)}</td>
              <td><a href={href(`jobs/${job.id}`)}>{KIND[job.kind] ?? job.kind}</a>{typeof job.spec.goal === 'string' && job.spec.goal ? <div className="mono">“{job.spec.goal.slice(0, 80)}”</div> : null}</td>
              <td>{job.state}</td><td>{job.message}</td><td className="mono">{job.backend}</td>
            </tr>))}</tbody></table></div>}
    </>
  )
}
