import { useState } from 'react'
import { del, download, media, patch, post, readOnly } from '../lib/client'
import { useData } from '../lib/hooks'
import { aspect } from '../lib/library'
import { go, href } from '../lib/router'
import type { Collection, LibraryItem } from '../lib/types'
import { Empty, Failure, Loading, PageHead, useNotice } from './ui'

export default function Collections({ id }: { id?: number }) {
  const { data, error, busy, reload } = useData<Collection[]>('collections')
  const { fail } = useNotice()
  const [name, setName] = useState('')
  if (id) return <CollectionPage id={id} collection={data?.find((c) => c.id === id)} onChange={reload} />
  async function create(event: React.FormEvent) {
    event.preventDefault()
    try { const made = await post<{ id: number }>('collections', { name }); setName(''); reload(); go(`collections/${made.id}`) }
    catch (reason) { fail(reason) }
  }
  const images = data?.reduce((sum, c) => sum + c.size, 0) ?? 0
  return (
    <>
      <PageHead kicker={data ? `Collections · ${data.length} board${data.length === 1 ? '' : 's'} · ${images} image${images === 1 ? '' : 's'} · credits ready to export` : 'Collections'}
        title="Collections" asideClass="actions"
        aside={!readOnly && <form className="filters" onSubmit={create}>
          <label className="field">New collection<input required maxLength={80} value={name} onChange={(e) => setName(e.target.value)} placeholder="Festival flyer" /></label>
          <button type="submit" className="primary">Create</button></form>} />
      {error ? <Failure message={error} busy={busy} retry={reload} /> : !data ? <Loading plates={false} />
        : data.length === 0 ? <Empty title="No collections yet">Open any image and choose “Save to a collection”, or name a new one above.</Empty>
        : <div className="cards" style={{ marginTop: 40, gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
          {data.map((c) => (
            <article key={c.id} className="drawer-card">
              <div className="contact" aria-hidden="true">
                {c.covers.length ? c.covers.map((cover, i) => <img key={cover} src={media(cover)} alt="" style={{ height: [84, 112, 124, 96][i % 4] }} />)
                  : <span className="none">Empty</span>}
              </div>
              <div className="section-title"><h2 style={{ fontSize: 28 }}><a href={href(`collections/${c.id}`)} style={{ textDecoration: 'none' }}>{c.name}</a></h2>
                <span className="mono">{c.size} image{c.size === 1 ? '' : 's'}</span></div>
              {c.description && <p className="muted" style={{ fontSize: 14 }}>{c.description}</p>}
              {!readOnly && <div className="row">
                <button type="button" className="small" onClick={() => download(`export/collection/${c.id}`, 'collection.zip').catch(fail)}>Export with credits</button>
                <button type="button" className="small" onClick={() => download(`export/credits?collection=${c.id}`, 'credits.md').catch(fail)}>Credits</button>
              </div>}
            </article>))}
        </div>}
    </>
  )
}

function CollectionPage({ id, collection, onChange }: { id: number; collection?: Collection; onChange: () => void }) {
  const { data, error, busy, reload } = useData<{ items: LibraryItem[]; total: number }>(`library?collection=${id}&sort=collection&limit=200`)
  const { notify, fail, confirm } = useNotice()
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(collection?.name ?? '')
  const [description, setDescription] = useState(collection?.description ?? '')
  const items = data?.items ?? []
  async function run(work: () => Promise<unknown>, done?: string) {
    try { await work(); if (done) notify(done); reload(); onChange() } catch (reason) { fail(reason) }
  }
  function order(ids: number[]) { return post(`collections/${id}/order`, { image_ids: ids }) }
  function move(index: number, by: number) {
    const ids = items.map((item) => item.id)
    const [moved] = ids.splice(index, 1)
    ids.splice(index + by, 0, moved)
    run(() => order(ids))
  }
  async function remove(item: LibraryItem) {
    try {
      const { position } = await post<{ position: number | null }>(`collections/${id}/items`, { image_id: item.id, add: false })
      reload(); onChange()
      notify(`Removed “${item.title}” from this collection (it stays in your library).`, {
        undo: async () => { await post(`collections/${id}/items`, { image_id: item.id, add: true, position }); reload(); onChange() } })
    } catch (reason) { fail(reason) }
  }
  async function deleteCollection() {
    const sure = await confirm({ title: `Delete “${collection?.name ?? 'this collection'}”?`, danger: true, confirm: 'Delete',
      body: 'The board and its order are deleted. The images stay in your library. This cannot be undone.' })
    if (sure) run(() => del(`collections/${id}`), 'Collection deleted.').then(() => go('collections'))
  }
  return (
    <>
      <PageHead kicker={<><a href="#/collections">Collections</a> / {items.length} image{items.length === 1 ? '' : 's'}</>} title={collection?.name ?? 'Collection'} asideClass="actions"
        aside={<>
          {!readOnly && <button type="button" onClick={() => run(() => download(`export/collection/${id}`, 'collection.zip'), 'Export downloaded.')}>Export zip</button>}
          {!readOnly && <button type="button" onClick={() => run(() => download(`export/credits?collection=${id}`, 'credits.md'))}>Credits</button>}
          <a className="button" href={href('', { collection: id, sort: 'collection' })}>Filter in the library</a>
          {!readOnly && <button type="button" onClick={() => setEditing(!editing)}>{editing ? 'Close' : 'Rename'}</button>}</>} />
      {collection?.description && !editing && <p className="lede under">{collection.description}</p>}
      {editing && <form className="stack panel" onSubmit={(e) => { e.preventDefault(); run(() => patch(`collections/${id}`, { name, description }), 'Saved.').then(() => setEditing(false)) }}>
        <label className="field">Name<input required value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label className="field">Description<textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} /></label>
        <div className="row"><button type="submit" className="primary">Save</button></div></form>}
      {error ? <Failure message={error} busy={busy} retry={reload} /> : !data ? <Loading />
        : items.length === 0 ? <Empty title="This collection is empty">Open any image and choose “Save to a collection”.</Empty>
        : <div className="justified">
          {items.map((item, index) => (
            <article key={item.id} className="plate-item" style={{ '--a': aspect(item) } as React.CSSProperties}>
              <a className="plate" href={href(`image/${item.id}`)}>
                <span className="plate-frame"><img src={media(item.thumb)} alt={item.title} loading="lazy" decoding="async" /></span>
                <span className="fig">Fig. {index + 1}  {item.license_label}</span>
                <span className="plate-title">{item.title}</span>
              </a>
              {!readOnly && <div className="row" style={{ marginTop: 8, gap: 6 }}>
                <button type="button" className="small" aria-label={`Move ${item.title} earlier`} disabled={index === 0} onClick={() => move(index, -1)}>←</button>
                <button type="button" className="small" aria-label={`Move ${item.title} later`} disabled={index === items.length - 1} onClick={() => move(index, 1)}>→</button>
                <button type="button" className="quiet small" onClick={() => remove(item)}>Remove</button>
              </div>}
            </article>))}
        </div>}
      {!readOnly && <p style={{ marginTop: 48 }}><button type="button" className="quiet small" style={{ color: 'var(--danger)' }} onClick={deleteCollection}>Delete this collection…</button></p>}
    </>
  )
}
