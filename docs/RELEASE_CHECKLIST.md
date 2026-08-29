# AdaptiveAgent Release Checklist

Use this checklist before publishing a release.

## Quality gate

- [ ] Backend tests pass.
- [ ] Frontend typecheck/lint passes.
- [ ] Ruff and mypy checks pass.
- [ ] Security scan is clean.
- [ ] Docker build completes successfully.
- [ ] `/health` reports the expected service state.
- [ ] `/metrics` is reachable when monitoring is enabled.

## Evaluation gate

- [ ] Versioned evaluation dataset is identified.
- [ ] Baseline and AdaptiveAgent use the same evaluation set.
- [ ] Exact models/configuration are recorded.
- [ ] Retrieval metrics are measured.
- [ ] Generation/evidence metrics are measured where supported.
- [ ] p50/p95 latency and error rate are measured.
- [ ] Results are reproducible from a clean checkout.
- [ ] No estimated or fabricated numbers are published.

## Demo gate

- [ ] Demo uses synthetic/redistributable data.
- [ ] No secrets or private information are visible.
- [ ] Retrieval, evidence, refinement and health are demonstrated.
- [ ] Demo commit hash is recorded.
- [ ] Published video URL is verified.

## Release notes

Include:

- user-visible changes;
- important bug/security fixes;
- compatibility notes;
- evaluation summary;
- known limitations;
- upgrade instructions.

## Versioning

Follow Semantic Versioning. Create the Git tag only after all gates above are green.
