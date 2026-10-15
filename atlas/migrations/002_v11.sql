-- Visual Atlas 0.2 (v1.1): who made a tombstone, and labels that belong to the current analysis only.

-- A person's removal ('user') is final; an automatic "no clear technique" rejection ('auto') records the analysis
-- version that made it so a later version may look again. Rows made before 0.2 have NULL and are classified by
-- their reason, without rewriting the append-only rows.
ALTER TABLE tombstones ADD COLUMN source TEXT CHECK(source IN ('user','auto'));
ALTER TABLE tombstones ADD COLUMN rule_version TEXT NOT NULL DEFAULT '';
CREATE VIEW tombstone_kinds AS
  SELECT id, provider, provider_item_id, file_sha256, dhash, reason, rule_version, created_at,
         COALESCE(source, CASE WHEN reason LIKE 'not added:%' THEN 'auto' ELSE 'user' END) AS source
  FROM tombstones;

-- Labels left by an earlier analysis are superseded by the image's current analysis (a person's decisions stay).
INSERT INTO annotation_history(annotation_id, image_id, technique_id, state, role, evidence_json, effect,
                               confidence, analysis_id, human_locked, changed_by, note, created_at)
  SELECT a.id, a.image_id, a.technique_id, 'superseded', a.role, a.evidence_json, a.effect, a.confidence,
         i.analysis_id, 0, 'upgrade', 'superseded: not part of the current analysis',
         strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now')
  FROM annotations a JOIN images i ON i.id = a.image_id
  WHERE a.human_locked = 0 AND i.analysis_id IS NOT NULL AND a.analysis_id IS NOT NULL
    AND a.analysis_id != i.analysis_id;
DELETE FROM annotations WHERE id IN (
  SELECT a.id FROM annotations a JOIN images i ON i.id = a.image_id
  WHERE a.human_locked = 0 AND i.analysis_id IS NOT NULL AND a.analysis_id IS NOT NULL
    AND a.analysis_id != i.analysis_id);

-- Status follows the remaining active labels.
UPDATE images SET status = CASE WHEN EXISTS (SELECT 1 FROM annotations a WHERE a.image_id = images.id
                                               AND a.state != 'rejected') THEN 'ready' ELSE 'unanalyzed' END
  WHERE removed_at IS NULL AND status IN ('ready', 'unanalyzed');
