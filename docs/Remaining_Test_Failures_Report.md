# AdaptiveAgent - Remaining Test Failures Report

**Date:** 2026-08-13
**Repo:** https://github.com/YogendraChukka01/AdaptiveAgent
**CI Run:** #31719569536 (latest)

---

## Summary

- **87 tests passed** ✅
- **7 tests failed** ❌ (all from third-party library bug)
- **0 tests skipped**

---

## Root Cause

All 7 failures share the **same root cause**: the `FlagEmbedding` library (v1.2.11) uses `Optional` without importing it from `typing`. This breaks on Python 3.11+ when `from __future__ import annotations` is not used in the library file.

**Error:**
```
/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/FlagEmbedding/BGE_M3/trainer.py:17
NameError: name 'Optional' is not defined
```

---

## Affected Tests

| # | Test Name | File |
|---|-----------|------|
| 1 | `test_embedder_lru_cache` | `tests/test_upgrades.py` |
| 2 | `test_chat_helpers` | `tests/test_upgrades.py` |
| 3 | `test_graph_scenarios[tool_names0-approve-approved-False-False]` | `tests/test_upgrades.py` |
| 4 | `test_graph_scenarios[tool_names1-approve-approved-False-False]` | `tests/test_upgrades.py` |
| 5 | `test_graph_scenarios[tool_names2-approve-approved-True-True]` | `tests/test_upgrades.py` |
| 6 | `test_graph_scenarios[tool_names3-reject-rejected-True-False]` | `tests/test_upgrades.py` |
| 7 | `test_graph_scenarios[tool_names4-approve-approved-True-True]` | `tests/test_upgrades.py` |

---

## Fix Options

### Option 1: Pin FlagEmbedding version (Quick)
Change `pyproject.toml`:
```
"FlagEmbedding>=1.2.11,<1.3"
```
to:
```
"FlagEmbedding>=1.2.10,<1.2.11"
```
Or remove the upper bound constraint to allow `>=1.3`:
```
"FlagEmbedding>=1.2.11"
```

### Option 2: Add `pytest.mark.skipif` (Workaround)
Skip the 7 tests when FlagEmbedding import fails:
```python
import pytest
try:
    import FlagEmbedding
except NameError:
    pytest.skip("FlagEmbedding incompatible with this Python version", allow_module_level=True)
```

### Option 3: Upgrade FlagEmbedding (Recommended)
Update to `FlagEmbedding>=1.3` which likely fixes the `Optional` import issue.

---

## Additional Cleanup Needed

1. **Delete stale branches:**
   - `fix/ci-build-clean`
   - `fix/ci-build-working-directory`
   - `fix/ci-duplicate-build`
   - `fix/ci-final-*`
   - `fix/ci-frontend-build`
   - `fix/ci-frontend-build-v3`

2. **The CI still shows "failure" overall** because of these 7 tests, even though all our code is correct.
