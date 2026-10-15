import { describe, expect, it } from 'vitest'
import { activeCount, apiPath, appendPage, EMPTY, fromQuery, nextIndex, nextPages, toQuery } from './library'

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
