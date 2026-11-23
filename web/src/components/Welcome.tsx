import { useEffect, useRef } from 'react'
import { put } from '../lib/client'
import { useData } from '../lib/hooks'
import type { Settings } from '../lib/types'

/** First-run welcome: five plain steps, shown once. */
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
    <dialog ref={dialog} aria-labelledby="welcome-title" onCancel={() => close('#/library')} style={{ maxWidth: 'min(620px, 92vw)', background: 'var(--ground)' }}>
      <p className="kicker">Visual Atlas · a library of ways of looking</p>
      <h2 id="welcome-title" style={{ fontSize: 40, marginTop: 6 }}>Welcome</h2>
      <ol className="trays" style={{ gridTemplateColumns: '1fr', gap: 14, listStyle: 'none', padding: 0, marginTop: 18 }}>
        <li className="tray-col welcome-step" style={{ paddingTop: 8 }}><strong className="label">Ask.</strong> Say what a picture should do, like “a calm opening slide”. You get ways to do it and pictures that show them, each with its reason and licence. No AI is used.</li>
        <li className="tray-col welcome-step" style={{ paddingTop: 8 }}><strong className="label">Find images.</strong> Describe what you want to see; the atlas searches open museum and archive collections.</li>
        <li className="tray-col welcome-step" style={{ paddingTop: 8 }}><strong className="label">Only free-to-use pictures are kept.</strong> Each licence is checked against the source's own record, and the credit is saved.</li>
        <li className="tray-col welcome-step" style={{ paddingTop: 8 }}><strong className="label">Learn why they work.</strong> Codex or Claude Code, under your own sign-in, names the techniques in each picture. You confirm or correct every reading.</li>
        <li className="tray-col welcome-step" style={{ paddingTop: 8 }}><strong className="label">Use them.</strong> Save images to collections, compare them, and ask for directions for your own project.</li>
      </ol>
      <p className="muted" style={{ marginTop: 18, fontSize: 14, lineHeight: 1.5 }}>Your library stays on this computer. When an assistant runs, the picture or your brief goes to OpenAI or
        Anthropic under your own account. Searches go to the collections.</p>
      <div className="row" style={{ justifyContent: 'flex-start', marginTop: 20 }}>
        <button type="button" className="primary" onClick={() => close('#/ask')}>Ask the atlas</button>
        <button type="button" onClick={() => close('#/find')}>Find new images</button>
        <button type="button" className="quiet" onClick={() => close('#/library')}>Go to the library</button>
      </div>
    </dialog>
  )
}
