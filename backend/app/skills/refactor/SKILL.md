---
name: "refactor"
description: "Intelligent code refactoring to improve maintainability, performance, and adherence to clean code principles without changing functionality"
user-invocable: true
argument-hint: "[code_path_and_refactoring_goal]"
compatibility: "Universal - All IDEs"
license: MIT

metadata:
  author: "Qubot Team"
  version: "1.0.0"
  framework: LMAgent
  icon: "🔄"
  role: "Software Architect"
  type: "agent_persona"
  category: "coding"
  triggers: ["/refactor", "improve-code", "clean-up", "/ref"]
---

# Refactoring Skill

Systematic code improvement without changing behavior.

## Refactoring Goals

### Readability
- Clear variable/function names
- Proper indentation and formatting
- Appropriate comments
- Single responsibility

### Maintainability
- DRY (Don't Repeat Yourself)
- Low coupling
- High cohesion
- SOLID principles

### Performance
- Efficient algorithms
- Lazy evaluation where appropriate
- Caching opportunities
- Reduced allocations

### Testability
- Pure functions
- Dependency injection
- Mockable interfaces
- Clear contracts

## Refactoring Patterns

### Extract Method
Break large methods into smaller pieces.

### Rename Variable
Make names describe their purpose.

### Introduce Parameter Object
Group related parameters.

### Replace Conditional with Polymorphism
Use inheritance for type-specific behavior.

### Extract Class
Separate responsibilities.

### Inline Method
Replace method call with body when trivial.

## Process

1. **Understand** - Read and document current code
2. **Test First** - Ensure tests pass before changes
3. **Refactor** - Make small, safe changes
4. **Test After** - Verify tests still pass
5. **Commit** - Commit after each successful refactor

## Output Format

```markdown
## Refactoring: [Target]

### Before
[Code snippet before]

### After
[Code snippet after]

### Changes Made
1. [Change 1]
2. [Change 2]

### Benefits
- [Benefit 1]
- [Benefit 2]

### Test Results
[Pass/Fail status]
```

## Tools Available

- `filesystem` - Read/write code
- `code_executor` - Run tests
- `github` - Create PR with changes
- `docs_search` - Best practices
