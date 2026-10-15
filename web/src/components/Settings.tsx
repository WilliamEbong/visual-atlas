import { useEffect, useState } from 'react'
import { download, post, put, readOnly, request } from '../lib/client'
import { date, useData } from '../lib/hooks'
import type { Settings } from '../lib/types'
import type { Source } from './Find'
import { Failure, Loading, PageHead, useNotice } from './ui'

interface Status { ready: boolean; version: string; code?: string; message: string }
interface Backup { name: string; size_bytes: number; created: string }

const SIGN_IN: Record<string, string> = {
  codex: 'Install the Codex CLI (npm install -g @openai/codex), then run “codex login” in a terminal and sign in with your ChatGPT account.',
  claude: 'Install Claude Code (see claude.com/claude-code), then run “claude” in a terminal and sign in with your Claude subscription.',
}
const SECTIONS = [['assistants', 'Assistants'], ['sources', 'Sources'], ['help', 'Project help'], ['backups', 'Backups and restore'],
  ['appearance', 'Appearance'], ['privacy', 'Privacy']] as const

function theme(value?: string) {
  const root = document.documentElement
  if (!value || value === 'auto') root.removeAttribute('data-theme'); else root.setAttribute('data-theme', value)
}
try { theme(localStorage.getItem('theme') ?? 'auto') } catch { /* storage blocked */ }

