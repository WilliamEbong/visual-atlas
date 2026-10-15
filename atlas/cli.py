"""Command line for people and agents (Claude Code or Codex). Every command works on the same data home."""

import json
import sys
import threading

import typer

from atlas import catalog, jobs, transfer
from atlas.home import home_dir

app = typer.Typer(help='Visual Atlas: find free-to-use images and learn the techniques that make them work.',
                  no_args_is_help=True, add_completion=False)
taxonomy_app = typer.Typer(help='Check or reload the editable taxonomy and source policies.')
app.add_typer(taxonomy_app, name='taxonomy')
for stream in (sys.stdout, sys.stderr):
    if stream is not None and hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')


def _print(value):
    typer.echo(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def _queue(kind: str, spec: dict, run: bool) -> str:
    with jobs.open_store() as store:
        settings = {r['key']: r['value'] for r in store.rows('SELECT * FROM settings')}
        spec.setdefault('backend', settings.get('backend', 'codex'))
        if kind in ('find', 'grow') and 'verify_with' not in spec:
            verifier = settings.get('verify_with', 'claude')
            spec['verify_with'] = None if verifier == 'none' else verifier
        job_id = jobs.create_job(store, kind, spec)
    typer.echo(f'Queued {kind} job {job_id}.')
    if run:
        _work(job_id)
    return job_id


def _work(job_id: str | None):
    worker = jobs.Worker()
    claimed = worker.run_once(job_id)
    if claimed is None:
        typer.echo('No job to run (or another worker holds the lease; try again in a minute).')
        return
    with jobs.open_store() as store:
        job = store.one('SELECT id, kind, state, message FROM jobs WHERE id=?', (claimed,))
    typer.echo(f"Job {job['id']} ({job['kind']}): {job['state']}. {job['message']}")


@app.command()
def find(goal: str = typer.Argument(..., help='What you want to see, in plain words.'),
         backend: str = typer.Option(None, help='codex, claude or fake (offline practice).'),
         verify_with: str = typer.Option(None, help='Second model that checks each analysis: codex, claude or none.'),
         count: int = typer.Option(8, help='How many new images to add.'),
         technique: list[str] = typer.Option(None, help='Technique id(s) to aim for.'),
         subject: str = typer.Option('', help='Subject to search for.'),
         provider: list[str] = typer.Option(None, help='Limit to provider id(s): aic met cma smithsonian commons.'),
         run: bool = typer.Option(True, help='Work the job now in this terminal.')):
    """Find images for a specific request."""
    spec = {'goal': goal, 'target_new_images': count, 'technique_ids': technique or [], 'subject': subject,
            'providers': provider or None}
    if backend:
        spec['backend'] = backend
    if verify_with:
        spec['verify_with'] = None if verify_with == 'none' else verify_with
    _queue('find', spec, run)


@app.command()
def grow(backend: str = typer.Option(None), verify_with: str = typer.Option(None), count: int = typer.Option(8),
         technique: list[str] = typer.Option(None, help='Defaults to the techniques with the fewest examples.'),
         run: bool = typer.Option(True)):
    """Grow the library where technique coverage is thinnest."""
    spec = {'target_new_images': count, 'technique_ids': technique or []}
    if backend:
        spec['backend'] = backend
    if verify_with:
        spec['verify_with'] = None if verify_with == 'none' else verify_with
    _queue('grow', spec, run)


@app.command()
def verify(image_ids: list[int], backend: str = typer.Option('claude'), run: bool = typer.Option(True)):
    """Ask a second model to check proposed annotations on images."""
    _queue('verify', {'image_ids': image_ids, 'backend': backend}, run)


@app.command()
def analyze(image_ids: list[int], backend: str = typer.Option(None), run: bool = typer.Option(True)):
    """Analyse (or re-analyse) images. A person's corrections are never overwritten."""
    spec = {'image_ids': image_ids}
    if backend:
        spec['backend'] = backend
    _queue('analyze', spec, run)


@app.command()
def worker(job: str = typer.Option(None, help='Run this job id; default: the next queued or unfinished job.'),
           forever: bool = typer.Option(False, help='Keep taking jobs until stopped (Ctrl+C).')):
    """Continue unfinished jobs. Safe alongside the app: a lease stops two workers sharing a job."""
    if forever:
        stop = threading.Event()
        try:
            jobs.Worker().loop(stop)
        except KeyboardInterrupt:
            stop.set()
        return
    _work(job)


@app.command(name='jobs')
def list_jobs(limit: int = 15):
    """List recent jobs and their state."""
    with jobs.open_store() as store:
        _print(store.rows('SELECT id, kind, state, stage, message, backend, created_at, finished_at FROM jobs '
                          'ORDER BY created_at DESC LIMIT ?', (limit,)))


@app.command()
def job(job_id: str, action: str = typer.Argument('show', help='show, pause, resume or cancel')):
    """Show or control one job."""
    with jobs.open_store() as store:
        if action != 'show':
            store.request_job_state(job_id, action)
        _print({'job': store.one('SELECT * FROM jobs WHERE id=?', (job_id,)),
                'items': store.rows('SELECT kind, provider, provider_item_id, state, reason, image_id FROM job_items '
                                    'WHERE job_id=? ORDER BY id', (job_id,))})


@app.command()
def library(limit: int = 50):
    """List images in the library with their techniques."""
    with jobs.open_store() as store:
        _print(store.rows(
            "SELECT i.id, i.title, i.creator, i.provider, (SELECT label FROM rights_records r WHERE r.image_id=i.id "
            "ORDER BY r.id DESC LIMIT 1) AS licence, (SELECT group_concat(technique_id || ':' || state, ', ') FROM "
            "annotations a WHERE a.image_id=i.id) AS techniques FROM images i WHERE i.removed_at IS NULL "
            "ORDER BY i.id DESC LIMIT ?", (limit,)))


@app.command()
def remove(image_id: int, reason: str = typer.Option('removed from the command line')):
    """Remove an image, its files and annotations; it will not be collected again."""
    from atlas import images
    with jobs.open_store() as store:
        removed = store.remove_image(image_id, reason)
    images.delete_files(home_dir() / 'media', removed)
    typer.echo(f'Removed image {image_id}.')


@app.command()
def credits(fmt: str = typer.Option('md', '--format', help='md or csv'), collection: int = typer.Option(0)):
    """Print credits (attribution) for the library or a collection."""
    with jobs.open_store() as store:
        typer.echo(transfer.credits(store, collection_id=collection or None, fmt=fmt))


@app.command()
def backup():
    """Back up the whole library (database + images) into the backups folder."""
    _print(transfer.backup(home_dir()))


@app.command()
def restore(name: str = typer.Argument(..., help='A backup file name from the backups folder.')):
    """Restore a backup. A safety backup of the current library is made first. Close the app before restoring."""
    _print(transfer.restore(home_dir(), name))


@app.command(name='starter-import')
def starter_import():
    """Add the bundled starter library (used by the Windows installer; safe to run again)."""
    from atlas.home import REPO
    with jobs.open_store() as store:
        added = transfer.import_starter(store, home_dir(), REPO / 'starter')
    typer.echo(f'Starter library: {added} new reference(s) added.')


@app.command(name='starter-export', hidden=True)
def starter_export(out: str = typer.Option('starter', help='Folder to write (replaced).')):
    """Maintainers: write the current library as the bundled starter pack."""
    from pathlib import Path
    with jobs.open_store() as store:
        typer.echo(f'Exported {transfer.export_starter(store, home_dir(), Path(out))} references to {out}.')


@app.command()
def coverage():
    """Techniques by number of examples (fewest first)."""
    with jobs.open_store() as store:
        _print(catalog.coverage(store))


@app.command()
def doctor():
    """Check the data home, knowledge files and both AI assistants."""
    report = {'home': str(home_dir())}
    try:
        catalog.load()
        report['knowledge_files'] = 'ok'
    except ValueError as error:
        report['knowledge_files'] = str(error)
    for name in ('codex', 'claude'):
        try:
            report[name] = f'ready (version {jobs.BACKENDS[name].check(force=True)})'
        except jobs.BackendError as error:
            report[name] = jobs.backend_message(error.code, name)
    _print(report)


@app.command()
def serve(port: int = typer.Option(8775), worker: bool = typer.Option(True, help='Run the background job worker.')):
    """Run the local server without opening a window (developers and agents)."""
    import uvicorn

    from atlas.server import create_app
    application = create_app(start_worker=worker)
    typer.echo(f'Visual Atlas on http://127.0.0.1:{port}  (Ctrl+C to stop)')
    uvicorn.run(application, host='127.0.0.1', port=port, access_log=False)


@taxonomy_app.command('check')
def taxonomy_check():
    """Validate atlas/data/taxonomy.json and source_policies.json."""
    try:
        taxonomy, policies, *_ = catalog.load()
    except ValueError as error:
        typer.echo(str(error))
        raise typer.Exit(1)
    enabled = [p['id'] for p in policies['providers'] if p['status'] == 'enabled']
    typer.echo(f"OK: {len(taxonomy['goals'])} goals, {len(taxonomy['operations'])} operations, "
               f"{len(taxonomy['domains'])} domains, {len(taxonomy['techniques'])} techniques; "
               f"enabled sources: {', '.join(enabled)}.")


@taxonomy_app.command('sync')
def taxonomy_sync():
    """Reload the knowledge files into the library database now."""
    with jobs.open_store() as store:
        catalog.sync(store, force=True)
    typer.echo('Knowledge files reloaded.')
