# AdaptiveAgent Demo Runbook

The public demo should demonstrate the system as an engineering product, not as a slide deck.

## 60–90 second flow

1. **Open the application** and show the clean chat interface.
2. **Upload a small knowledge base** using a safe, non-sensitive document.
3. Ask a question that requires retrieval from that document.
4. Show the streamed answer and supporting evidence.
5. Show confidence/risk information returned by the pipeline.
6. Trigger a query that requires refinement and show the recovery path.
7. Open the health/observability surface and show service status.
8. End on the repository README with the architecture and benchmark links.

## Recording rules

- Use only synthetic or redistributable documents.
- Do not expose API keys, local paths, private data, or personal information.
- Keep the browser zoom and terminal font readable.
- Record at 1080p or better.
- Avoid claiming latency or quality numbers unless they are measured and linked to a benchmark result.

## Evidence to capture

The demo should visibly establish:

- retrieval is actually occurring;
- answers are grounded in retrieved evidence;
- the refinement loop can recover from weak evidence;
- the service health endpoint works;
- the project can be reproduced from the documented setup.

## Suggested demo questions

Use questions whose answers are present in the synthetic document set. Prefer questions that make the retrieved evidence easy to inspect.

## Before publishing

- [ ] Run the test suite.
- [ ] Run the benchmark procedure.
- [ ] Verify no secrets are visible.
- [ ] Verify README links.
- [ ] Record the commit hash used for the demo.
- [ ] Add the final video URL to the README only after the video is actually published.
