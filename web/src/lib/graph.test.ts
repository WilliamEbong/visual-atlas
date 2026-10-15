import { describe, expect, it } from 'vitest'
import { adjacency, layout, route } from './graph'
import type { GraphData } from './types'

const graph: GraphData = {
  focus: 'technique:a',
  nodes: [
    { id: 'technique:a', label: 'A', kind: 'technique', ring: 0 },
    { id: 'goal:g', label: 'Goal', kind: 'goal', ring: 1 },
    { id: 'technique:b', label: 'B', kind: 'technique', ring: 1 },
    { id: 'image:1', label: 'Pic', kind: 'image', ring: 2 },
  ],
  edges: [{ source: 'goal:g', target: 'technique:a', kind: 'serves' }, { source: 'technique:a', target: 'technique:b', kind: 'related' },
    { source: 'technique:a', target: 'image:1', kind: 'example' }],
}

describe('connection map', () => {
  it('places the focus at the centre and is deterministic', () => {
    const first = layout(graph)
    expect(first.find((n) => n.id === 'technique:a')).toMatchObject({ x: 0, y: 0 })
    expect(layout({ ...graph, nodes: [...graph.nodes].reverse() })).toEqual(expect.arrayContaining(first))
    const ring2 = first.find((n) => n.id === 'image:1')!
    expect(Math.hypot(ring2.x, ring2.y)).toBeGreaterThan(Math.hypot(first[1].x, first[1].y))
  })
  it('gives a text alternative listing every connection', () => {
    const list = adjacency(graph)
    expect(list.find((n) => n.id === 'technique:a')!.links.map((l) => l.id).sort()).toEqual(['goal:g', 'image:1', 'technique:b'])
  })
  it('routes nodes to their pages', () => {
    expect(route('image:1')).toBe('#/image/1')
    expect(route('goal:g')).toBe('#/explore/goal/g')
    expect(route('technique:b')).toBe('#/technique/b')
  })
})
