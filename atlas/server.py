"""Local API + bundled web app. Loopback only, per-launch token, Host/Origin checks (pattern from Qualia)."""

import json
import re
import secrets
import sqlite3
import threading
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from atlas import __version__, catalog, images, jobs, transfer
from atlas.home import REPO, home_dir
from atlas.store import Store

SORTS = {'newest': 'i.created_at DESC, i.id DESC', 'oldest': 'i.created_at, i.id', 'title': 'i.title COLLATE NOCASE',
         'maker': 'i.creator COLLATE NOCASE', 'colorful': 'm.colorfulness DESC', 'bright': 'm.mean_luma DESC',
         'dark': 'm.mean_luma', 'techniques': 'technique_count DESC, i.id DESC'}


class JobRequest(BaseModel):
    kind: str
    spec: dict = Field(default_factory=dict)


class AnnotationInput(BaseModel):
    technique_id: str
    state: str
    evidence: list[str] | None = None
    effect: str | None = None
    note: str = ''


class CollectionInput(BaseModel):
    name: str | None = None
    description: str | None = None


class MembershipInput(BaseModel):
    image_id: int
    add: bool = True
    note: str = ''


class BriefInput(BaseModel):
    title: str
    text: str


class StateInput(BaseModel):
    state: str


def fts_query(text: str) -> str:
    words = re.findall(r'\w+', text.lower())[:8]
    return ' '.join(f'"{word}"*' for word in words)


