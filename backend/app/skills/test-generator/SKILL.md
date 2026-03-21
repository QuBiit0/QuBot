---
name: "test-generator"
description: "Generates comprehensive unit tests, integration tests, and property-based tests following testing best practices"
user-invocable: true
argument-hint: "[source_file_or_module]"
compatibility: "Universal - All Testing Frameworks"
license: MIT

metadata:
  author: "Qubot Team"
  version: "1.0.0"
  framework: LMAgent
  icon: "🧪"
  role: "QA Engineer"
  type: "agent_persona"
  category: "coding"
  triggers: ["/test", "generate-tests", "add-tests", "/tg"]
---

# Test Generator Skill

Automated generation of comprehensive test suites.

## Testing Pyramid

```
        /\
       /  \
      / E2E\      <- Few, slow, expensive
     /-------\
    /Integrat.\  <- Some, medium speed
   /-----------\
  /   Unit      \ <- Many, fast, cheap
 /---------------\
```

## Test Types

### Unit Tests
- Test single functions/methods
- Mock external dependencies
- Fast execution
- High coverage target

### Integration Tests
- Test component interactions
- Real database (or test db)
- Slower than unit tests
- Critical paths

### E2E Tests
- Test complete user flows
- Use real browser/app
- Slowest, most expensive
- Smoke tests for critical paths

## Test Structure

### Arrange-Act-Assert (AAA)
```python
def test_function():
    # Arrange
    input_data = {...}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected
```

### Given-When-Then (GWT)
```gherkin
Given a user is logged in
When they submit the form
Then they should see success message
```

## Test Coverage Goals

- [ ] Happy path coverage
- [ ] Error path coverage
- [ ] Edge cases
- [ ] Boundary conditions
- [ ] Null/undefined inputs
- [ ] Empty collections
- [ ] Concurrent access

## Output Format

```markdown
## Test Suite: [Module]

### Coverage Report
- Statements: X%
- Branches: X%
- Functions: X%
- Lines: X%

### Tests Added
1. `test_function_happy_path`
2. `test_function_error_case`
3. `test_function_edge_case`

### Edge Cases Covered
- [Case 1]
- [Case 2]
```

## Tools Available

- `filesystem` - Read source, write tests
- `code_executor` - Run test suite
- `docs_search` - Framework docs
- `github` - Create PR with tests
