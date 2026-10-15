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
    <dialog ref={dialog} aria-labelledby="welcome-title" onCancel={() => close('#/')}>
      <div className="stack">
        <h2 id="welcome-title">Welcome to Visual Atlas</h2>
        <ol className="observations">
          <li><strong>Find images.</strong> Describe what you want to see. The atlas searches five open museum and archive collections.</li>
          <li><strong>Only free-to-use pictures are kept.</strong> Each licence is checked against the source's own record, and the credit is saved.</li>
          <li><strong>Learn why they work.</strong> An assistant on your computer (Codex or Claude Code, with your own sign-in) describes what it sees and names the techniques. You can confirm or correct every reading.</li>
          <li><strong>Use them.</strong> Save images to collections, compare them, and ask for directions for your own project.</li>
        </ol>
        <p className="mono">Nothing leaves your computer except searches to the collections and the images you choose to analyse.</p>
        <div className="row">
          <button type="button" className="primary" onClick={() => close('#/find')}>Find my first images</button>
          <button type="button" onClick={() => close('#/settings')}>Check AI setup</button>
          <button type="button" className="quiet" onClick={() => close('#/')}>Look around first</button>
        </div>
      </div>
    </dialog>
  )
}
