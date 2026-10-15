# TypeSafe Jev decision gate (v1.1)

Written on 2026-10-15, **before any Jev call**. Jev is evaluated against what Visual Atlas already does, one use at
a time, on frozen inputs. "No integration justified" is a valid outcome. Rights decisions, licence evidence and
review states are never in scope: Jev can never authorise an image or mark anything reviewed.

## What was checked first (official sources only, 2026-10-15)
- API: `POST https://api.typesafe.ai/v1/systemone` with `state`, `model` and typed `questions` (choice, score,
  noul); bearer key (docs.typesafe.ai quick start). Noul returns a 0–1 probability of "yes"; the docs do not
  claim these probabilities are calibrated (docs.typesafe.ai/confidence).
- Models: `jev-1.14.0` was released as `jev-preview` (typesafe.ai/blog/jev-1-14); `jev-latest` moves to it a week
  later; `jev-1.13.0` stays available. **Pinned for this evaluation: `jev-1.13.0`** (the production model behind
  `jev-latest` on this date; the returned model id is recorded with every answer).
- Images are an experimental "danger zone" header that the vendor says is not production-ready, so **every arm
  here is text only**.
- Price: $0.042 per million input tokens, output free (typesafe.ai launch post). Spend is estimated from the
  returned token usage and capped at **$0.50** for the whole evaluation.
- Data: requests go to TypeSafe in the United States. The launch material says customer data is not used for
  training, but there is no general zero-retention promise. Only the evaluation's own text is sent: frozen briefs,
  starter-pack catalogue text, evaluation-case catalogue text and model evidence sentences. No image and nothing
  from the owner's library is sent.
- Key: the owner's own key (the one Qualia uses), with permission for **local evaluation only**. It is read into
  memory and never printed, logged or written. The public product will never ship or use it; if Jev is ever
  integrated, each user brings their own key.

## Arms, inputs and adoption criteria (fixed before running)
Each use compares the same frozen inputs across three arms:
1. the v1 baseline;
2. the improved v1.1 deterministic or existing-model step;
3. that step with Jev added or substituted.

Small samples are reported with 95% Wilson intervals. A use is integrated only if **every** criterion holds.

### 1. Request coding (the owner's "tag the prompt like qualitative coding" idea)
- **Input:** the 16 frozen briefs and the builder's codes (`briefs.json`).
- **Arms:**
  1. v1: no coding.
  2. v1.1: the deterministic coder (`atlas/coding.py`).
  3. Jev: one call per brief, with one noul question per technique and per goal. Each question carries the
     code's definition and terms. A tag is set when the answer is ≥ 0.5.
- **Adopt if all hold:**
  - micro-F1 (techniques and goals together) is at least 0.15 above the deterministic coder;
  - precision is at least 0.60;
  - feeding the Jev tags into the same retrieval raises recall@20 by at least 0.05 over the deterministic
    reading;
  - no brief fails after one retry;
  - median latency is at most 5 s;
  - repeating 4 briefs gives identical tag sets for at least 3 of them.

### 2. Relevance ranking of library references for a brief
- **Input:** the 16 frozen briefs over the 85 starter references.
- **Arms:**
  1. v1: newest first.
  2. v1.1: the deterministic relevance ranking.
  3. Jev: one call per brief, with one noul question per reference ("useful supporting evidence for this
     brief?"). Each question carries the reference's title, maker, date, summary and technique names.
- **Adopt if all hold:**
  - recall@20 is at least 0.10 above the deterministic ranking;
  - the estimated cost is at most $0.01 per brief;
  - median latency is at most 10 s;
  - no brief fails after one retry.

### 3. Metadata classification (skip documentation photos before downloading)
- **Input:** the 25 evaluation cases' catalogue text (title, maker, date, medium, description).
- **Arms:**
  1. v1 and v1.1: no filter (every eligible candidate is analysed).
  2. Jev: one noul per case ("plain documentation photograph or page of text?"); the candidate is skipped at
     ≥ 0.8.
- **Adopt if all hold:**
  - no case with a reference technique is skipped;
  - at least half of the negative cases are skipped.
- **Small-sample rule:** with fewer than 10 negative cases, the best possible outcome is "promising, deferred",
  never "integrated".

### 4. Annotation review (text only)
- **Input:** the Codex proposals and their evidence sentences from the development and final runs.
- **Arms:**
  1. the current pixel checker (shown the proposals);
  2. the independent-first pixel checker;
  3. Jev, reading only the technique definition and the cited evidence sentences.
- **Limit:** Jev never sees the pixels, so it cannot replace the image checker; that is excluded in advance.
- **Adopt** as a cheap pre-filter only if both hold:
  - false rejection is at most 0.10;
  - false acceptance is at least 0.15 lower than the current checker's.

Results and the decision for each use are in [REPORT.md](REPORT.md).
