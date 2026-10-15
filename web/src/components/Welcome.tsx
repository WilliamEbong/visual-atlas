import { useEffect, useRef } from 'react'
import { put } from '../lib/client'
import { useData } from '../lib/hooks'
import type { Settings } from '../lib/types'

/** First-run welcome: four plain steps, shown once. */
export default function Welcome() {
  const { data, setData } = useData<Settings>('settings')
  const dialog = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    if (data && !data.welcomed && dialog.current && !dialog.current.open) dialog.current.showModal()
  }, [data])
  async function close(target: string) {
    dialog.current?.close()
    try { setData(await put<Settings>('settings', { welcomed: true })) } catch { /* shown again next time */ }
    window.location.hash = target
  }
  return (
    <dialog ref={dialog} aria-labelledby="welcome-title" onCancel={() => close('#/')} style={{ maxWidth: 'min(620px, 92vw)', background: 'var(--ground)' }}>
      <p className="kicker">Visual Atlas · a library of ways of looking</p>
      <h2 id="welcome-title" style={{ fontSize: 40, marginTop: 6, paddingBottom: 14, borderBottom: '1px solid var(--axis)' }}>Welcome</h2>
      <ol className="trays" style={{ gridTemplateColumns: '1fr', gap: 14, listStyle: 'none', padding: 0, marginTop: 18 }}>
        <li className="tray-col rule-blue" style={{ paddingTop: 8 }}><strong className="label">Find images.</strong> Describe what you want to see; the atlas searches open museum and archive collections.</li>
        <li className="tray-col rule-green" style={{ paddingTop: 8 }}><strong className="label">Only free-to-use pictures are kept.</strong> Each licence is checked against the source's own record, and the credit is saved.</li>
        <li className="tray-col rule-ochre" style={{ paddingTop: 8 }}><strong className="label">Learn why they work.</strong> An assistant on your computer (Codex or Claude Code, with your own sign-in) describes what it sees and names the techniques. You can confirm or correct every reading.</li>
        <li className="tray-col rule-rust" style={{ paddingTop: 8 }}><strong className="label">Use them.</strong> Save images to collections, compare them, and ask for directions for your own project.</li>
      </ol>
      <p className="mono" style={{ marginTop: 18 }}>Your library stays on this computer. Searches go to the collections. When an assistant is used, the
        request it needs goes to that assistant's service (OpenAI or Anthropic, under your own account): the picture and its
        catalogue details for an analysis, or your brief and short summaries of library images for project directions.</p>
      <div className="row" style={{ justifyContent: 'flex-start', marginTop: 20 }}>
        <button type="button" className="primary" onClick={() => close('#/find')}>Find my first images</button>
        <button type="button" onClick={() => close('#/settings')}>Check AI setup</button>
        <button type="button" className="quiet" onClick={() => close('#/')}>Look around first</button>
      </div>
    </dialog>
  )
}
