export type State = 'proposed' | 'model_reviewed' | 'human_reviewed' | 'rejected'

export interface TechniqueRef { id: string; name: string; state?: State }

export interface LibraryItem {
  id: number; title: string; creator: string; date_text: string; provider: string; thumb?: string
  width: number; height: number; status: string; favorite: number; created_at: string
  orientation: string; color_family: string; palette: string[]; license_label: string
  technique_count: number; techniques: TechniqueRef[]
}

export interface Annotation {
  id: number; technique_id: string; name: string; definition: string; state: State; role: 'primary' | 'supporting'
  evidence: string[]; effect: string; confidence: number; changed_by: string; note: string; updated_at: string; human_locked: number
  proposed_backend: string | null; proposed_model: string | null
}

export interface ImageDetail {
  image: { id: number; title: string; creator: string; date_text: string; medium: string; description: string; provider: string
    provider_item_id: string; source_url: string; width: number; height: number; status: string; favorite: number
    created_at: string; file_sha256: string; original?: string; display?: string; thumb?: string }
  rights: { license_code: string; license_version: string; license_url: string; label: string; evidence_url: string
    required_attribution: string; restrictions: string; permitted_mode: string; retrieved_at: string; verified_at: string
    evidence: Record<string, unknown>; provenance: Record<string, unknown> } | null
  metrics: { aspect: number; orientation: string; mean_luma: number; contrast: number; colorfulness: number; saturation: number
    color_family: string; palette: { hex: string; share: number; name: string }[] } | null
  analysis: { observations: { id: string; text: string; region: string }[]; summary: string; ambiguities: string[]
    subjects: string[]; creator_intent: { statement: string; metadata_field: string } | null; image_usable: boolean
    backend: string; model: string; created_at: string } | null
  annotations: Annotation[]
  history: { technique_id: string; state: string; changed_by: string; note: string; effect: string; created_at: string }[]
  goals: { id: string; name: string }[]
  collections: { id: number; name: string }[]
  related: { id: number; title: string; creator: string; thumb?: string; width: number; height: number; shared: number; via: string[] }[]
}

export interface Goal { id: string; name: string; description: string }
export interface TaxonomyTechnique { id: string; name: string; aliases: string[]; definition: string; goals: string[]
  operations: string[]; domains: string[]; examples: number }
export interface Taxonomy { goals: Goal[]; operations: Goal[]; domains: (Goal & { variables: string[] })[]; techniques: TaxonomyTechnique[] }

export interface TechniqueDetail {
  id: string; name: string; aliases: string[]; definition: string; explanation: string; when_it_helps: string[]
  observable_cues: string[]; limitations: string; counterexample: string; working_definition: boolean
  sources: { citation: string; url: string }[]
  confusions: { technique: string; name: string; how_to_tell: string }[]
  related: { id: string; name: string; relation: string }[]
  goals: Goal[]; operations: Goal[]; domains: Goal[]
  examples: { id: number; title: string; creator: string; date_text: string; thumb?: string; display?: string; width: number; height: number
    state: State; effect: string; role: string }[]
}

export interface Job {
  id: string; kind: string; state: string; stage: string; message: string; error_code: string | null; backend: string; model: string
  created_at: string; started_at: string | null; finished_at: string | null; spec: Record<string, unknown>
  counts: Record<string, number>; searches: number; added: { id: number; title: string; thumb?: string }[]
  matching: number; checked: number
  items?: { id: number; kind: string; provider: string; state: string; reason: string; image_id: number | null; title: string | null; query: string | null }[]
}

export interface Collection { id: number; name: string; description: string; size: number; covers: string[]; created_at: string }

export interface Direction {
  id: number; state: 'proposed' | 'kept' | 'dismissed'; title: string; idea: string; rationale: string
  execution: string[]; tradeoffs: string[]; images: { id: number; title: string; thumb?: string }[]
  techniques: { id: string; name: string }[]; backend: string; model: string; model_version: string | null
}

export interface Tag { id: string; name: string; exact: boolean; why: string }
export interface Reading { techniques: Tag[]; goals: Tag[]; subject_terms: string[] }
export interface Brief { id: number; title: string; text: string; created_at: string; updated_at: string; directions?: Direction[]; reading?: Reading }

export interface Settings { backend: 'codex' | 'claude' | 'fake'; verify_with: 'codex' | 'claude' | 'none'; daily_ai_cap: number; welcomed: boolean
  jev_ranking: boolean; jev_key: boolean }

export interface GraphData { focus: string; nodes: { id: string; label: string; kind: 'goal' | 'technique' | 'image'; thumb?: string | null; ring: number }[]
  edges: { source: string; target: string; kind: string }[] }

export const STATE_LABEL: Record<State, string> = {
  proposed: '○ proposed by a model', model_reviewed: '◐ agreed by a second model', human_reviewed: '● confirmed by you',
  rejected: '✕ rejected',
}

export const PROVIDERS: Record<string, string> = {
  aic: 'Art Institute of Chicago', met: 'The Met', cma: 'Cleveland Museum of Art', smithsonian: 'Smithsonian', commons: 'Wikimedia Commons',
  rijksmuseum: 'Rijksmuseum', nga: 'National Gallery of Art',
}
