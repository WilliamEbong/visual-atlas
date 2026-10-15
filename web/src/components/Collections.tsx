import { useState } from 'react'
import { del, download, media, patch, post, readOnly } from '../lib/client'
import { useData } from '../lib/hooks'
import { go, href } from '../lib/router'
import type { Collection, LibraryItem } from '../lib/types'

export default function Collections({ id }: { id?: number }) {
  const { data, error, reload } = useData<Collection[]>('collections')
  const [name, setName] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  if (id) return <CollectionPage id={id} collection={data?.find((c) => c.id === id)} onChange={reload} />
  async function create(event: React.FormEvent) {
    event.preventDefault()
    try { const made = await post<{ id: number }>('collections', { name }); setName(''); reload(); go(`collections/${made.id}`) }
    catch (reason) { setMessage((reason as Error).message) }
  }
  return (
    <div className="stack">
      <h1>My collections</h1>
      <p className="lede">Boards for projects and themes. Export one as a zip with the original files, the credits and the annotations.</p>
      {!readOnly && <form className="row" onSubmit={create}>
        <label className="field grow">New collection<input required maxLength={80} value={name} onChange={(e) => setName(e.target.value)} placeholder="Solitude poster" /></label>
        <button type="submit" style={{ alignSelf: 'end' }}>Create</button></form>}
      {(message || error) && <p className="notice error" role="alert">{message || error}</p>}
      {data?.length === 0 && <p className="muted">No collections yet. Open any image and choose “Save to collection”.</p>}
      <div className="plates">
        {data?.map((c) => (
          <a key={c.id} className="plate" href={href(`collections/${c.id}`)}>
            <div className="frame" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, padding: 2 }}>
              {c.covers.length ? c.covers.map((cover) => <img key={cover} src={media(cover)} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />)
                : <span className="mono">Empty</span>}
            </div>
            <span className="title">{c.name}</span><span className="mono">{c.size} image{c.size === 1 ? '' : 's'}</span>
            {c.description && <span className="maker">{c.description}</span>}
          </a>))}
      </div>
    </div>
  )
}

function CollectionPage({ id, collection, onChange }: { id: number; collection?: Collection; onChange: () => void }) {
  const { data, reload } = useData<{ items: LibraryItem[]; total: number }>(`library?collection=${id}&sort=collection&limit=200`)
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(collection?.name ?? '')
  const [description, setDescription] = useState(collection?.description ?? '')
  const [message, setMessage] = useState<string | null>(null)
  const items = data?.items ?? []
  async function run(work: () => Promise<unknown>, done?: string) {
    try { await work(); if (done) setMessage(done); reload(); onChange() } catch (reason) { setMessage((reason as Error).message) }
  }
  function move(index: number, by: number) {
    const ids = items.map((item) => item.id)
    const [moved] = ids.splice(index, 1)
    ids.splice(index + by, 0, moved)
    run(() => post(`collections/${id}/order`, { image_ids: ids }))
  }
  return (
    <div className="stack">
      <p><a href="#/collections">← All collections</a></p>
      <div className="page-head"><h1>{collection?.name ?? 'Collection'}</h1>
        <div className="row">
          {!readOnly && <button type="button" onClick={() => run(() => download(`export/collection/${id}`, 'collection.zip'), 'Export downloaded.')}>Export zip</button>}
          {!readOnly && <button type="button" onClick={() => run(() => download(`export/credits?collection=${id}`, 'credits.md'))}>Credits</button>}
          <a className="button" href={href('', { collection: id, sort: 'collection' })}>Filter in library</a>
          {!readOnly && <button type="button" onClick={() => setEditing(!editing)}>Rename</button>}
          {!readOnly && <button type="button" className="quiet" onClick={() => run(() => del(`collections/${id}`)).then(() => go('collections'))}>Delete collection</button>}
        </div></div>
      {collection?.description && !editing && <p className="lede">{collection.description}</p>}
      {editing && <form className="stack notice" onSubmit={(e) => { e.preventDefault(); run(() => patch(`collections/${id}`, { name, description }), 'Saved.').then(() => setEditing(false)) }}>
        <label className="field">Name<input required value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label className="field">Description<textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} /></label>
        <div className="row"><button type="submit" className="primary">Save</button></div></form>}
      {message && <p className="notice" role="status">{message}</p>}
      {items.length === 0 && <p className="muted">Empty. Open any image and choose “Save to collection”.</p>}
      <div className="plates">
        {items.map((item, index) => (
          <div key={item.id} className="stack" style={{ gap: 6 }}>
            <a className="plate" href={href(`image/${item.id}`)}>
              <div className="frame"><img src={media(item.thumb)} alt={item.title} loading="lazy" /></div>
              <span className="title">{item.title}</span><span className="mono">{item.license_label}</span>
            </a>
            {!readOnly && <div className="row">
              <button type="button" aria-label={`Move ${item.title} earlier`} disabled={index === 0} onClick={() => move(index, -1)}>←</button>
              <button type="button" aria-label={`Move ${item.title} later`} disabled={index === items.length - 1} onClick={() => move(index, 1)}>→</button>
              <button type="button" className="quiet" onClick={() => run(() => post(`collections/${id}/items`, { image_id: item.id, add: false }), 'Removed from this collection (still in your library).')}>Remove</button>
            </div>}
          </div>))}
      </div>
    </div>
  )
}
