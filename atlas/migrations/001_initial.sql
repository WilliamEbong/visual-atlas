-- Visual Atlas schema v1. Knowledge tables are synced from atlas/data/*.json by atlas/catalog.py.

CREATE TABLE goals(id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL);
CREATE TABLE operations(id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL);
CREATE TABLE domains(id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
  variables_json TEXT NOT NULL);
CREATE TABLE techniques(id TEXT PRIMARY KEY, name TEXT NOT NULL, data_json TEXT NOT NULL);
CREATE TABLE technique_links(
  technique_id TEXT NOT NULL REFERENCES techniques(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN ('goal','operation','domain','related','confused_with')),
  target_id TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
  PRIMARY KEY(technique_id, kind, target_id));
CREATE TABLE source_policies(provider TEXT PRIMARY KEY, status TEXT NOT NULL, data_json TEXT NOT NULL);
CREATE TABLE data_versions(name TEXT PRIMARY KEY, sha256 TEXT NOT NULL, loaded_at TEXT NOT NULL);

CREATE TABLE images(
  id INTEGER PRIMARY KEY,
  provider TEXT NOT NULL, provider_item_id TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT '', creator TEXT NOT NULL DEFAULT '', date_text TEXT NOT NULL DEFAULT '',
  medium TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
  source_url TEXT NOT NULL,
  file_sha256 TEXT NOT NULL UNIQUE, analysis_sha256 TEXT NOT NULL, dhash TEXT NOT NULL,
  width INTEGER NOT NULL, height INTEGER NOT NULL, bytes INTEGER NOT NULL, mime TEXT NOT NULL,
  original_path TEXT, analysis_path TEXT, thumb_path TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','ready','unanalyzed')),
  analysis_id INTEGER REFERENCES analyses(id),
  favorite INTEGER NOT NULL DEFAULT 0 CHECK(favorite IN (0,1)),
  job_id TEXT, removed_at TEXT, created_at TEXT NOT NULL,
  UNIQUE(provider, provider_item_id));

CREATE TABLE rights_records(
  id INTEGER PRIMARY KEY, image_id INTEGER NOT NULL REFERENCES images(id),
  license_code TEXT NOT NULL, license_version TEXT NOT NULL, license_url TEXT NOT NULL,
  label TEXT NOT NULL, evidence_url TEXT NOT NULL, evidence_json TEXT NOT NULL,
  required_attribution TEXT NOT NULL, restrictions TEXT NOT NULL, permitted_mode TEXT NOT NULL,
  file_sha256 TEXT NOT NULL, retrieved_at TEXT NOT NULL, verified_at TEXT NOT NULL,
  policy_sha TEXT NOT NULL, provenance_json TEXT NOT NULL);

CREATE TABLE image_metrics(
  image_id INTEGER PRIMARY KEY REFERENCES images(id) ON DELETE CASCADE,
  aspect REAL NOT NULL, orientation TEXT NOT NULL, mean_luma REAL NOT NULL, contrast REAL NOT NULL,
  colorfulness REAL NOT NULL, saturation REAL NOT NULL, palette_json TEXT NOT NULL,
  color_family TEXT NOT NULL);

CREATE TABLE tombstones(
  id INTEGER PRIMARY KEY, provider TEXT NOT NULL, provider_item_id TEXT NOT NULL,
  file_sha256 TEXT NOT NULL, dhash TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL);

CREATE VIRTUAL TABLE images_fts USING fts5(title, creator, body, tokenize='porter unicode61 remove_diacritics 2');

CREATE TABLE analyses(
  id INTEGER PRIMARY KEY, image_id INTEGER REFERENCES images(id), job_id TEXT,
  task TEXT NOT NULL CHECK(task IN ('plan','analyze','verify','compare','directions')),
  backend TEXT NOT NULL, model TEXT NOT NULL, model_version TEXT, cli_version TEXT,
  prompt_sha TEXT NOT NULL, taxonomy_sha TEXT NOT NULL, input_sha TEXT NOT NULL,
  cache_key TEXT NOT NULL, result_json TEXT NOT NULL,
  input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL);
CREATE INDEX analyses_cache ON analyses(cache_key);
CREATE INDEX analyses_image ON analyses(image_id, task);

CREATE TABLE annotations(
  id INTEGER PRIMARY KEY,
  image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
  technique_id TEXT NOT NULL REFERENCES techniques(id),
  state TEXT NOT NULL CHECK(state IN ('proposed','model_reviewed','human_reviewed','rejected')),
  role TEXT NOT NULL DEFAULT 'supporting' CHECK(role IN ('primary','supporting')),
  evidence_json TEXT NOT NULL, effect TEXT NOT NULL, confidence REAL NOT NULL,
  analysis_id INTEGER REFERENCES analyses(id),
  human_locked INTEGER NOT NULL DEFAULT 0 CHECK(human_locked IN (0,1)),
  changed_by TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL,
  UNIQUE(image_id, technique_id));

CREATE TABLE annotation_history(
  id INTEGER PRIMARY KEY, annotation_id INTEGER NOT NULL, image_id INTEGER NOT NULL,
  technique_id TEXT NOT NULL, state TEXT NOT NULL, role TEXT NOT NULL, evidence_json TEXT NOT NULL,
  effect TEXT NOT NULL, confidence REAL NOT NULL, analysis_id INTEGER, human_locked INTEGER NOT NULL,
  changed_by TEXT NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL);

CREATE TRIGGER annotations_history_insert AFTER INSERT ON annotations BEGIN
  INSERT INTO annotation_history(annotation_id,image_id,technique_id,state,role,evidence_json,effect,
    confidence,analysis_id,human_locked,changed_by,note,created_at)
  VALUES(NEW.id,NEW.image_id,NEW.technique_id,NEW.state,NEW.role,NEW.evidence_json,NEW.effect,
    NEW.confidence,NEW.analysis_id,NEW.human_locked,NEW.changed_by,NEW.note,NEW.updated_at);
END;
CREATE TRIGGER annotations_history_update AFTER UPDATE ON annotations BEGIN
  INSERT INTO annotation_history(annotation_id,image_id,technique_id,state,role,evidence_json,effect,
    confidence,analysis_id,human_locked,changed_by,note,created_at)
  VALUES(NEW.id,NEW.image_id,NEW.technique_id,NEW.state,NEW.role,NEW.evidence_json,NEW.effect,
    NEW.confidence,NEW.analysis_id,NEW.human_locked,NEW.changed_by,NEW.note,NEW.updated_at);
END;

CREATE TABLE collections(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE collection_items(
  collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
  image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
  position INTEGER NOT NULL DEFAULT 0, note TEXT NOT NULL DEFAULT '', added_at TEXT NOT NULL,
  PRIMARY KEY(collection_id, image_id));

CREATE TABLE briefs(id INTEGER PRIMARY KEY, title TEXT NOT NULL, text TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE directions(id INTEGER PRIMARY KEY, brief_id INTEGER NOT NULL REFERENCES briefs(id) ON DELETE CASCADE,
  analysis_id INTEGER REFERENCES analyses(id), position INTEGER NOT NULL, result_json TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'proposed' CHECK(state IN ('proposed','kept','dismissed')), created_at TEXT NOT NULL);
CREATE TABLE comparisons(id INTEGER PRIMARY KEY, image_ids TEXT NOT NULL,
  analysis_id INTEGER NOT NULL REFERENCES analyses(id), created_at TEXT NOT NULL);
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE jobs(
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK(kind IN ('find','grow','analyze','verify','compare','directions')),
  spec_json TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('queued','running','paused','cancelling','cancelled','done','failed')),
  stage TEXT NOT NULL DEFAULT 'queued', message TEXT NOT NULL DEFAULT '', error_code TEXT,
  backend TEXT NOT NULL, model TEXT NOT NULL,
  lease_owner TEXT, lease_until REAL, heartbeat_at REAL,
  created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT);
CREATE TABLE job_items(
  id INTEGER PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN ('query','candidate')), key TEXT NOT NULL,
  provider TEXT NOT NULL, provider_item_id TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL, state TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '',
  attempts INTEGER NOT NULL DEFAULT 0, next_attempt_at REAL NOT NULL DEFAULT 0,
  image_id INTEGER REFERENCES images(id), updated_at TEXT NOT NULL,
  UNIQUE(job_id, kind, key));
CREATE INDEX job_items_provider ON job_items(provider, provider_item_id);
CREATE TABLE attempts(
  id INTEGER PRIMARY KEY, job_id TEXT, item_id INTEGER,
  kind TEXT NOT NULL CHECK(kind IN ('search','download','ai')),
  backend TEXT NOT NULL DEFAULT '', model TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL CHECK(status IN ('ok','error')), error_code TEXT,
  input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0,
  latency_ms INTEGER NOT NULL DEFAULT 0, cli_version TEXT, created_at TEXT NOT NULL);
