# Adapt mode

Use to fit a chosen recipe to user data, object names, variables, or existing code.

1. Enforce the backend gate before emitting executable adapted code.
2. Inspect the selected Scheme's `executable_plan`, recipe schema, SemanticCard,
   input contract, dependencies, and provenance tier; compare them with the
   user's actual data schema. `visual_only`, `reference_only`, and non-callable
   source candidates cannot satisfy an execution request.
3. Refuse silent unit-of-analysis changes. Flag pseudoreplication, missing sample
   identifiers, absent statistics, or incompatible objects before adaptation.
4. Generalize names and paths; preserve analysis meaning. Separate data adapter,
   plotting function, modifiers, and optional export.
5. Return code plus a minimal call example, assumptions, and unsupported claims.
6. Run `plot_library.py preflight` before execution. Do not run merely because
   code was adapted. If rendering is requested, execute the exact formal chain
   through `plot_library.py render --review-state ...`, then complete the native
   visual-review loop.

Never add fabricated columns, statistics, significance markers, or mock results to
make a recipe fit.
