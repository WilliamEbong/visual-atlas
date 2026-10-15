# Plan 004 — Install, release, demo and documentation

- Installer and launcher adapted from Qualia (same owner).
- `atlas starter-export` / `atlas starter-import` move a library as `starter/library.json` plus
  reduced media copies, keeping the original SHA-256 for duplicate detection.
- `scripts/build_demo.py` records real API responses from a temporary library into `snapshot.json`
  and builds `web/dist-demo` in demo mode (read-only client).
- `scripts/build-release.ps1` mirrors `.github/workflows/release.yml` for a local zip.
