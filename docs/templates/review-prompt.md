# Review Prompt Template

Use this with a second model, second session, or final self-review pass.

```text
Review this diff like a skeptical senior engineer.
Assume the tests may pass while the implementation is still wrong.

Look specifically for:
- logic bugs
- missing edge cases
- overfitting to tests
- architecture drift
- security/privacy problems
- unnecessary complexity

Return:
1. critical issues
2. medium-risk concerns
3. optional improvements
4. anything that should block merge
```
