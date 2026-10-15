import { describe, expect, it } from 'vitest'
import { activeCount, activeFilters, apiPath, appendPage, EMPTY, fromQuery, nextByPosition, nextIndex, nextPages, toQuery } from './library'

describe('justified grid keyboard movement', () => {
  // two rows of different lengths: [0 wide][1][2] / [3][4 wide]
  const boxes = [{ left: 0, top: 0, width: 500 }, { left: 520, top: 0, width: 200 }, { left: 740, top: 0, width: 260 },
    { left: 0, top: 300, width: 300 }, { left: 320, top: 300, width: 680 }]
  it('moves up and down to the nearest item in the next row', () => {
    expect(nextByPosition(boxes, 0, 'ArrowDown')).toBe(3)   // centre 250 -> [3] centre 150
    expect(nextByPosition(boxes, 2, 'ArrowDown')).toBe(4)   // centre 870 -> [4] centre 660
    expect(nextByPosition(boxes, 4, 'ArrowUp')).toBe(1)     // centre 660 -> [1] centre 620
    expect(nextByPosition(boxes, 1, 'ArrowUp')).toBe(1)     // no row above
    expect(nextByPosition(boxes, 3, 'ArrowDown')).toBe(3)   // no row below
  })
  it('moves along the reading order and to the ends', () => {
    expect(nextByPosition(boxes, 2, 'ArrowRight')).toBe(3)
    expect(nextByPosition(boxes, 0, 'ArrowLeft')).toBe(0)
    expect(nextByPosition(boxes, 2, 'End')).toBe(4)
    expect(nextByPosition(boxes, 4, 'Home')).toBe(0)
    expect(nextByPosition(boxes, 2, 'Enter')).toBe(2)
  })
})

describe('active filter labels', () => {
  it('names each filter in use with the change that removes it', () => {
    const labels = activeFilters({ ...EMPTY, q: 'fog', technique: 'silhouette', favorite: true, sort: 'title' }, { silhouette: 'Silhouette' })
    expect(labels.map((f) => f.label)).toEqual(['“fog”', 'Silhouette', 'Favourites'])
    expect(labels[2].clear).toEqual({ favorite: false })
  })
})

describe('library filters', () => {
  it('round-trips through the URL and drops defaults', () => {
    const filters = { ...EMPTY, q: 'fog', technique: 'negative-space', favorite: true, sort: 'title' }
    const query = new URLSearchParams(toQuery(filters))
    expect(Object.fromEntries(query)).toEqual({ q: 'fog', technique: 'negative-space', favorite: '1', sort: 'title' })
    expect(fromQuery(query)).toEqual(filters)
    expect(activeCount(filters)).toBe(3)
  })
  it('builds the API path with paging and the favourite flag', () => {
    expect(apiPath({ ...EMPTY, favorite: true, color: 'blue' }, 30, 60)).toBe('library?color=blue&favorite=true&limit=30&offset=60')
  })
})

describe('grid keyboard movement', () => {
  it('moves by row and column and stays inside the grid', () => {
    expect(nextIndex(0, 'ArrowRight', 4, 10)).toBe(1)
    expect(nextIndex(5, 'ArrowUp', 4, 10)).toBe(1)
    expect(nextIndex(8, 'ArrowDown', 4, 10)).toBe(9)
    expect(nextIndex(0, 'ArrowLeft', 4, 10)).toBe(0)
    expect(nextIndex(3, 'End', 4, 10)).toBe(9)
    expect(nextIndex(7, 'Home', 4, 10)).toBe(0)
    expect(nextIndex(2, 'Enter', 4, 10)).toBe(2)
  })
})

describe('appendPage', () => {
  it('adds the next page without repeating images whose offsets shifted', () => {
    const merged = appendPage([{ id: 3 }, { id: 2 }], [{ id: 2 }, { id: 1 }])
    expect(merged.map((item) => item.id)).toEqual([3, 2, 1])
  })
})

describe('nextPages', () => {
  it('keeps advancing the offset when new images make a page repeat what is shown, and stops on an empty page', () => {
    let pages = nextPages({ key: '', items: [], consumed: 0, done: false }, 'k', [{ id: 9 }, { id: 8 }])
    pages = nextPages(pages, 'k', [{ id: 9 }, { id: 8 }])  // shifted offsets: only repeats
    expect(pages.items.map((item) => item.id)).toEqual([9, 8])
    expect(pages.consumed).toBe(4)  // the next request asks for rows after these, not the same offset again
    expect(nextPages(pages, 'k', []).done).toBe(true)
    expect(nextPages(pages, 'other filters', [{ id: 1 }]).consumed).toBe(1)  // new filters start over
  })
})
