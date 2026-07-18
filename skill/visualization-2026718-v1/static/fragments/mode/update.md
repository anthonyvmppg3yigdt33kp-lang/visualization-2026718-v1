# Update mode

Use to scan a refreshed source library and create an ingestion proposal.

1. Load the extension protocol and recipe schema. Run update in `--dry-run` first.
2. Treat the embedded source snapshot and manually curated recipes as immutable.
   Compare normalized content fingerprints; do not key identity only by filenames.
3. Classify new fences and images, correct language labels, detect unsafe code,
   link result-image candidates, and create a pending-distillation report.
4. Preserve stable IDs, manual metadata, lineage, promoted recipes, and preview
   decisions. Never delete or overwrite on ambiguity.
5. Apply only after explicit authorization. Record added, changed, conflicting,
   excluded, and unresolved items with checksums.
6. Updating sources does not promote generated candidates or learn from user data.

Do not ingest session state, credentials, temporary downloads, raw browser data,
or private paths into user-facing metadata.
