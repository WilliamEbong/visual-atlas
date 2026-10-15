// Talks to the local server with the per-launch token (pattern from Qualia). In the public demo build
// (VITE_DEMO=1) requests are answered read-only from a bundled snapshot.
import { demoRequest } from './demo'

export const readOnly = import.meta.env.VITE_DEMO === '1'

function token(): string {
  return document.querySelector<HTMLMetaElement>('meta[name="atlas-token"]')?.content ?? ''
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (readOnly) return demoRequest<T>(path, init)
  const response = await fetch(`/api/${path}`, {
    ...init, headers: { 'Content-Type': 'application/json', 'X-Atlas-Token': token(), ...init?.headers },
  })
  const data = await response.json().catch(() => null)
  if (response.status === 401 && !sessionStorage.getItem('reloaded')) {
    // The app was restarted with a new launch token: reload once to pick it up.
    sessionStorage.setItem('reloaded', '1')
    window.location.reload()
  }
  if (response.ok) sessionStorage.removeItem('reloaded')
  if (!response.ok) {
    const detail = data?.detail
    const message = typeof detail === 'string' ? detail : Array.isArray(detail)
      ? detail.map((item: { loc?: unknown[]; msg?: string }) => `${item.loc?.slice(1).join('.') ?? 'Field'}: ${item.msg ?? 'invalid'}`).join('; ')
      : `Something went wrong (${response.status}). Try again.`
    throw new Error(message)
  }
  if (data === null) throw new Error('The local server returned an unreadable answer. Refresh and try again.')
  return data as T
}

export const post = <T>(path: string, body: unknown = {}) => request<T>(path, { method: 'POST', body: JSON.stringify(body) })
export const put = <T>(path: string, body: unknown) => request<T>(path, { method: 'PUT', body: JSON.stringify(body) })
export const patch = <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body: JSON.stringify(body) })
export const del = <T>(path: string) => request<T>(path, { method: 'DELETE' })

/** Download a file from the API (credits, collection zips) without putting the token in a URL. */
export async function download(path: string, fallbackName: string) {
  if (readOnly) throw new Error('Downloads are not available in the online demo.')
  const response = await fetch(`/api/${path}`, { headers: { 'X-Atlas-Token': token() } })
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail ?? 'Download failed.')
  const name = /filename="([^"]+)"/.exec(response.headers.get('content-disposition') ?? '')?.[1] ?? fallbackName
  const url = URL.createObjectURL(await response.blob())
  const link = Object.assign(document.createElement('a'), { href: url, download: name })
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}

export function media(path: string | null | undefined): string | undefined {
  if (!path) return undefined
  return readOnly ? `${import.meta.env.BASE_URL}${path.replace(/^\/media\//, 'media/')}` : path
}
