import { useEffect, useLayoutEffect, useMemo, useRef, useState, type RefObject } from 'react'

/**
 * Widths for a justified picture layout: pictures keep their shape, every full row fills the width exactly,
 * and no row is taller than the target. The last row stretches only while that keeps it under 1.5 times
 * the target; otherwise it sits at the target height, left-aligned.
 */
export function justify(aspects: number[], width: number, target: number, gap: number): number[] {
  const widths: number[] = []
  let row: number[] = []
  const height = (items: number[]) => (width - gap * (items.length - 1)) / items.reduce((a, b) => a + b, 0)
  const flush = (h: number) => { row.forEach((a) => widths.push(Math.max(1, Math.floor(a * h)))); row = [] }
  for (const aspect of aspects) {
    row.push(aspect)
    if (height(row) <= target) flush(height(row))
  }
  if (row.length) { const h = height(row); flush(h <= target * 1.5 ? h : target) }
  return widths
}

/** Measures the container and returns each picture's width, or null before the first measurement. */
export function useJustified(ref: RefObject<HTMLElement | null>, aspects: number[], row: number, phoneRow = Math.round(row * 0.6)): number[] | null {
  const [box, setBox] = useState<{ width: number; gap: number } | null>(null)
  const observed = useRef<{ element: HTMLElement; observer: ResizeObserver } | null>(null)
  useLayoutEffect(() => {  // every render: the container may appear only once its data has loaded
    const element = ref.current
    if (observed.current?.element === element) return
    observed.current?.observer.disconnect()
    observed.current = null
    if (!element) return
    const measure = () => {
      const width = Math.floor(element.clientWidth)
      const gap = parseFloat(getComputedStyle(element).columnGap) || 0
      setBox((now) => now && now.width === width && now.gap === gap ? now : { width, gap })
    }
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    observed.current = { element, observer }
    measure()
  })
  useEffect(() => () => observed.current?.observer.disconnect(), [])
  const key = aspects.join(',')
  return useMemo(() => box && box.width > 0 ? justify(aspects, box.width, box.width < 600 ? phoneRow : row, box.gap) : null,
    [box, key, row, phoneRow])
}
