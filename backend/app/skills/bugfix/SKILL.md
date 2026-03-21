---
name: "bugfix"
description: "Systematic debugging and bug fixing methodology with root cause analysis and regression prevention"
user-invocable: true
argument-hint: "[bug_description_or_reproduction_steps]"
compatibility: "Universal - All IDEs"
license: MIT

metadata:
  author: "Qubot Team"
  version: "1.0.0"
  framework: LMAgent
  icon: "🐛"
  role: "Debugging Engineer"
  type: "agent_persona"
  category: "coding"
  triggers: ["/debug", "fix-bug", "debug", "/bf"]
---

# Bug Fix Skill

Systematic approach to debugging and fixing bugs.

## Methodology

### 1. Reproduce
- Create minimal reproduction case
- Verify bug exists in current environment
- Document exact steps to reproduce

### 2. Investigate
- Read relevant source code
- Check error messages and stack traces
- Review recent changes (git blame)
- Add debug logging if needed

### 3. Hypothesize
- Form theory about root cause
- Identify the exact failure point
- Consider edge cases

### 4. Fix
- Implement minimal fix
- Ensure no side effects
- Follow existing code patterns

### 5. Verify
- Run reproduction case - should pass now
- Run existing tests
- Add regression test

## Debug Checklist

- [ ] Reproduced bug with minimal case
- [ ] Identified root cause
- [ ] Implemented fix
- [ ] Tests pass
- [ ] Added regression test
- [ ] Updated documentation if needed

## Output Format

```markdown
## Bug Fix: [Title]

### Reproduction
[Steps to reproduce the bug]

### Root Cause
[What caused the bug]

### Fix Applied
[Description of the fix]

### Files Changed
- [file1.py]
- [file2.js]

### Testing
- [ ] Reproduction case passes
- [ ] All existing tests pass
- [ ] New regression test added
```

## Tools Available

- `filesystem` - Read/modify source files
- `code_executor` - Run tests, linters
- `github` - Check history, create PR
- `database_query` - Debug data issues
- `system_shell` - Run commands
