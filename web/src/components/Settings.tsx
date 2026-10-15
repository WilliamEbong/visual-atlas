import { useEffect, useState } from 'react'
import { download, post, put, readOnly, request } from '../lib/client'
import { date, useData } from '../lib/hooks'
import type { Settings } from '../lib/types'

interface Status { ready: boolean; version: string; code?: string; message: string }
interface Source { id: string; name: string; status: string; rule?: string; reason?: string; label?: string; attribution?: string
  evidence_urls: string[]; checked_on: string; notes?: string }
interface Backup { name: string; size_bytes: number; created: string }

const SIGN_IN: Record<string, string> = {
  codex: 'Install the Codex CLI (npm install -g @openai/codex), then run “codex login” in a terminal and sign in with your ChatGPT account.',
  claude: 'Install Claude Code (see claude.com/claude-code), then run “claude” in a terminal and sign in with your Claude subscription.',
}

function theme(value?: string) {
  const root = document.documentElement
  if (!value || value === 'auto') root.removeAttribute('data-theme'); else root.setAttribute('data-theme', value)
}
try { theme(localStorage.getItem('theme') ?? 'auto') } catch { /* storage blocked */ }

export default function SettingsPage() {
  const settings = useData<Settings>(readOnly ? null : 'settings')
  const sources = useData<Source[]>('sources')
  const [status, setStatus] = useState<Record<string, Status> | null>(null)
  const [checking, setChecking] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [mode, setMode] = useState(() => { try { return localStorage.getItem('theme') ?? 'auto' } catch { return 'auto' } })
  useEffect(() => { theme(mode); try { localStorage.setItem('theme', mode) } catch { /* ignore */ } }, [mode])

  async function check(refresh: boolean) {
    setChecking(true)
    try { setStatus(await request<Record<string, Status>>(`ai/status${refresh ? '?refresh=true' : ''}`)) }
    catch (reason) { setMessage((reason as Error).message) } finally { setChecking(false) }
  }
  useEffect(() => { if (!readOnly) check(false) }, [])
  async function save(change: Partial<Settings>) {
    try { settings.setData(await put<Settings>('settings', change)); setMessage('Saved.') } catch (reason) { setMessage((reason as Error).message) }
  }

  return (
    <div className="stack">
      <h1>Settings</h1>
      {message && <p className="notice" role="status">{message}</p>}
      {!readOnly && <section className="stack" aria-labelledby="ai">
        <h2 id="ai">AI setup</h2>
        <p className="muted">Visual Atlas uses the assistants already on this computer, with your own subscription sign-in. It never sees or stores your password or tokens. Browsing, searching and collections work without any AI.</p>
        <div className="compare-grid">
          {(['codex', 'claude'] as const).map((name) => (
            <div key={name} className="notice stack">
              <h3>{name === 'codex' ? 'Codex (ChatGPT plan)' : 'Claude Code (Claude plan)'}</h3>
              {status ? <p><strong>{status[name].ready ? '● Ready' : '○ Not ready'}</strong>{status[name].ready ? '' : ` — ${status[name].message}`}{status[name].version && status[name].version !== 'unknown' ? ` (version ${status[name].version})` : ''}</p>
                : <p className="mono">Checking…</p>}
              {status && !status[name].ready && <p>{SIGN_IN[name]}</p>}
            </div>))}
        </div>
        <p><button type="button" disabled={checking} onClick={() => check(true)}>{checking ? 'Checking…' : 'Check again'}</button></p>
        {settings.data && <div className="filters">
          <label className="field">Analyses images<select value={settings.data.backend} onChange={(e) => save({ backend: e.target.value as Settings['backend'] })}>
            <option value="codex">Codex</option><option value="claude">Claude Code</option><option value="fake">Practice mode (no AI)</option></select></label>
          <label className="field">Second-model check<select value={settings.data.verify_with} onChange={(e) => save({ verify_with: e.target.value as Settings['verify_with'] })}>
            <option value="claude">Claude Code</option><option value="codex">Codex</option><option value="none">None</option></select></label>
          <label className="field">Daily AI limit (calls)<input type="number" min={0} max={1000} defaultValue={settings.data.daily_ai_cap}
            onBlur={(e) => save({ daily_ai_cap: Number(e.target.value) })} /></label>
        </div>}
        <p className="mono">A second-model agreement is shown as “agreed by a second model”. Only your own decisions count as reviewed by you.</p>
      </section>}

      <section className="stack" aria-labelledby="look">
        <h2 id="look">Appearance</h2>
        <div className="row" role="radiogroup" aria-label="Theme">
          {[['auto', 'Match my computer'], ['light', 'Light'], ['dark', 'Dark']].map(([value, label]) =>
            <label key={value} className="choice"><input type="radio" name="theme" checked={mode === value} onChange={() => setMode(value)} /> {label}</label>)}
        </div>
      </section>

      <section className="stack" aria-labelledby="sources">
        <h2 id="sources">Image sources and permissions</h2>
        <p className="muted">Images are only added when the source's own record shows a licence that allows keeping a copy, showing it and analysing it. That check is ordinary code reading the museum's fields — never an AI's opinion. Unclear means skipped.</p>
        <div className="scroll-x"><table className="plain">
          <thead><tr><th>Source</th><th>Status</th><th>Rule or reason</th><th>Evidence</th></tr></thead>
          <tbody>{sources.data?.map((s) => (
            <tr key={s.id}><td>{s.name}</td><td>{s.status === 'enabled' ? '● used' : s.status === 'disabled' ? '✕ not used' : '○ candidate'}</td>
              <td>{s.rule ?? s.reason}{s.notes ? <div className="mono">{s.notes}</div> : null}</td>
              <td className="mono">{s.evidence_urls.map((u, i) => <div key={u}><a href={u} target="_blank" rel="noreferrer">link {i + 1}</a></div>)}checked {s.checked_on}</td></tr>))}</tbody>
        </table></div>
      </section>

      {!readOnly && <Backups onMessage={setMessage} />}
    </div>
  )
}

