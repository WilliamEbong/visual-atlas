// Shared pieces every screen is built from: the horizon header, the four data states (loading, empty, failure,
// busy), notices with Undo, and an in-app confirmation for things that cannot be undone.
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { BusyError } from '../lib/client'

export function PageHead({ kicker, title, aside, asideClass = '', id = 'page-title' }: {
  kicker?: ReactNode; title: ReactNode; aside?: ReactNode; asideClass?: string; id?: string
}) {
  return (
    <section className="horizon-head" aria-labelledby={id}>
      <div className="head-text">
        {kicker && <p className="kicker">{kicker}</p>}
        <h1 id={id}>{title}</h1>
      </div>
      {aside && <div className={`head-aside ${asideClass}`}>{aside}</div>}
    </section>
  )
}

const SHAPES = [1.5, 0.75, 1.3, 0.6, 1.8, 1]

export function Loading({ label = 'Loading…', plates = true }: { label?: string; plates?: boolean }) {
  return (
    <div>
      {plates && <div className="skeleton" aria-hidden="true">
        {SHAPES.map((a, index) => <div key={index} style={{ '--a': a } as React.CSSProperties}>
          <div className="block" /><div className="line" /><div className="line long" /></div>)}
      </div>}
      <p className="mono" role="status" style={{ marginTop: 14 }}>{label}</p>
    </div>
  )
}

export function Empty({ title, children, actions }: { title: string; children?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      {children && <p>{children}</p>}
      {actions && <div className="row">{actions}</div>}
    </div>
  )
}

/** A failed load, or the library busy with maintenance (nothing failed: try again in a moment). */
export function Failure({ message, busy = false, retry }: { message: string; busy?: boolean; retry?: () => void }) {
  return (
    <div className={`failure${busy ? ' busy' : ''}`} role="alert">
      <p className="label">{busy ? 'The library is busy' : 'This did not load'}</p>
      <p className="muted" style={{ fontSize: 14 }}>{busy ? `${message} Nothing you did is lost.` : message}</p>
      {retry && <div className="row"><button type="button" className="small" onClick={retry}>Try again</button></div>}
    </div>
  )
}

interface Notice { id: number; text: string; tone: 'info' | 'error'; undo?: () => unknown }
interface NoticeApi {
  notify: (text: string, options?: { undo?: () => unknown; tone?: 'info' | 'error' }) => void
  fail: (reason: unknown) => void
  confirm: (options: ConfirmOptions) => Promise<boolean>
}
interface ConfirmOptions { title: string; body: ReactNode; confirm: string; cancel?: string; danger?: boolean }

const NoticeContext = createContext<NoticeApi>({ notify: () => {}, fail: () => {}, confirm: async () => false })
export const useNotice = () => useContext(NoticeContext)

/** Notices sit bottom left for 8 s (paused while hovered or focused); Undo replays the inverse action.
 *  The confirm function opens a modal dialog: Escape or the safe button answers false, focus returns to where it was. */
export function NoticeProvider({ children }: { children: ReactNode }) {
  const [notices, setNotices] = useState<Notice[]>([])
  const counter = useRef(0)
  const dismiss = useCallback((id: number) => setNotices((list) => list.filter((n) => n.id !== id)), [])
  const notify = useCallback((text: string, options: { undo?: () => unknown; tone?: 'info' | 'error' } = {}) => {
    const id = ++counter.current
    setNotices((list) => [...list.slice(-2), { id, text, tone: options.tone ?? 'info', undo: options.undo }])
  }, [])
  const fail = useCallback((reason: unknown) => {
    const message = reason instanceof Error ? reason.message : String(reason)
    notify(reason instanceof BusyError ? `The library is busy: ${message}` : message, { tone: 'error' })
  }, [notify])

  const dialog = useRef<HTMLDialogElement>(null)
  const [asking, setAsking] = useState<(ConfirmOptions & { answer: (value: boolean) => void }) | null>(null)
  const returnTo = useRef<HTMLElement | null>(null)
  const confirm = useCallback((options: ConfirmOptions) => new Promise<boolean>((resolve) => {
    returnTo.current = document.activeElement as HTMLElement | null
    setAsking({ ...options, answer: resolve })
  }), [])
  useEffect(() => { if (asking && dialog.current && !dialog.current.open) dialog.current.showModal() }, [asking])
  function answer(value: boolean) {
    asking?.answer(value)
    dialog.current?.close()
    setAsking(null)
    returnTo.current?.focus?.()
  }

  return (
    <NoticeContext.Provider value={{ notify, fail, confirm }}>
      {children}
      <div className="toasts" aria-live="polite" role="status">
        {notices.map((notice) => <Toast key={notice.id} notice={notice} onDone={() => dismiss(notice.id)} />)}
      </div>
      <dialog ref={dialog} aria-labelledby="confirm-title" onCancel={(event) => { event.preventDefault(); answer(false) }}>
        {asking && <>
          <h2 id="confirm-title">{asking.title}</h2>
          <p className="muted" style={{ marginTop: 10 }}>{asking.body}</p>
          <div className="row">
            <button type="button" autoFocus onClick={() => answer(false)}>{asking.cancel ?? 'Keep it'}</button>
            <button type="button" className={asking.danger ? 'danger primary' : 'primary'} onClick={() => answer(true)}>{asking.confirm}</button>
          </div>
        </>}
      </dialog>
    </NoticeContext.Provider>
  )
}

function Toast({ notice, onDone }: { notice: Notice; onDone: () => void }) {
  const [held, setHeld] = useState(false)
  useEffect(() => {
    if (held) return
    const timer = window.setTimeout(onDone, notice.tone === 'error' ? 12000 : 8000)
    return () => window.clearTimeout(timer)
  }, [held, notice.tone, onDone])
  return (
    <div className={`toast ${notice.tone}`} role={notice.tone === 'error' ? 'alert' : undefined}
      onMouseEnter={() => setHeld(true)} onMouseLeave={() => setHeld(false)} onFocus={() => setHeld(true)} onBlur={() => setHeld(false)}>
      <span>{notice.text}</span>
      <span className="row" style={{ gap: 14, flexWrap: 'nowrap' }}>
        {notice.undo && <button type="button" onClick={async () => { onDone(); await notice.undo!() }}>Undo</button>}
        <button type="button" className="close" aria-label="Dismiss notice" onClick={onDone}>×</button>
      </span>
    </div>
  )
}
