import type { GraphData } from './types'

export interface Positioned { id: string; label: string; kind: string; thumb?: string | null; x: number; y: number }

/** Stable layout: the focus in the centre, then rings; nodes on a ring sorted by kind then label, so the
 *  same focus always draws the same picture (no random force layout). Pure, unit-tested. */
export function layout(graph: GraphData, radius = 220): Positioned[] {
  const rings = new Map<number, GraphData['nodes']>()
  for (const node of graph.nodes) rings.set(node.ring, [...(rings.get(node.ring) ?? []), node])
  const out: Positioned[] = []
  for (const [ring, nodes] of [...rings.entries()].sort(([a], [b]) => a - b)) {
    const sorted = [...nodes].sort((a, b) => a.kind.localeCompare(b.kind) || a.label.localeCompare(b.label))
    sorted.forEach((node, index) => {
      if (ring === 0) { out.push({ ...node, x: 0, y: 0 }); return }
      const angle = -Math.PI / 2 + (2 * Math.PI * index) / sorted.length + (ring % 2 ? 0 : Math.PI / sorted.length)
      const r = radius * ring * (sorted.length > 14 ? 1.25 : 1)
      out.push({ ...node, x: Math.round(Math.cos(angle) * r), y: Math.round(Math.sin(angle) * r) })
    })
  }
  return out
}

/** Accessible list alternative: each non-focus node with how it connects to others. */
export function adjacency(graph: GraphData): { id: string; label: string; kind: string; links: { id: string; label: string; kind: string }[] }[] {
  const label = new Map(graph.nodes.map((node) => [node.id, node]))
  return graph.nodes.map((node) => ({
    id: node.id, label: node.label, kind: node.kind,
    links: graph.edges.filter((edge) => edge.source === node.id || edge.target === node.id).map((edge) => {
      const other = label.get(edge.source === node.id ? edge.target : edge.source)!
      return { id: other.id, label: other.label, kind: edge.kind }
    }),
  }))
}

export function route(nodeId: string): string {
  const [kind, id] = nodeId.split(':')
  return kind === 'image' ? `#/image/${id}` : kind === 'technique' ? `#/technique/${id}` : `#/explore/goal/${id}`
}
