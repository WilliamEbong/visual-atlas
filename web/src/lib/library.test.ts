import { describe, expect, it } from 'vitest'
import { activeCount, apiPath, EMPTY, fromQuery, nextIndex, toQuery } from './library'

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