export default function SettingsPage() {
  const settings = useData<Settings>(readOnly ? null : 'settings')
  const sources = useData<Source[]>('sources')
  const health = useData<{ version: string; home: string }>(readOnly ? null : 'health')
  const { notify, fail } = useNotice()
  const [status, setStatus] = useState<Record<string, Status> | null>(null)
  const [checking, setChecking] = useState(false)
  const [here, setHere] = useState('assistants')
  const [mode, setMode] = useState(() => { try { return localStorage.getItem('theme') ?? 'auto' } catch { return 'auto' } })
  useEffect(() => { theme(mode); try { localStorage.setItem('theme', mode) } catch { /* ignore */ } }, [mode])

  async function check(refresh: boolean) {
    setChecking(true)
    try { setStatus(await request<Record<string, Status>>(`ai/status${refresh ? '?refresh=true' : ''}`)) }
    catch (reason) { fail(reason) } finally { setChecking(false) }
  }
  useEffect(() => { if (!readOnly) check(false) }, []) // eslint-disable-line react-hooks/exhaustive-deps
  async function save(change: Partial<Settings>) {
    try { settings.setData(await put<Settings>('settings', change)); notify('Saved.') } catch (reason) { fail(reason) }
  }
  function jump(id: string) {
    setHere(id)
    const heading = document.getElementById(id)
    heading?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    heading?.focus({ preventScroll: true })
  }
  const shown = SECTIONS.filter(([id]) => !readOnly || ['sources', 'appearance', 'privacy'].includes(id))

  return (
    <>
      <PageHead kicker={health.data ? `Settings · library at ${health.data.home} · version ${health.data.version}` : 'Settings'} title="Settings" />
      <div className="split" style={{ marginTop: 32, gap: 56 }}>
        <nav className="side-nav" aria-label="Settings sections">
          {shown.map(([id, label]) => <button key={id} type="button" aria-current={here === id ? 'true' : undefined} onClick={() => jump(id)}>{label}</button>)}
        </nav>
        <div className="main-col stack" style={{ gap: 64 }}>
          {!readOnly && <section className="stack" aria-labelledby="assistants">
            <h2 id="assistants" tabIndex={-1}>Assistants</h2>
            <p className="muted" style={{ maxWidth: 760 }}>Visual Atlas uses the assistants already on this computer, with your own subscription sign-in. Browsing, searching and collections work without any AI.</p>
            <div className="trays" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
              {(['codex', 'claude'] as const).map((name) => (
                <div key={name} className="status-card">
                  <div className="section-title"><span className="label" style={{ fontSize: 17 }}>{name === 'codex' ? 'Codex (ChatGPT plan)' : 'Claude Code (Claude plan)'}</span>
                    <span className="mono" style={{ color: !status ? 'var(--graphite)' : status[name].ready ? 'var(--green-strong)' : 'var(--danger)' }}>{status ? (status[name].ready ? 'Ready' : 'Not ready') : 'Checking…'}</span></div>
                  {status && <p className="mono" style={{ color: 'var(--graphite)' }}>{status[name].ready ? `Signed in${status[name].version && status[name].version !== 'unknown' ? ` · version ${status[name].version}` : ''}` : status[name].message}</p>}
                  {status && !status[name].ready && <p style={{ fontSize: 14 }}>{SIGN_IN[name]}</p>}
                </div>))}
            </div>
            <div><button type="button" className="small" disabled={checking} onClick={() => check(true)}>{checking ? 'Checking…' : 'Check again'}</button></div>
            {settings.error ? <Failure message={settings.error} busy={settings.busy} retry={settings.reload} /> : settings.data && <div className="filters">
              <label className="field">Analyses images<select value={settings.data.backend} onChange={(e) => save({ backend: e.target.value as Settings['backend'] })}>
                <option value="codex">Codex</option><option value="claude">Claude Code</option><option value="fake">Practice mode (no AI)</option></select></label>
              <label className="field">Checks the readings<select value={settings.data.verify_with} onChange={(e) => save({ verify_with: e.target.value as Settings['verify_with'] })}>
                <option value="claude">Claude Code</option><option value="codex">Codex</option><option value="none">No second check</option></select></label>
              <label className="field">Daily AI limit (calls)<input type="number" min={0} max={1000} defaultValue={settings.data.daily_ai_cap}
                onBlur={(e) => save({ daily_ai_cap: Number(e.target.value) })} /></label>
            </div>}
            <p className="mono">A second model's agreement is shown as “agreed by a second model”. Only your own decisions count as confirmed by you.</p>
          </section>}

          <section className="stack" aria-labelledby="sources">
            <div className="section-title"><h2 id="sources" tabIndex={-1}>Sources</h2>
              <span className="mono">Each rule reads the source's own record; an assistant never decides permission</span></div>
            {sources.error ? <Failure message={sources.error} busy={sources.busy} retry={sources.reload} /> : !sources.data ? <Loading plates={false} />
              : <div className="scroll-x"><table className="plain">
                <thead><tr><th scope="col">Source</th><th scope="col">Status</th><th scope="col">Accepted when</th><th scope="col">Evidence</th></tr></thead>
                <tbody>{sources.data.map((s) => (
                  <tr key={s.id}><th scope="row" style={{ minWidth: 190 }}><span className="label" style={{ fontSize: 15 }}>{s.name}</span></th>
                    <td className="mono" style={{ color: s.status === 'enabled' ? 'var(--green)' : 'var(--caption)', whiteSpace: 'nowrap' }}>{s.status === 'enabled' ? 'Used' : s.status === 'disabled' ? 'Not used' : 'Candidate'}</td>
                    <td>{s.rule ?? s.reason}{s.notes ? <div className="mono" style={{ marginTop: 4 }}>{s.notes}</div> : null}</td>
                    <td className="mono">{s.evidence_urls.map((u, i) => <div key={u}><a href={u} target="_blank" rel="noreferrer">source {i + 1}</a></div>)}checked {s.checked_on}</td></tr>))}</tbody>
              </table></div>}
          </section>

          {!readOnly && settings.data && <section className="stack" aria-labelledby="help">
            <h2 id="help" tabIndex={-1}>Project help</h2>
            <div className="status-card" style={{ background: 'transparent' }}>
              <label className="choice plain" style={{ alignItems: 'flex-start' }}><input type="checkbox" checked={settings.data.jev_ranking} disabled={!settings.data.jev_key}
                onChange={(e) => save({ jev_ranking: e.target.checked })} style={{ marginTop: 3 }} />
                <span><span className="label">Rank references with TypeSafe Jev</span><br />
                  <span style={{ fontSize: 14 }} className="muted">Optional and off by default. Jev reorders which library images are offered to the assistant for your brief (in the v1.1 evaluation it found more of the relevant ones). Your brief and the titles, makers, dates, summaries and technique names of up to 120 library images go to TypeSafe, billed to your own account (usually a fraction of a cent per brief). No picture is sent. If it fails, the built-in ranking is used.</span></span></label>
              {!settings.data.jev_key && <p className="mono">No key found. Add TYPESAFE_API_KEY=… to the .env file in your library folder, then reopen Settings.</p>}
            </div>
          </section>}

          {!readOnly && <Backups />}

          <section className="stack" aria-labelledby="appearance">
            <h2 id="appearance" tabIndex={-1}>Appearance</h2>
            <fieldset><legend>Theme</legend>
              <div className="segments" role="radiogroup" aria-label="Theme">
                {[['auto', 'Match my computer'], ['light', 'Light'], ['dark', 'Dark']].map(([value, label]) =>
                  <label key={value} className="choice"><input type="radio" name="theme" checked={mode === value} onChange={() => setMode(value)} /> {label}</label>)}
              </div></fieldset>
          </section>

          <section className="stack" aria-labelledby="privacy" style={{ marginBottom: 48 }}>
            <h2 id="privacy" tabIndex={-1}>Privacy</h2>
            <p style={{ maxWidth: 760 }}>Your library stays in its folder on this computer. Searches go to the open collections. When an assistant is used, what it needs goes to that assistant's service under your own account (OpenAI for Codex, Anthropic for Claude Code): the picture and its catalogue details for an analysis, or your brief and short summaries of library images for project directions. Visual Atlas never sees or stores your passwords or tokens.</p>
          </section>
        </div>
      </div>
    </>
  )
}

