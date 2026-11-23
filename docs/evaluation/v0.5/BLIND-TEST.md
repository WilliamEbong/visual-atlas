# Blind test: does the reference desk make an agent's visual choices better?

This is the test that decides the product thesis (`docs/research/05-thesis.md`). Only the owner can run the rating step,
so it is prepared here and not yet run.

## Protocol
1. Write 12 to 20 briefs you would really hand an agent: slides, a poster, a web hero, a social post. Write each in
   one or two sentences, as you would type it. Put them in the table below before running anything.
2. For each brief, run two fresh agent sessions (Claude Code or Codex) with the same prompt: "Choose two reference
   images for this brief and say why each fits. Give their credits."
   - **A**: no Visual Atlas.
   - **B**: Visual Atlas MCP added (`claude mcp add visual-atlas ...`, see the user guide).
3. Shuffle the outputs so A and B cannot be told apart, for example by having another session relabel them X and Y.
4. Rate each output from 1 to 5 on fit, distinctiveness and "could I check its reasoning?".
5. Pass or fail checks for each B output:
   - every image proposed for published use carries its credit line;
   - no generated or design-system image is offered as freely publishable.
6. Thesis holds if B beats A on fit and checkable reasoning in at least two thirds of briefs, and the pass/fail
   checks never fail. If not, rethink before widening the layers.

## Briefs

| # | Brief | A fit | B fit | A reasoning | B reasoning | Credits OK |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
