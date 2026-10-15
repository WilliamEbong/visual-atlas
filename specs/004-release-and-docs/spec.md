# Spec 004 — Install, release, demo and documentation

## Functional requirements
- FR-1 Windows: download the zip, Unblock, double-click "Install Visual Atlas.cmd", get Desktop and
  Start-menu shortcuts; the app opens in its own window and closing the window stops it (idle
  detection; a running job counts as activity). Safe to re-run for updates.
- FR-2 A starter library is bundled (licence-checked references with analyses, ≤1024 px copies) and
  imported by the installer; references the user removed stay removed.
- FR-3 Backups (database, media and a manifest with SHA-256) and verified restore with a safety backup.
- FR-4 A public read-only demo built from the starter pack (GitHub Pages); releases built by CI.
- FR-5 README in Qualia's shape, an illustrated user guide, a quick start, a welcome-back handoff and
  a GIF tour.

## Success criteria
Fresh-install test from a locally built zip into a scratch home passes; the demo build runs; the docs
match the app.
