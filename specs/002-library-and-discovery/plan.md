# Plan 002 — Library, discovery and corrections

- Reuses the spec 001 modules. Connectors are one function each in `atlas/providers.py`; licence
  rules are one function each in `atlas/rights.py`; filters live in `atlas/jobs.py::_download`.
- UI: `web/src/components/{Library,ImagePage,Find,JobProgress,Jobs,Collections,Compare}.tsx`,
  filters kept in the URL (`web/src/lib/library.ts`).
- Comparisons and project directions are jobs, so they share progress, budgets, leases and resume.
- Codex task 2 owns tests for fetch, images, rights and providers.
