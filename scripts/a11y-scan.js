// Accessibility and layout-shift scan for the running app (spec 006 FR-14, FR-15). Run with the Playwright MCP tool
// browser_run_code_unsafe (filename: VisualAtlas/scripts/a11y-scan.js) against `atlas serve --port 8791` on a scratch
// library, with web/node_modules/axe-core served on 8792 (python -m http.server 8792 --bind 127.0.0.1 in that folder).
// axe-core (web devDependency, pinned) is fetched by Playwright and injected with page.evaluate, which the app's CSP
// does not block.
// Prints serious and critical WCAG 2.x A/AA violations per screen, light and dark, and the library's first-load CLS.
async (page) => {
  const base = 'http://127.0.0.1:8791/'
  const axe = await (await page.request.get('http://127.0.0.1:8792/axe.min.js')).text()
  const screens = ['#/', '#/image/7', '#/technique/silhouette', '#/explore', '#/explore/goal/create-calm', '#/find',
    '#/project', '#/collections', '#/compare?ids=7,8,9', '#/settings', '#/jobs', '#/connections']
  const report = { cls: null, screens: {} }
  await page.addInitScript(() => {
    window.__cls = 0
    new PerformanceObserver((list) => { for (const e of list.getEntries()) if (!e.hadRecentInput) window.__cls += e.value })
      .observe({ type: 'layout-shift', buffered: true })
  })
  for (const theme of ['light', 'dark']) {
    for (const hash of screens) {
      await page.goto(base + hash)
      await page.evaluate((t) => { document.documentElement.setAttribute('data-theme', t) }, theme)
      await page.waitForTimeout(1800)
      if (theme === 'light' && hash === '#/') report.cls = await page.evaluate(() => Math.round(window.__cls * 1000) / 1000)
      await page.evaluate(axe)
      const result = await page.evaluate(async () => {
        const r = await window.axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'], resultTypes: ['violations'] })
        return r.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
          .map((v) => ({ id: v.id, impact: v.impact, count: v.nodes.length, sample: v.nodes.slice(0, 2).map((n) => n.target.join(' ')) }))
      })
      report.screens[`${theme} ${hash}`] = result
    }
  }
  return report
}
