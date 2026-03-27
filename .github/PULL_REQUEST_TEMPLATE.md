## Description
<!-- What does this PR do? Why? -->

## Type of Change
- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Pipeline/CI change
- [ ] Model architecture change
- [ ] Config change

## Safety Impact
<!-- Does this change affect safety-critical behavior? -->
- [ ] No safety impact
- [ ] Affects detection logic → requires eval report comparison
- [ ] Affects promotion policy → requires senior review
- [ ] Affects dangerous class handling → requires safety sign-off

## Checklist
- [ ] `make lint` passes locally
- [ ] `make test` passes locally
- [ ] `pre-commit run --all-files` passes
- [ ] If model change: eval report attached or linked
- [ ] If config change: configs/README updated
- [ ] If new dependency: requirements.txt pinned version added
- [ ] No `.pt` files accidentally staged

## Eval Report (if applicable)
<!-- Paste or link outputs/reports/eval_report.md here -->

## Related Issues
Closes #
