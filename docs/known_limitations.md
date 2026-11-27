# Known limitations

Stated plainly, so a reviewer does not have to hunt for them.

1. **The deployed models are not the paper's models.** All four are small
   custom CNNs; the PMLR v319 paper describes MobileNetV2 field models.
   See `docs/research_reproducibility.md`.
2. **Class-index ordering is unverified.** The human-readable class names
   come from the legacy app source; no label artifact exists to prove that
   output index i maps to class name i. A wrong ordering would silently
   mislabel predictions. The manifest flags this (`classes_verified=false`)
   and the UI shows a caption.
3. **Uncalibrated probabilities.** Scores are raw softmax outputs. No
   temperature scaling, Platt scaling, or isotonic regression has been
   applied or validated. The UI labels outputs "uncalibrated model score".
4. **No accuracy claims.** No labeled evaluation set or historical
   evaluation record exists for the deployed models; therefore no accuracy,
   ECE, or AUROC number is claimed anywhere in this repository.
5. **No OOD detection or selective prediction.** The low-margin warning is a
   heuristic, not a calibrated abstention mechanism.
6. **Field robustness is unknown.** The models were probably trained on
   curated leaf images; performance under harmattan dust, glare, and soil
   clutter (the paper's motivation) is unmeasured.
7. **Guides are unverified inherited content.** Crop-rotation and vaccination
   tables come from the legacy app without citable sources; the UI marks
   them educational-only.
8. **Optional services require keys.** Q&A (OpenAI) and web search (SerpAPI)
   fail gracefully with configuration messages when keys are absent.
9. **Legacy sources were the credential's last public copy.** The value was
   redacted from `docs/legacy_*` at the branch tip (commit 205a10c) after
   the local rotation was verified; the verbatim pre-redaction originals
   exist only in the local recovery bundle. The value remains reachable in
   public Git history at commit 4d87028; it is verifiably dead, and history
   cleanup is pending owner decision.
10. **The SQLite demo is not production storage.** It exists so the database
    pages work without a server; real deployments should use MySQL with the
    provided schema.
11. **Single-language UI.** The interface is English; no localization exists.
