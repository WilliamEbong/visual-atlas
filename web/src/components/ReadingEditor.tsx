import { useApp } from '../lib/hooks'
import type { Reading, ReadingCorrection } from '../lib/types'

export default function ReadingEditor({ reading, value, onChange }: {
  reading: Reading | null; value: ReadingCorrection | null; onChange: (value: ReadingCorrection | null) => void
}) {
  const { taxonomy } = useApp()
  const current = value ?? { technique_ids: reading?.techniques.map((t) => t.id) ?? [],
    goal_ids: reading?.goals.map((g) => g.id) ?? [], subject_terms: reading?.subject_terms ?? [] }
  const names = (kind: 'techniques' | 'goals', ids: string[]) => ids.map((id) => taxonomy?.[kind].find((t) => t.id === id)?.name ?? id).join(', ')
  return <section aria-label="Interpretation" className="stack" style={{ gap: 12 }}>
    <div className="mono" aria-live="polite">
      <p><strong>Goals:</strong> {names('goals', current.goal_ids) || 'No goal inferred'}</p>
      <p><strong>Techniques:</strong> {names('techniques', current.technique_ids) || 'No technique inferred'}</p>
      <p><strong>Subject words:</strong> {current.subject_terms.join(', ') || 'None yet'}</p>
    </div>
    <p className="mono muted">{value ? 'Your corrections apply to the next request.' : 'A suggested reading, using word matching. No AI call.'} The original brief is kept.</p>
    <details>
      <summary>Correct this reading</summary>
      <div className="stack" style={{ gap: 14, marginTop: 12 }}>
        {(['goals', 'techniques'] as const).map((kind) => {
          const key = kind === 'goals' ? 'goal_ids' : 'technique_ids'
          return <fieldset key={kind}><legend>{kind === 'goals' ? 'Goals' : 'Techniques'} — choose any, or none</legend>
            <div style={{ maxHeight: 190, overflowY: 'auto', padding: 4 }}>
              {taxonomy?.[kind].map((tag) => <label key={tag.id} className="choice plain" style={{ display: 'flex', marginBottom: 5 }}>
                <input type="checkbox" checked={current[key].includes(tag.id)} onChange={(event) => onChange({ ...current,
                  [key]: event.target.checked ? [...current[key], tag.id] : current[key].filter((id) => id !== tag.id) })} />
                {tag.name}</label>)}
            </div>
          </fieldset>
        })}
        <label className="field">Subject words (separate with commas, up to eight)
          <input value={current.subject_terms.join(', ')} onChange={(event) => onChange({ ...current,
            subject_terms: event.target.value.split(',').slice(0, 8).map((term) => term.trimStart()) })} /></label>
        <button type="button" className="quiet small" onClick={() => onChange(null)}>Use automatic reading</button>
      </div>
    </details>
    {!value && reading && reading.techniques.length + reading.goals.length > 0 && <details>
      <summary>Why these suggestions?</summary>
      <ul>{[...reading.goals, ...reading.techniques].map((tag) => <li key={tag.id}>{tag.name}: {tag.why}{tag.exact ? '' : ' — possible match'}</li>)}</ul>
    </details>}
  </section>
}
