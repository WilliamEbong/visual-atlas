# Review rubric for generated images

Each image is checked by eye at full size. Every check is pass or fail, and **any fail means the image is dropped**. The reason is recorded in `manifest.json` under `dropped`.

1. **Technique reads at a glance.** The technique's `observable_cues` in `atlas/data/taxonomy.json` are visible without explanation. The image is not easier to read as one of the techniques listed under its `confusions`, and it does not match the technique's `counterexample`.
2. **Anatomy.** Hands, faces, limbs and animals are correct, or they are absent or too small to judge. No extra or missing fingers, fused limbs or doubled heads.
3. **No artefacts.** No melted or merging objects, warped geometry where it should be straight, duplicated elements that should be single, seams, tiling errors, smeared patches or half-formed shapes.
4. **Coherent light and perspective.** One light logic, with shadows consistent with it. Perspective lines converge consistently, and reflections match what they reflect.
5. **Original.** Not a near-copy of any work in `STUDY.md` or any other known work: a different subject and a different composition.
6. **No text, logos or watermarks.** No letters, numbers, signatures, brand marks or pseudo-text.
7. **Craft.** A picture editor would keep it: deliberate composition, controlled tones, and no generic stock or "AI gloss" look (plastic sheen, HDR glow, oversaturation).
8. **Safe as a teaching example.** No real people, real landmarks or recognisable trademarks.
