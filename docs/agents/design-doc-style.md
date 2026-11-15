# Working with the design document

The design document describes the design as it stands, with relevant rationale. It is not a status-tracking
or history document.

When updating it:

- Preserve established terminology.
- State settled design plainly; mark open or evolving areas **Provisional** and keep the §11 rollup in step.
- When a decision changes, rewrite the affected text to describe the new design; do not narrate what it
  replaced ("previously", "no longer", "superseded").
- Retain rationale that explains a non-obvious current decision.
- Leave procurement and CAD state, and detailed BOM data, to `bom/bom.csv`.

## Purpose and content

A reader, human or agent, should be able to build a complete, coherent picture of what is in the design, why,
how it fits together, and the calculations and constraints behind the basic element selections and gross
dimensions. It conveys absolute and relative scale. Detailed dimensional validation belongs in the models,
which are the single source for dimensions.

- **Dimensions:** state one only when the narrative uses it (a calculation, constraint, selection rationale,
  or sense of scale). Otherwise name the parameter and the module holding it, or omit it. Never copy a
  model-held dimension into the text for completeness, and never hand-copy values the model computes.
- **Shop-reference dimensions:** the document is also the shop reference during construction, so dimensions a
  builder works to belong in it: hole sizes and clearances, plate and stock sizes, alignments, stack
  positions. State them as committed fabrication values and keep them in step with the model parameters (a
  test pins the important ones). On a conflict the model governs: fix the text.
- **Measured values:** keep them, and the rule for which source governs (e.g. measurement over datasheet),
  only where no model parameter holds them yet. Once one does, state the provenance and leave the value to
  the model.
- **Part and hardware callouts:** each must say where in the kit the part is used and which particular part
  to use in a given place. Name each part by the identifier the BOM uses and say where it goes. The document
  may be printed as a desktop reference for the build crew, so a callout must identify the part without
  opening the code.
