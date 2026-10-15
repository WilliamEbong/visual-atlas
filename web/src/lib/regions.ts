// Observation regions are named zones (the analysis schema's REGIONS). Each maps to a box on the picture, in
// percent. Depth zones become horizontal bands and are only approximate. Pure, unit-tested.

export interface RegionBox { x: number; y: number; w: number; h: number; approximate: boolean }

const BOXES: Record<string, [number, number, number, number]> = {
  whole: [1, 1, 98, 98], center: [25, 25, 50, 50], top: [2, 2, 96, 40], bottom: [2, 58, 96, 40], left: [2, 2, 44, 96],
  right: [54, 2, 44, 96], 'top-left': [2, 2, 46, 46], 'top-right': [52, 2, 46, 46], 'bottom-left': [2, 52, 46, 46],
  'bottom-right': [52, 52, 46, 46], foreground: [2, 62, 96, 36], 'middle-ground': [2, 34, 96, 34], background: [2, 2, 96, 34],
}
const DEPTH = new Set(['foreground', 'middle-ground', 'background'])

export function regionBox(region: string): RegionBox | null {
  const box = BOXES[region]
  return box ? { x: box[0], y: box[1], w: box[2], h: box[3], approximate: DEPTH.has(region) } : null
}

export function regionLabel(region: string): string {
  const name = region.replace('-', ' ')
  return DEPTH.has(region) ? `${name} (approximate area)` : region === 'whole' ? 'the whole picture' : name
}