function Backups() {
  const { data, error, busy: unavailable, reload } = useData<Backup[]>('backups')
  const { notify, fail, confirm } = useNotice()
  const [busy, setBusy] = useState(false)
  async function run(work: () => Promise<unknown>, done: string) {
    setBusy(true)
    try { await work(); notify(done); reload() } catch (reason) { fail(reason) } finally { setBusy(false) }
  }
  async function restore(name: string) {
    const sure = await confirm({ title: 'Restore this backup?', confirm: 'Restore', danger: true,
      body: `The library is replaced by the backup “${name}”. A safety backup of what you have now is made first, so you can go back.` })
    if (sure) run(() => post(`backups/${encodeURIComponent(name)}/restore`), 'Restored. A safety backup of the previous state was made.')
  }
  return (
    <section className="stack" aria-labelledby="backups">
      <h2 id="backups" tabIndex={-1}>Backups and restore</h2>
      <p className="muted">A backup holds the whole library: database, images and readings. Restoring first makes a safety backup of what you have now.</p>
      <div className="row">
        <button type="button" className="primary" disabled={busy} onClick={() => run(() => post('backups'), 'Backup made.')}>Back up now</button>
        <button type="button" onClick={() => run(() => download('export/credits?format=md', 'credits.md'), 'Credits downloaded.')}>All credits (Markdown)</button>
        <button type="button" onClick={() => run(() => download('export/credits?format=csv', 'credits.csv'), 'Credits downloaded.')}>Credits as CSV</button>
      </div>
      {error ? <Failure message={error} busy={unavailable} retry={reload} /> : !data ? <Loading plates={false} />
        : data.length ? <div className="scroll-x"><table className="plain"><thead><tr><th scope="col">Backup</th><th scope="col">Made</th><th scope="col">Size</th><th scope="col"><span className="sr-only">Action</span></th></tr></thead>
          <tbody>{data.map((b) => <tr key={b.name}><td className="mono">{b.name}</td><td>{date(b.created)}</td><td>{(b.size_bytes / 1048576).toFixed(1)} MB</td>
            <td><button type="button" className="small" disabled={busy} onClick={() => restore(b.name)}>Restore…</button></td></tr>)}</tbody></table></div>
        : <p className="muted">No backups yet.</p>}
    </section>
  )
}
