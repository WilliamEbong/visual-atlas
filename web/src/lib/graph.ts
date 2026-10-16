import type { GraphData } from './types'

export interface Positioned { id: string; label: string; kind: string; thumb?: string | null; x: number; y: number }

/** Fixed readable columns; the surrounding viewport scrolls instead of shrinking labels to fit. */
export function layout(graph: GraphData): Positioned[] {
  const columns = [graph.nodes.filter((n) => !['technique', 'image'].includes(n.kind)),
    graph.nodes.filter((n) => n.kind === 'technique'), graph.nodes.filter((n) => n.kind === 'image')]
  const out: Positioned[] = []
  columns.forEach((nodes, column) => {
    const sorted = [...nodes].sort((a, b) => Number(b.id === graph.focus) - Number(a.id === graph.focus)
      || a.kind.localeCompare(b.kind) || a.label.localeCompare(b.label))
    sorted.forEach((node, index) => {
      out.push({ ...node, x: 115 + column * 285, y: 55 + index * 140 })
    })
  })
  return out
}

/** Accessible list alternative: each non-focus node with how it connects to others. */
export function adjacency(graph: GraphData) {
  const label = new Map(graph.nodes.map((node) => [node.id, node]))
  return graph.nodes.map((node) => ({
    id: node.id, label: node.label, kind: node.kind,
    links: graph.edges.filter((edge) => edge.source === node.id || edge.target === node.id).map((edge) => {
      const other = label.get(edge.source === node.id ? edge.target : edge.source)!
      return { ...edge, id: other.id, label: other.label }
    }),
  }))
}

export function route(nodeId: string): string {
  const [kind, id] = nodeId.split(':')
  return kind === 'image' ? `#/image/${id}` : kind === 'technique' ? `#/technique/${id}`
    : kind === 'goal' ? `#/explore/goal/${id}` : `#/connections?focus=${encodeURIComponent(nodeId)}`
}
