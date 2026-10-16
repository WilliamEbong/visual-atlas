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
  it('keeps stable readable columns and puts the focus first in its column', () => {
    const first = layout(graph)
    expect(first.find((n) => n.id === 'technique:a')).toMatchObject({ x: 400, y: 55 })
    expect(layout({ ...graph, nodes: [...graph.nodes].reverse() })).toEqual(expect.arrayContaining(first))
    expect(first.find((n) => n.id === 'image:1')!.x).toBeGreaterThan(first.find((n) => n.id === 'technique:a')!.x)
    expect(first.find((n) => n.id === 'technique:b')!.y).toBeGreaterThan(150)
  })
  it('gives a text alternative listing every connection', () => {
    const list = adjacency(graph)
    expect(list.find((n) => n.id === 'technique:a')!.links.map((l) => l.id).sort()).toEqual(['goal:g', 'image:1', 'technique:b'])
  })
  it('routes nodes to their pages', () => {
    expect(route('image:1')).toBe('#/image/1')
    expect(route('goal:g')).toBe('#/explore/goal/g')
    expect(route('technique:b')).toBe('#/technique/b')
    expect(route('operation:isolate')).toBe('#/connections?focus=operation%3Aisolate')
    expect(route('domain:space')).toBe('#/connections?focus=domain%3Aspace')
  })
  it('preserves the identity and explanation of reciprocal relationships', () => {
    const forward = { source: 'technique:a', target: 'technique:b', kind: 'related', explanation: 'A builds on B.' }
    const reverse = { source: 'technique:b', target: 'technique:a', kind: 'related', explanation: 'B can create A.' }
    const list = adjacency({ ...graph, edges: [forward, reverse] })
    const links = list.find((node) => node.id === 'technique:a')!.links
    expect(links).toEqual([{ ...forward, id: 'technique:b', label: 'B' }, { ...reverse, id: 'technique:b', label: 'B' }])
    expect(new Set(links.map((link) => `${link.source}-${link.target}-${link.kind}`)).size).toBe(2)
  })
})
