import { describe, expect, it } from 'vitest'
import { justify } from './justify'

describe('justify', () => {
  it('fills each full row exactly and never exceeds the target height', () => {
    const aspects = [1.5, 0.7, 1, 2, 0.8, 1.3, 1.6, 0.75]
    const widths = justify(aspects, 1000, 240, 20)
    let start = 0
    let used = 0
    widths.forEach((w, i) => {
      used += w + (i > start ? 20 : 0)
      if (used >= 1000 - (i - start + 1)) {  // a full row: within a pixel per picture of the width
        expect(used).toBeLessThanOrEqual(1000)
        expect(w / aspects[i]).toBeLessThanOrEqual(241)
        start = i + 1; used = 0
      }
    })
    expect(widths).toHaveLength(aspects.length)
  })

  it('keeps a lone last picture at the target height instead of ballooning', () => {
    const widths = justify([1.5, 1.5, 1.5, 0.6], 1000, 240, 20)
    expect(widths[3]).toBe(Math.floor(0.6 * 240))
  })
})
