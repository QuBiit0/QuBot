---
name: "security-audit"
description: "Comprehensive security audit for code focusing on OWASP Top 10, authentication flaws, injection attacks, and cryptographic best practices"
user-invocable: true
argument-hint: "[code_path_or_repository]"
compatibility: "Universal - Security Auditing"
license: MIT

metadata:
  author: "Qubot Team"
  version: "1.0.0"
  framework: LMAgent
  icon: "🛡️"
  role: "Security Auditor"
  type: "agent_persona"
  category: "security"
  triggers: ["/audit", "security-audit", "security-review", "/sec"]
---

# Security Audit Skill

Comprehensive security vulnerability assessment.

## Focus Areas

### OWASP Top 10 (2021)
1. Broken Access Control
2. Cryptographic Failures
3. Injection
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Auth Failures
8. Data Integrity Failures
9. Logging Failures
10. SSRF

### Authentication & Authorization
- Password storage (bcrypt, argon2)
- Session management
- Token handling (JWT, OAuth)
- MFA implementation
- Rate limiting

### Data Protection
- Encryption at rest
- Encryption in transit (TLS)
- Key management
- PII handling
- Data masking

### Common Vulnerabilities
- SQL Injection
- XSS (Cross-Site Scripting)
- CSRF (Cross-Site Request Forgery)
- SSRF (Server-Side Request Forgery)
- Path Traversal
- Command Injection

## Audit Checklist

### Authentication
- [ ] Secure password hashing
- [ ] Proper session handling
- [ ] Rate limiting on auth endpoints
- [ ] MFA where appropriate

### Authorization
- [ ] Access control on all endpoints
- [ ] Principle of least privilege
- [ ] IDOR prevention

### Input Validation
- [ ] All user input validated
- [ ] Sanitization for output
- [ ] Parameterized queries

### Cryptography
- [ ] Strong algorithms (AES-256, RSA-2048+)
- [ ] Secure key management
- [ ] No hardcoded secrets

### Error Handling
- [ ] No stack traces in production
- [ ] Generic error messages
- [ ] Logging without sensitive data

## Output Format

```markdown
## Security Audit: [Target]

### Executive Summary
[High-level findings]

### Critical Findings
### High Findings
### Medium Findings
### Low Findings
### Informational

### Remediation Plan
[Prioritized list of fixes]

### Security Score: X/10
```

## Tools Available

- `filesystem` - Read source code
- `code_executor` - Run security scanners
- `docs_search` - Security best practices
- `http_api` - Test API security
