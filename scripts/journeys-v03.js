// v0.3 browser journeys (spec 006 T622). Run with the Playwright MCP tool browser_run_code_unsafe
// (filename: VisualAtlas/scripts/journeys-v03.js) against `atlas serve --port 8791` on a SCRATCH library whose
// backend is practice mode (fake). It changes that library: a Find job, a collection, a brief.
async (page) => {
  const base = 'http://127.0.0.1:8791/'
  const log = []
  const note = (step, ok, detail = '') => log.push({ step, ok, detail })
  const errors = []
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
  const toast = () => page.locator('.toast').last()

  // 1. Library: More filters, an active filter and its removal, arrow keys in the justified grid
  await page.goto(base + '#/')
  await page.getByRole('button', { name: /More filters/ }).click()
  await page.getByLabel('Shape').selectOption('portrait')
  await page.waitForTimeout(900)
  const portrait = await page.locator('.plate-item').count()
  await page.getByRole('button', { name: 'Remove filter: Portrait' }).click()
  await page.waitForTimeout(900)
  note('filter portrait then remove', portrait > 0 && (await page.locator('.plate-item').count()) > portrait, `${portrait} portrait`)
  await page.locator('a.plate').first().focus()
  await page.keyboard.press('ArrowDown')
  const down = await page.evaluate(() => [...document.querySelectorAll('a.plate')].indexOf(document.activeElement))
  note('arrow down moves to the next row', down > 0, `index ${down}`)

  // 2. Image page: previous/next by arrow keys, an observation lights its area
  await page.locator('a.plate').nth(1).click()
  await page.waitForSelector('.image-title h1')
  const first = page.url()
  await page.keyboard.press('ArrowRight')
  await page.waitForTimeout(900)
  note('arrow right opens the next result', page.url() !== first, page.url())
  const obs = page.locator('.observations button').first()
  if (await obs.count()) {
    await obs.focus()
    note('observation focus lights a marked area', (await page.locator('.region.lit').count()) <= 1)
  }

  // 3. Favourite and Undo
  const fav = page.getByRole('button', { name: /Favourite/ })
  const before = await fav.getAttribute('aria-pressed')
  await fav.click()
  await page.waitForTimeout(600)
  await toast().getByRole('button', { name: 'Undo' }).click()
  await page.waitForTimeout(900)
  note('favourite then Undo restores it', (await fav.getAttribute('aria-pressed')) === before)

  // 4. Save to a new collection, remove from it with Undo, delete it through the in-app confirm (Escape first)
  await page.getByRole('button', { name: 'Save to a collection' }).click()
  await page.getByLabel('New collection').fill('Journey board')
  await page.getByRole('button', { name: 'Create and save' }).click()
  await page.waitForTimeout(900)
  await page.goto(base + '#/collections')
  await page.getByRole('link', { name: 'Journey board' }).click()
  await page.waitForSelector('.plate-item')
  await page.getByRole('button', { name: 'Remove', exact: true }).first().click()
  await page.waitForTimeout(700)
  const emptied = await page.locator('.plate-item').count()
  await toast().getByRole('button', { name: 'Undo' }).click()
  await page.waitForTimeout(1200)
  note('remove from collection then Undo', emptied === 0 && (await page.locator('.plate-item').count()) === 1)
  await page.getByRole('button', { name: 'Delete this collection…' }).click()
  await page.keyboard.press('Escape')
  await page.waitForTimeout(400)
  note('Escape keeps the collection', await page.getByRole('heading', { name: 'Journey board' }).isVisible())
  await page.getByRole('button', { name: 'Delete this collection…' }).click()
  await page.locator('dialog[open]').getByRole('button', { name: 'Delete' }).click()
  await page.waitForTimeout(1000)
  note('confirm deletes and returns to Collections', page.url().endsWith('#/collections'))

  // 5. A brief, practice-mode directions, dismiss with Undo, delete through the confirm
  await page.goto(base + '#/project')
  await page.getByLabel('Project name').fill('Journey brief')
  await page.getByLabel(/The brief/).fill('Backlit figures against a pale evening sky for a festival flyer, calm but lively.')
  await page.getByRole('button', { name: 'Save and continue' }).click()
  await page.waitForSelector('text=How the atlas read your brief')
  const reading = await page.locator('div.tray-col').filter({ hasText: 'Techniques' }).innerText()
  note('brief reads silhouette from "backlit"', /Silhouette/.test(reading), reading.replace(/\s+/g, ' '))
  await page.getByRole('button', { name: /Suggest directions/ }).first().click()
  await page.waitForSelector('text=Show the results', { timeout: 60000 })
  await page.waitForTimeout(4000)
  await page.getByRole('button', { name: 'Show the results' }).click()
  await page.waitForTimeout(1200)
  const directions = await page.locator('article.tray-col').count()
  if (directions) {
    await page.locator('article.tray-col').first().getByRole('button', { name: 'Dismiss' }).click()
    await page.waitForTimeout(700)
    const after = await page.locator('article.tray-col').count()
    await toast().getByRole('button', { name: 'Undo' }).click()
    await page.waitForTimeout(1000)
    note('dismiss a direction then Undo', after === directions - 1 && (await page.locator('article.tray-col').count()) === directions, `${directions} directions`)
  } else note('practice-mode directions', false, 'none came back')
  await page.getByRole('button', { name: 'Delete this brief…' }).click()
  await page.locator('dialog[open]').getByRole('button', { name: 'Delete' }).click()
  await page.waitForTimeout(900)
  note('delete brief through the confirm', page.url().endsWith('#/project'))

  // 6. Find on the live Rijksmuseum (practice-mode analysis): timeline, counts and outcomes
  await page.goto(base + '#/find')
  await page.getByLabel('Describe what you need').fill('ships in a storm')
  for (const box of await page.locator('fieldset').filter({ hasText: 'Sources' }).locator('input[type=checkbox]').all()) {
    if (await box.isChecked()) await box.uncheck()
  }
  await page.getByLabel(/Rijksmuseum/).check()
  await page.getByLabel('How many new images').fill('2')
  await page.getByRole('button', { name: 'Start finding' }).click()
  await page.waitForSelector('.timeline', { timeout: 20000 })
  await page.waitForFunction(() => /Ready|Stopped short|Finished|Stopped/.test(document.querySelector('[aria-label="Job progress"] h2')?.textContent ?? ''), null, { timeout: 240000 })
  const heading = await page.locator('[aria-label="Job progress"] h2').innerText()
  const counts = await page.locator('.counts').innerText()
  note('Find on the Rijksmuseum finishes with counts', /Ready|Stopped short|Finished/.test(heading), `${heading} | ${counts.replace(/\s+/g, ' ')}`)
  return { log, errors }
}