function Backups({ onMessage }: { onMessage: (text: string) => void }) {
  const { data, reload } = useData<Backup[]>('backups')
  const health = useData<{ version: string; home: string }>('health')
  const [busy, setBusy] = useState(false)
  const [confirm, setConfirm] = useState<string | null>(null)
  async function run(work: () => Promise<unknown>, done: string) {
    setBusy(true)
    try { await work(); onMessage(done); reload() } catch (reason) { onMessage((reason as Error).message) } finally { setBusy(false) }
  }
  return (
    <section className="stack" aria-labelledby="backup">
      <h2 id="backup">Backups and exports</h2>
      <p className="muted">A backup holds the whole library: database, images and annotations. Restoring first makes a safety backup of what you have now.</p>
      <div className="row">
        <button type="button" className="primary" disabled={busy} onClick={() => run(() => post('backups'), 'Backup made.')}>Back up now</button>
        <button type="button" onClick={() => run(() => download('export/credits?format=md', 'credits.md'), 'Credits downloaded.')}>Download all credits (Markdown)</button>
        <button type="button" onClick={() => run(() => download('export/credits?format=csv', 'credits.csv'), 'Credits downloaded.')}>Credits as CSV</button>
      </div>
      {data?.length ? <div className="scroll-x"><table className="plain"><thead><tr><th>Backup</th><th>Made</th><th>Size</th><th /></tr></thead>
        <tbody>{data.map((b) => <tr key={b.name}><td className="mono">{b.name}</td><td>{date(b.created)}</td><td>{(b.size_bytes / 1048576).toFixed(1)} MB</td>
          <td>{confirm === b.name ? <span className="row">Replace the current library with this backup?
            <button type="button" className="danger" disabled={busy} onClick={() => run(() => post(`backups/${encodeURIComponent(b.name)}/restore`), 'Restored. A safety backup of the previous state was made.').then(() => setConfirm(null))}>Restore</button>
            <button type="button" onClick={() => setConfirm(null)}>Cancel</button></span>
            : <button type="button" onClick={() => setConfirm(b.name)}>Restore…</button>}</td></tr>)}</tbody></table></div>
        : <p className="muted">No backups yet.</p>}
      {health.data && <p className="mono">Your library folder: {health.data.home} · Visual Atlas {health.data.version}</p>}
    </section>
  )
}