def create_app(home: Path | None = None, token: str | None = None, dist: Path | None = None,
               start_worker: bool = False) -> FastAPI:
    home = home_dir(home)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.token = token or secrets.token_urlsafe(32)
    app.state.activity = 0
    web = dist or REPO / 'web/dist'
    media_root = (home / 'media').resolve()
    with jobs.open_store(home) as store:  # migrate + sync knowledge files once at start
        images.sweep_orphans(home / 'media', transfer.referenced_media(store))
    worker = jobs.Worker(home)
    app.state.worker = worker
    app.state.stop = threading.Event()
    app.state.thread = None

    def start():
        if start_worker:
            app.state.stop = threading.Event()
            app.state.thread = threading.Thread(target=worker.loop, args=(app.state.stop,), daemon=True,
                                                name='atlas-worker')
            app.state.thread.start()

    start()

    def db() -> Store:
        return Store(jobs.db_path(home))

    @app.middleware('http')
    async def secure(request: Request, call_next):
        host = request.headers.get('host', '')
        try:
            parsed = urlsplit('http://' + host)
            valid_host = parsed.hostname in ('localhost', '127.0.0.1') and not parsed.username
        except ValueError:
            valid_host = False
        origin = request.headers.get('origin')
        path = request.url.path
        if not valid_host:
            response = JSONResponse({'detail': 'Host forbidden'}, status_code=403)
        elif origin and origin != f'http://{host}':
            response = JSONResponse({'detail': 'Origin forbidden'}, status_code=403)
        elif path.startswith('/api/') and not secrets.compare_digest(
                request.headers.get('x-atlas-token', ''), app.state.token):
            response = JSONResponse({'detail': 'Invalid launch token. Reopen Visual Atlas.'}, status_code=401)
        else:
            if path.startswith('/api/'):
                app.state.activity += 1
            response = await call_next(request)
        response.headers.update({
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                                       "img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'; "
                                       "base-uri 'none'; form-action 'self'",
            'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'no-referrer',
            'Cross-Origin-Resource-Policy': 'same-origin'})
        if not path.startswith('/media/') and 'cache-control' not in response.headers:
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=400)

    @app.exception_handler(sqlite3.IntegrityError)
    async def conflict(request, exc):
        return JSONResponse({'detail': 'That change conflicts with existing records.'}, status_code=400)

    def media_url(relative: str | None) -> str | None:
        return f'/media/{relative}' if relative else None

    # ---- library ------------------------------------------------------------------------------
    @app.get('/api/health')
    def health():
        return {'version': __version__, 'home': str(home)}

    @app.get('/api/library')
    def library(q: str = '', technique: str = '', goal: str = '', provider: str = '', license: str = '',
                orientation: str = '', color: str = '', state: str = '', favorite: bool = False,
                collection: int = 0, sort: str = 'newest', limit: int = 60, offset: int = 0):
        where, params = ["i.removed_at IS NULL", "i.status!='pending'"], []
        if q.strip():
            where.append('i.id IN (SELECT rowid FROM images_fts WHERE images_fts MATCH ?)')
            params.append(fts_query(q) or '""')
        if technique:
            where.append("i.id IN (SELECT image_id FROM annotations WHERE technique_id=? AND state!='rejected')")
            params.append(technique)
        if goal:
            where.append("i.id IN (SELECT a.image_id FROM annotations a JOIN technique_links l ON l.technique_id="
                         "a.technique_id AND l.kind='goal' WHERE l.target_id=? AND a.state!='rejected')")
            params.append(goal)
        if state:
            where.append('i.id IN (SELECT image_id FROM annotations WHERE state=?)')
            params.append(state)
        for column, value in (('i.provider', provider), ('m.orientation', orientation), ('m.color_family', color)):
            if value:
                where.append(f'{column}=?')
                params.append(value)
        if license:
            where.append('(SELECT license_code FROM rights_records r WHERE r.image_id=i.id ORDER BY r.id DESC LIMIT 1)=?')
            params.append(license)
        if favorite:
            where.append('i.favorite=1')
        if collection:
            where.append('i.id IN (SELECT image_id FROM collection_items WHERE collection_id=?)')
            params.append(collection)
        order = SORTS.get(sort, SORTS['newest'])
        if collection and sort == 'collection':
            order = '(SELECT position FROM collection_items c WHERE c.image_id=i.id AND c.collection_id=%d)' % collection
        limit = max(1, min(limit, 5000))
        with db() as store:
            total = store.one(f"SELECT COUNT(*) AS n FROM images i LEFT JOIN image_metrics m ON m.image_id=i.id "
                              f"WHERE {' AND '.join(where)}", params)['n']
            rows = store.rows(
                "SELECT i.id, i.title, i.creator, i.date_text, i.provider, i.thumb_path, i.width, i.height, i.status, "
                "i.favorite, i.created_at, m.orientation, m.color_family, m.palette_json, "
                "(SELECT label FROM rights_records r WHERE r.image_id=i.id ORDER BY r.id DESC LIMIT 1) AS license_label, "
                "(SELECT COUNT(*) FROM annotations a WHERE a.image_id=i.id AND a.state!='rejected') AS technique_count "
                "FROM images i LEFT JOIN image_metrics m ON m.image_id=i.id "
                f"WHERE {' AND '.join(where)} ORDER BY {order} LIMIT ? OFFSET ?", [*params, limit, max(0, offset)])
            ids = [row['id'] for row in rows]
            names = {}
            if ids:
                for row in store.rows(
                        "SELECT a.image_id, a.technique_id, a.state, a.role, t.name FROM annotations a JOIN techniques t "
                        f"ON t.id=a.technique_id WHERE a.state!='rejected' AND a.image_id IN ({','.join('?' * len(ids))}) "
                        "ORDER BY a.role='primary' DESC, a.confidence DESC", ids):
                    names.setdefault(row['image_id'], []).append(
                        {'id': row['technique_id'], 'name': row['name'], 'state': row['state']})
            waiting = [r['id'] for r in store.rows("SELECT id FROM images WHERE removed_at IS NULL AND status='pending' "
                                                   "AND id NOT IN (SELECT image_id FROM job_items j JOIN jobs b ON "
                                                   "b.id=j.job_id WHERE b.state IN ('queued','running','cancelling','paused') "
                                                   "AND j.image_id IS NOT NULL)")]
        items = [{**row, 'thumb': media_url(row.pop('thumb_path')),
                  'palette': [p['hex'] for p in json.loads(row.pop('palette_json') or '[]')][:4],
                  'techniques': names.get(row['id'], [])} for row in rows]
        return {'items': items, 'total': total, 'waiting': waiting}

    @app.get('/api/images/{image_id}')
    def image(image_id: int):
        with db() as store, store.reading():
            row = store.one('SELECT * FROM images WHERE id=?', (image_id,))
            if row is None or row['removed_at']:
                raise HTTPException(404, 'That image is not in the library.')
            rights = store.one('SELECT * FROM rights_records WHERE image_id=? ORDER BY id DESC LIMIT 1', (image_id,))
            metrics = store.one('SELECT * FROM image_metrics WHERE image_id=?', (image_id,))
            analysis = store.one('SELECT id, backend, model, model_version, created_at, result_json FROM analyses '
                                 'WHERE id=?', (row['analysis_id'],)) if row['analysis_id'] else None
            annotations = store.rows(
                "SELECT a.*, t.name, t.data_json, p.backend AS proposed_backend, COALESCE(p.model_version, p.model) "
                "AS proposed_model FROM annotations a JOIN techniques t ON t.id=a.technique_id LEFT JOIN analyses p "
                "ON p.id=a.analysis_id WHERE a.image_id=? ORDER BY a.state='rejected', a.role='primary' DESC, "
                "a.confidence DESC", (image_id,))
            history = store.rows('SELECT technique_id, state, changed_by, note, effect, created_at FROM annotation_history '
                                 'WHERE image_id=? ORDER BY id DESC LIMIT 60', (image_id,))
            related = store.rows(
                "SELECT i.id, i.title, i.creator, i.thumb_path, COUNT(*) AS shared, group_concat(b.technique_id) AS via "
                "FROM annotations a JOIN annotations b ON b.technique_id=a.technique_id AND b.image_id!=a.image_id "
                "JOIN images i ON i.id=b.image_id WHERE a.image_id=? AND a.state!='rejected' AND b.state!='rejected' "
                "AND i.removed_at IS NULL GROUP BY i.id ORDER BY shared DESC, i.id DESC LIMIT 12", (image_id,))
            collections = store.rows('SELECT c.id, c.name FROM collections c JOIN collection_items ci ON '
                                     'ci.collection_id=c.id WHERE ci.image_id=?', (image_id,))
            goals = store.rows("SELECT DISTINCT g.id, g.name FROM annotations a JOIN technique_links l ON "
                               "l.technique_id=a.technique_id AND l.kind='goal' JOIN goals g ON g.id=l.target_id "
                               "WHERE a.image_id=? AND a.state!='rejected'", (image_id,))
        result = json.loads(analysis['result_json']) if analysis else None
        for annotation in annotations:
            data = json.loads(annotation.pop('data_json'))
            annotation['definition'] = data['definition']
            annotation['evidence'] = json.loads(annotation.pop('evidence_json'))
        return {
            'image': {**{k: row[k] for k in ('id', 'title', 'creator', 'date_text', 'medium', 'description', 'provider',
                                             'provider_item_id', 'source_url', 'width', 'height', 'status', 'favorite',
                                             'created_at', 'file_sha256')},
                      'original': media_url(row['original_path']), 'display': media_url(row['analysis_path']),
                      'thumb': media_url(row['thumb_path'])},
            'rights': rights and {**rights, 'evidence': json.loads(rights.pop('evidence_json')),
                                  'provenance': json.loads(rights.pop('provenance_json'))},
            'metrics': metrics and {**metrics, 'palette': json.loads(metrics.pop('palette_json'))},
            'analysis': result and {'observations': result['observations'], 'summary': result['summary'],
                                    'ambiguities': result['ambiguities'], 'subjects': result['subjects'],
                                    'creator_intent': result['creator_intent'], 'image_usable': result['image_usable'],
                                    'backend': analysis['backend'], 'model': analysis['model_version'] or analysis['model'],
                                    'created_at': analysis['created_at']},
            'annotations': annotations, 'history': history, 'goals': goals, 'collections': collections,
            'related': [{**r, 'thumb': media_url(r.pop('thumb_path')), 'via': (r['via'] or '').split(',')}
                        for r in related]}

    @app.post('/api/images/{image_id}/favorite')
    def favorite(image_id: int, body: dict):
        with db() as store:
            store.set_favorite(image_id, bool(body.get('favorite')))
        return {'ok': True}

    @app.post('/api/images/{image_id}/annotations')
    def annotate(image_id: int, body: AnnotationInput):
        with db() as store:
            store.human_annotation(image_id, body.technique_id, state=body.state, evidence=body.evidence,
                                   effect=body.effect, note=body.note)
        return image(image_id)

    @app.delete('/api/images/{image_id}')
    def remove(image_id: int):
        with db() as store:
            removed = store.remove_image(image_id, 'removed by you')
        images.delete_files(home / 'media', removed)
        return {'ok': True}

    # ---- knowledge ----------------------------------------------------------------------------
    @app.get('/api/taxonomy')
    def taxonomy():
        with db() as store, store.reading():
            counts = {r['id']: r['examples'] for r in catalog.coverage(store)}
            techniques = []
            for row in store.rows('SELECT id, data_json FROM techniques ORDER BY name'):
                data = json.loads(row['data_json'])
                techniques.append({k: data[k] for k in ('id', 'name', 'aliases', 'definition', 'goals', 'operations',
                                                        'domains')} | {'examples': counts.get(row['id'], 0)})
            return {'goals': store.rows('SELECT * FROM goals ORDER BY name'),
                    'operations': store.rows('SELECT * FROM operations ORDER BY name'),
                    'domains': [{**d, 'variables': json.loads(d.pop('variables_json'))}
                                for d in store.rows('SELECT * FROM domains ORDER BY name')],
                    'techniques': techniques}

    @app.get('/api/techniques/{technique_id}')
    def technique(technique_id: str):
        with db() as store, store.reading():
            row = store.one('SELECT data_json FROM techniques WHERE id=?', (technique_id,))
            if row is None:
                raise HTTPException(404, 'Unknown technique.')
            data = json.loads(row['data_json'])
            names = {r['id']: r['name'] for r in store.rows('SELECT id, name FROM techniques')}
            examples = store.rows(
                "SELECT i.id, i.title, i.creator, i.date_text, i.thumb_path, a.state, a.effect, a.role FROM annotations a "
                "JOIN images i ON i.id=a.image_id WHERE a.technique_id=? AND a.state!='rejected' AND i.removed_at IS NULL "
                "ORDER BY a.state='human_reviewed' DESC, a.state='model_reviewed' DESC, a.confidence DESC LIMIT 24",
                (technique_id,))
            goals = store.rows("SELECT g.* FROM technique_links l JOIN goals g ON g.id=l.target_id WHERE "
                               "l.technique_id=? AND l.kind='goal'", (technique_id,))
            operations = store.rows("SELECT o.* FROM technique_links l JOIN operations o ON o.id=l.target_id WHERE "
                                    "l.technique_id=? AND l.kind='operation'", (technique_id,))
            domains = store.rows("SELECT d.id, d.name, d.description FROM technique_links l JOIN domains d ON "
                                 "d.id=l.target_id WHERE l.technique_id=? AND l.kind='domain'", (technique_id,))
            used_by = store.rows("SELECT technique_id AS id, kind, note FROM technique_links WHERE target_id=? AND "
                                 "kind IN ('related','confused_with') AND technique_id!=?", (technique_id, technique_id))
        related = [{'id': r['technique'], 'name': names.get(r['technique'], r['technique']), 'relation': r['relation']}
                   for r in data['related']]
        seen = {r['id'] for r in related}
        related += [{'id': r['id'], 'name': names.get(r['id'], r['id']), 'relation': 'related'}
                    for r in used_by if r['kind'] == 'related' and r['id'] not in seen]
        return {**data, 'goals': goals, 'operations': operations, 'domains': domains, 'related': related,
                'confusions': [{**c, 'name': names.get(c['technique'], c['technique'])} for c in data['confusions']],
                'examples': [{**e, 'thumb': media_url(e.pop('thumb_path'))} for e in examples]}

    @app.get('/api/goals/{goal_id}')
    def goal(goal_id: str):
        with db() as store:
            row = store.one('SELECT * FROM goals WHERE id=?', (goal_id,))
            if row is None:
                raise HTTPException(404, 'Unknown goal.')
            techniques = store.rows(
                "SELECT t.id, t.name, json_extract(t.data_json,'$.definition') AS definition, "
                "(SELECT COUNT(*) FROM annotations a JOIN images i ON i.id=a.image_id WHERE a.technique_id=t.id "
                "AND a.state!='rejected' AND i.removed_at IS NULL) AS examples, "
                "(SELECT i.thumb_path FROM annotations a JOIN images i ON i.id=a.image_id WHERE a.technique_id=t.id "
                "AND a.state!='rejected' AND i.removed_at IS NULL ORDER BY a.confidence DESC LIMIT 1) AS thumb_path "
                "FROM technique_links l JOIN techniques t ON t.id=l.technique_id WHERE l.kind='goal' AND l.target_id=? "
                "ORDER BY t.name", (goal_id,))
        return {**row, 'techniques': [{**t, 'thumb': media_url(t.pop('thumb_path'))} for t in techniques]}

    @app.get('/api/graph')
    def graph(focus: str):
        kind, _, key = focus.partition(':')
        nodes, edges = {}, set()

        def node(node_id, label, node_kind, thumb=None, ring=1):
            nodes.setdefault(node_id, {'id': node_id, 'label': label, 'kind': node_kind, 'thumb': thumb, 'ring': ring})

        with db() as store, store.reading():
            names = {r['id']: r['name'] for r in store.rows('SELECT id, name FROM techniques')}
            goals = {r['id']: r['name'] for r in store.rows('SELECT id, name FROM goals')}

            def examples(technique_id, limit, ring):
                for e in store.rows("SELECT i.id, i.title, i.thumb_path FROM annotations a JOIN images i ON i.id=a.image_id "
                                    "WHERE a.technique_id=? AND a.state!='rejected' AND i.removed_at IS NULL "
                                    "ORDER BY a.confidence DESC LIMIT ?", (technique_id, limit)):
                    node(f"image:{e['id']}", e['title'], 'image', media_url(e['thumb_path']), ring)
                    edges.add((f'technique:{technique_id}', f"image:{e['id']}", 'example'))

            if kind == 'technique' and key in names:
                node(focus, names[key], 'technique', ring=0)
                for link in store.rows('SELECT kind, target_id FROM technique_links WHERE technique_id=?', (key,)):
                    if link['kind'] == 'goal':
                        node(f"goal:{link['target_id']}", goals[link['target_id']], 'goal')
                        edges.add((f"goal:{link['target_id']}", focus, 'serves'))
                    elif link['kind'] == 'related' and link['target_id'] in names:
                        node(f"technique:{link['target_id']}", names[link['target_id']], 'technique')
                        edges.add((focus, f"technique:{link['target_id']}", 'related'))
                examples(key, 8, 2)
            elif kind == 'goal' and key in goals:
                node(focus, goals[key], 'goal', ring=0)
                for link in store.rows("SELECT technique_id FROM technique_links WHERE kind='goal' AND target_id=?", (key,)):
                    node(f"technique:{link['technique_id']}", names[link['technique_id']], 'technique')
                    edges.add((focus, f"technique:{link['technique_id']}", 'serves'))
                    examples(link['technique_id'], 2, 2)
            elif kind == 'image' and key.isdigit():
                row = store.one('SELECT id, title, thumb_path FROM images WHERE id=? AND removed_at IS NULL', (int(key),))
                if row is None:
                    raise HTTPException(404, 'That image is not in the library.')
                node(focus, row['title'], 'image', media_url(row['thumb_path']), ring=0)
                for a in store.rows("SELECT technique_id FROM annotations WHERE image_id=? AND state!='rejected'",
                                    (row['id'],)):
                    tid = a['technique_id']
                    node(f'technique:{tid}', names[tid], 'technique')
                    edges.add((f'technique:{tid}', focus, 'example'))
                    for link in store.rows("SELECT target_id FROM technique_links WHERE technique_id=? AND kind='goal'",
                                           (tid,)):
                        node(f"goal:{link['target_id']}", goals[link['target_id']], 'goal', ring=2)
                        edges.add((f"goal:{link['target_id']}", f'technique:{tid}', 'serves'))
                    examples(tid, 3, 2)
            else:
                raise HTTPException(404, 'Unknown focus.')
        return {'focus': focus, 'nodes': list(nodes.values()),
                'edges': [{'source': s, 'target': t, 'kind': k} for s, t, k in sorted(edges)]}

    @app.get('/api/sources')
    def sources():
        with db() as store:
            return [json.loads(r['data_json']) for r in store.rows('SELECT data_json FROM source_policies '
                                                                   "ORDER BY status='enabled' DESC, provider")]

    # ---- jobs ---------------------------------------------------------------------------------
    def job_view(store, job):
        counts = {r['state']: r['n'] for r in store.rows(
            "SELECT state, COUNT(*) AS n FROM job_items WHERE job_id=? AND kind='candidate' GROUP BY state", (job['id'],))}
        searches = store.one("SELECT COUNT(*) AS n FROM job_items WHERE job_id=? AND kind='query' AND state!='pending'",
                             (job['id'],))['n']
        added = store.rows("SELECT i.id, i.title, i.thumb_path FROM job_items j JOIN images i ON i.id=j.image_id WHERE "
                           "j.job_id=? AND j.state='added' AND i.removed_at IS NULL ORDER BY j.id", (job['id'],))
        return {**{k: job[k] for k in ('id', 'kind', 'state', 'stage', 'message', 'error_code', 'backend', 'model',
                                       'created_at', 'started_at', 'finished_at')},
                'spec': json.loads(job['spec_json']), 'counts': counts, 'searches': searches,
                'added': [{**a, 'thumb': media_url(a.pop('thumb_path'))} for a in added]}

    @app.get('/api/jobs')
    def list_jobs(limit: int = 30):
        with db() as store, store.reading():
            return [job_view(store, j) for j in store.rows('SELECT * FROM jobs ORDER BY created_at DESC, rowid DESC '
                                                            'LIMIT ?', (max(1, min(limit, 100)),))]

    @app.post('/api/jobs', status_code=201)
    def start_job(body: JobRequest):
        with db() as store:
            job_id = jobs.create_job(store, body.kind, body.spec)
            return job_view(store, store.one('SELECT * FROM jobs WHERE id=?', (job_id,)))

    @app.get('/api/jobs/{job_id}')
    def get_job(job_id: str):
        with db() as store, store.reading():
            job = store.one('SELECT * FROM jobs WHERE id=?', (job_id,))
            if job is None:
                raise HTTPException(404, 'Job not found.')
            items = store.rows("SELECT id, kind, provider, state, reason, image_id, "
                               "json_extract(payload_json,'$.title') AS title, json_extract(payload_json,'$.query') AS query "
                               "FROM job_items WHERE job_id=? ORDER BY id", (job_id,))
            return {**job_view(store, job), 'items': items}

    @app.post('/api/jobs/{job_id}/{action}')
    def control_job(job_id: str, action: str):
        with db() as store:
            job = store.request_job_state(job_id, action)
            return job_view(store, job)

    # ---- collections, briefs, comparisons ---------------------------------------------------------
    @app.get('/api/collections')
    def collections():
        with db() as store:
            rows = store.rows("SELECT c.*, COUNT(ci.image_id) AS size FROM collections c LEFT JOIN collection_items ci ON "
                              "ci.collection_id=c.id GROUP BY c.id ORDER BY c.name COLLATE NOCASE")
            for row in rows:
                row['covers'] = [media_url(r['thumb_path']) for r in store.rows(
                    "SELECT i.thumb_path FROM collection_items ci JOIN images i ON i.id=ci.image_id WHERE "
                    "ci.collection_id=? AND i.removed_at IS NULL ORDER BY ci.position LIMIT 4", (row['id'],))]
            return rows

    @app.post('/api/collections', status_code=201)
    def create_collection(body: CollectionInput):
        with db() as store:
            return {'id': store.create_collection(body.name or '', body.description or '')}

    @app.patch('/api/collections/{collection_id}')
    def edit_collection(collection_id: int, body: CollectionInput):
        with db() as store:
            store.update_collection(collection_id, body.name, body.description)
        return {'ok': True}

    @app.delete('/api/collections/{collection_id}')
    def delete_collection(collection_id: int):
        with db() as store:
            store.delete_collection(collection_id)
        return {'ok': True}

    @app.post('/api/collections/{collection_id}/items')
    def membership(collection_id: int, body: MembershipInput):
        with db() as store:
            if not store.one('SELECT id FROM collections WHERE id=?', (collection_id,)):
                raise HTTPException(404, 'Collection not found.')
            store.collect(collection_id, body.image_id, body.add, body.note)
        return {'ok': True}

    @app.post('/api/collections/{collection_id}/order')
    def reorder(collection_id: int, body: dict):
        with db() as store:
            store.reorder_collection(collection_id, [int(i) for i in body.get('image_ids') or []])
        return {'ok': True}

    @app.get('/api/briefs')
    def briefs():
        with db() as store:
            return store.rows('SELECT * FROM briefs ORDER BY updated_at DESC')

    @app.post('/api/briefs', status_code=201)
    def create_brief(body: BriefInput):
        with db() as store:
            return {'id': store.save_brief(body.title, body.text)}

    @app.get('/api/briefs/{brief_id}')
    def get_brief(brief_id: int):
        with db() as store, store.reading():
            brief = store.one('SELECT * FROM briefs WHERE id=?', (brief_id,))
            if brief is None:
                raise HTTPException(404, 'Brief not found.')
            directions = store.rows('SELECT d.*, a.backend, a.model, a.model_version FROM directions d LEFT JOIN '
                                    'analyses a ON a.id=d.analysis_id WHERE brief_id=? AND state!=? ORDER BY '
                                    "state='kept' DESC, position", (brief_id, 'dismissed'))
            thumbs = {r['id']: r for r in store.rows('SELECT id, title, thumb_path FROM images WHERE removed_at IS NULL')}
            names = {r['id']: r['name'] for r in store.rows('SELECT id, name FROM techniques')}
        out = []
        for d in directions:
            data = json.loads(d.pop('result_json'))
            data['images'] = [{'id': i, 'title': thumbs[i]['title'], 'thumb': media_url(thumbs[i]['thumb_path'])}
                              for i in data.pop('image_ids') if i in thumbs]
            data['techniques'] = [{'id': t, 'name': names.get(t, t)} for t in data.pop('technique_ids')]
            out.append({**d, **data})
        return {**brief, 'directions': out}

    @app.put('/api/briefs/{brief_id}')
    def edit_brief(brief_id: int, body: BriefInput):
        with db() as store:
            store.save_brief(body.title, body.text, brief_id)
        return {'ok': True}

    @app.delete('/api/briefs/{brief_id}')
    def delete_brief(brief_id: int):
        with db() as store:
            store.delete_brief(brief_id)
        return {'ok': True}

    @app.post('/api/directions/{direction_id}')
    def direction_state(direction_id: int, body: StateInput):
        with db() as store:
            store.set_direction_state(direction_id, body.state)
        return {'ok': True}

    @app.get('/api/compare')
    def compare(ids: str):
        image_ids = sorted({int(i) for i in ids.split(',') if i.strip().isdigit()})[:4]
        details = [image(i) for i in image_ids]
        with db() as store:
            saved = store.one('SELECT a.result_json, a.backend, a.model, a.model_version, c.created_at FROM comparisons c '
                              'JOIN analyses a ON a.id=c.analysis_id WHERE c.image_ids=? ORDER BY c.id DESC LIMIT 1',
                              (','.join(map(str, image_ids)),))
        return {'images': details, 'comparison': saved and {**json.loads(saved.pop('result_json')), **saved}}

    # ---- AI status, settings, coverage --------------------------------------------------------------
    @app.get('/api/ai/status')
    def ai_status(refresh: bool = False):
        out = {}
        for name in ('codex', 'claude'):
            module = jobs.BACKENDS[name]
            try:
                out[name] = {'ready': True, 'version': module.check(force=refresh), 'message': 'Ready'}
            except jobs.BackendError as error:
                out[name] = {'ready': False, 'version': error.cli_version, 'code': error.code,
                             'message': jobs.backend_message(error.code, name)}
        return out

    @app.get('/api/settings')
    def settings():
        with db() as store:
            values = {r['key']: r['value'] for r in store.rows('SELECT * FROM settings')}
        return {'backend': values.get('backend', 'codex'), 'verify_with': values.get('verify_with', 'claude'),
                'daily_ai_cap': int(values.get('daily_ai_cap', jobs.DAILY_AI_CAP)),
                'welcomed': values.get('welcomed') == '1'}

    @app.put('/api/settings')
    def save_settings(body: dict):
        with db() as store:
            if body.get('backend') in ('codex', 'claude', 'fake'):
                store.set_setting('backend', body['backend'])
            if body.get('verify_with') in ('codex', 'claude', 'none'):
                store.set_setting('verify_with', body['verify_with'])
            if 'daily_ai_cap' in body:
                store.set_setting('daily_ai_cap', str(max(0, min(int(body['daily_ai_cap']), 1000))))
            if 'welcomed' in body:
                store.set_setting('welcomed', '1' if body['welcomed'] else '0')
        return settings()

    @app.get('/api/coverage')
    def coverage():
        with db() as store:
            return catalog.coverage(store)

    # ---- exports and backups ------------------------------------------------------------------------
    @app.get('/api/export/credits')
    def credits(format: str = 'md', collection: int = 0, ids: str = ''):
        image_ids = [int(i) for i in ids.split(',') if i.strip().isdigit()] or None
        with db() as store:
            text = transfer.credits(store, image_ids=image_ids, collection_id=collection or None, fmt=format)
        kind = 'text/csv' if format == 'csv' else 'text/markdown'
        return PlainTextResponse(text, media_type=f'{kind}; charset=utf-8', headers={
            'Content-Disposition': f'attachment; filename="visual-atlas-credits.{"csv" if format == "csv" else "md"}"'})

    @app.get('/api/export/collection/{collection_id}')
    def export_collection(collection_id: int):
        with db() as store:
            path = transfer.export_collection(store, home, collection_id)
        return FileResponse(path, media_type='application/zip', filename=path.name)

    @app.get('/api/backups')
    def backups():
        return transfer.list_backups(home)

    @app.post('/api/backups', status_code=201)
    def make_backup():
        return transfer.backup(home)

    @app.post('/api/backups/{name}/restore')
    def restore(name: str):
        with db() as store:
            if store.one("SELECT id FROM jobs WHERE state IN ('queued','running','cancelling')"):
                raise ValueError('A job is still running. Pause or cancel it, then restore.')
        app.state.stop.set()  # stop the background worker while files are swapped
        if app.state.thread is not None:
            app.state.thread.join(timeout=30)
            if app.state.thread.is_alive():
                raise ValueError('The background worker is still busy. Try again in a minute.')
        try:
            return transfer.restore(home, name)
        finally:
            start()

    @app.get('/media/{path:path}', include_in_schema=False)
    def media(path: str):
        resolved = (media_root / path).resolve()
        if (not resolved.is_relative_to(media_root) or not resolved.is_file()
                or resolved.parts[len(media_root.parts)] not in ('originals', 'analysis', 'thumbs')):
            raise HTTPException(404)
        return FileResponse(resolved, headers={'Cache-Control': 'private, max-age=31536000, immutable'})

    @app.get('/{asset:path}', include_in_schema=False)
    def spa(asset: str):
        if asset.startswith('api/'):
            raise HTTPException(404)
        resolved = (web / asset).resolve()
        if asset and resolved.is_relative_to(web.resolve()) and resolved.is_file() and resolved.suffix != '.html':
            return FileResponse(resolved)
        index = web / 'index.html'
        html = index.read_text(encoding='utf-8') if index.exists() else (
            '<!doctype html><html><head><title>Visual Atlas</title></head><body><h1>Visual Atlas</h1>'
            '<p>Build the web app with: npm --prefix web run build</p></body></html>')
        return HTMLResponse(html.replace('</head>', f'<meta name="atlas-token" content="{app.state.token}"></head>'))

    return app
