import { describe, expect, it } from 'vitest'
import { regionBox, regionLabel } from './regions'

describe('observation regions', () => {
  it('maps every named zone to a box inside the picture', () => {
    for (const name of ['whole', 'center', 'top', 'bottom', 'left', 'right', 'top-left', 'top-right', 'bottom-left',
      'bottom-right', 'foreground', 'middle-ground', 'background']) {
      const box = regionBox(name)!
      expect(box.x >= 0 && box.y >= 0 && box.x + box.w <= 100 && box.y + box.h <= 100).toBe(true)
    }
  })
  it('marks depth zones as approximate and ignores unknown names', () => {
    expect(regionBox('foreground')?.approximate).toBe(true)
    expect(regionBox('top-left')?.approximate).toBe(false)
    expect(regionBox('somewhere')).toBeNull()
    expect(regionLabel('middle-ground')).toBe('middle ground (approximate area)')
  })
})
