import { useCallback, useEffect, useState } from 'react'
import { media, readOnly, request } from './lib/client'
import { AppContext, useData, usePoll, type Pick } from './lib/hooks'
import { href, useRoute } from './lib/router'
import type { Job, Taxonomy } from './lib/types'
import Collections from './components/Collections'
import Compare from './components/Compare'
import Connections from './components/Connections'
import Explore from './components/Explore'
import Find from './components/Find'
import ImagePage from './components/ImagePage'
import Jobs from './components/Jobs'
import Library from './components/Library'
import Project from './components/Project'
import SettingsPage from './components/Settings'
import Welcome from './components/Welcome'

const NAV = [['', 'Library'], ['find', 'Find images'], ['explore', 'Explore'], ['project', 'My project'],
  ['collections', 'Collections'], ['jobs', 'Jobs'], ['settings', 'Settings']] as const

function readCompare(): Pick[] {
  try { return JSON.parse(sessionStorage.getItem('compare') ?? '[]') } catch { return [] }
}

export default function App() {
  const route = useRoute()
  const section = route.path[0] ?? ''
  const taxonomy = useData<Taxonomy>('taxonomy')
  const [compare, setCompare] = useState<Pick[]>(readCompare)
  const [running, setRunning] = useState<Job | null>(null)
  useEffect(() => { try { sessionStorage.setItem('compare', JSON.stringify(compare)) } catch { /* private mode */ } }, [compare])
  const toggleCompare = useCallback((pick: Pick) => setCompare((picks) => picks.some((p) => p.id === pick.id)
    ? picks.filter((p) => p.id !== pick.id) : picks.length >= 4 ? picks : [...picks, pick]), [])
  const checkJobs = useCallback(() => {
    if (readOnly) return
    request<Job[]>('jobs?limit=5').then((jobs) => setRunning(jobs.find((job) => ['queued', 'running', 'cancelling'].includes(job.state)) ?? null))
      .catch(() => setRunning(null))
  }, [])
  useEffect(checkJobs, [checkJobs, section])
  usePoll(checkJobs, true, running ? 3000 : 30000)  // the 30 s ping also tells the launcher the window is open
  useEffect(() => {
    if (section !== 'image') document.title = `${NAV.find(([key]) => key === section)?.[1] ?? 'Visual Atlas'} · Visual Atlas`
  }, [section])

  let page
  switch (section) {
    case 'image': page = <ImagePage id={Number(route.path[1])} />; break
    case 'find': page = <Find />; break
    case 'jobs': page = <Jobs id={route.path[1]} />; break
    case 'explore': page = <Explore route={route} />; break
    case 'technique': page = <Explore route={{ path: ['explore', 'technique', route.path[1]], query: route.query }} />; break
    case 'connections': page = <Connections focus={route.query.get('focus') ?? ''} />; break
    case 'project': page = <Project id={route.path[1] ? Number(route.path[1]) : undefined} />; break
    case 'collections': page = <Collections id={route.path[1] ? Number(route.path[1]) : undefined} />; break
    case 'compare': page = <Compare ids={(route.query.get('ids') ?? compare.map((p) => p.id).join(',')).split(',').map(Number).filter(Boolean)} />; break
    case 'settings': page = <SettingsPage />; break
    default: page = <Library query={route.query} />
  }

  return (
    <AppContext.Provider value={{ taxonomy: taxonomy.data, compare, toggleCompare, clearCompare: () => setCompare([]), refreshTaxonomy: taxonomy.reload }}>
      <a className="skip" href="#content" onClick={(event) => { event.preventDefault(); document.getElementById('content')?.focus() }}>Skip to content</a>
      <header className="topbar">
        <a className="brand" href="#/">Visual Atlas</a>
        <nav className="nav" aria-label="Main">
          {NAV.map(([key, label]) => (
            <a key={key} href={`#/${key}`} aria-current={section === key || (key === 'explore' && section === 'technique') ? 'page' : undefined}>{label}</a>
          ))}
        </nav>
        {readOnly ? <span className="status-line">Read-only online demo</span>
          : running && <a className="status-line" href={href(`jobs/${running.id}`)}>1 job running · {running.message || running.stage}</a>}
      </header>
      <main id="content" tabIndex={-1}>{page}</main>
      {!readOnly && <Welcome />}
      {compare.length > 0 && section !== 'compare' && (
        <div className="tray" role="region" aria-label="Images chosen for comparison">
          <span>Compare ({compare.length}/4)</span>
          <span className="row">{compare.map((p) => <img key={p.id} alt={p.title} src={media(p.thumb)} />)}</span>
          {compare.length >= 2 ? <a className="button" href={href('compare', { ids: compare.map((p) => p.id).join(',') })}>Compare side by side</a>
            : <span>Pick at least one more image</span>}
          <button type="button" onClick={() => setCompare([])}>Clear</button>
        </div>
      )}
    </AppContext.Provider>
  )
}
