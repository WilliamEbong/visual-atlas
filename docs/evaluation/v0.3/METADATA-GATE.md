# v0.3 metadata-filter gate (fixed 2026-10-15, before any case is scored)

**Question.** Can a candidate that is plainly a documentation photograph, a specimen record shot or a page of
text be skipped before download, from its catalogue text alone, without losing images that show a technique?

**Case set.** At least 40 real candidate records drawn from the app's own searches across the enabled sources,
including at least 10 negatives. A *negative* is a picture with no visual technique worth filing: catalogue or
record shots of objects on plain grounds, specimen sheets, installation or exhibition views taken for the record,
and pages that are mostly text. A *positive* is a picture a person would file for at least one technique. The
builder labels every case from its thumbnail, with the catalogue text hidden, before any arm runs. The labels
are provisional builder judgments. They are saved in `metadata-cases.json` with each record's source id, its
catalogue text and the thumbnail's sha256, and the file's hash is recorded below before scoring.

**Arms.**
1. No filter (v0.2.0 behaviour).
2. Deterministic rules: phrases in title, medium, classification or description, kept as data in
   `atlas/data/metadata_filter.json`. The rules are written from the sources' documentation and field
   vocabularies, not from this case set.
3. Jev: one noul per case with the v1.1 question; skip at ≥ 0.8. This arm is optional and needs a key.

**Adopt an arm only if all of these hold:**
- no positive case is skipped;
- at least half of the negative cases are skipped;
- there are at least 10 negative cases. With fewer, the best outcome is "deferred".

**If adopted.** Discovery skips a matching candidate before download and records the reason with the matched
rule. Settings can switch the filter off. The Jev arm, if adopted, stays off by default and needs the user's own
key.

**Case file hash:** recorded here when the case file is written, before scoring.
