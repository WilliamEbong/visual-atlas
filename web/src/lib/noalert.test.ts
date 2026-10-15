import { expect, test } from 'vitest'

// Browser alert, confirm and prompt boxes are replaced by in-app notices and dialogs (spec 006 FR-12).
const sources = import.meta.glob(['../**/*.ts', '../**/*.tsx', '!../**/*.test.ts'], { query: '?raw', import: 'default', eager: true }) as Record<string, string>

test('no browser alert, confirm or prompt in the web app', () => {
  expect(Object.keys(sources).length).toBeGreaterThan(10)
  const offenders = Object.entries(sources).filter(([, text]) =>
    /\b(?:window\.)?(?:alert|confirm|prompt)\s*\(/.test(text.replace(/\bconfirm\(\{/g, ''))).map(([path]) => path)
  expect(offenders).toEqual([])
})
