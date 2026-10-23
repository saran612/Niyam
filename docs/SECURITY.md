# Security Policy & Audit Record (SIH PS 26262)

## 1. Authentication & Role Scoping
- Passwords hashed using modern memory-hard **Argon2id** algorithm (`argon2-cffi`).
- Cryptographic JWT bearer tokens with expiration and strict claims (`sub`, `role`, `region_id`, `institution_id`).
- Server-side regional isolation in repository query layers: `scope_applications_query` and `scope_obligations_query`. A regional officer cannot access data outside their assigned region (returns HTTP 403 or 404).

## 2. Document Ingestion Security
- Magic-byte file validation (`b'%PDF-'`, `b'\xff\xd8\xff'`, `b'\x89PNG\r\n\x1a\n'`). Client-supplied `Content-Type` is never trusted.
- Enforced file size caps (max 10MB per file).
- Path traversal mitigation: filenames sanitized via regex `[^a-zA-Z0-9_.-]`, stored under namespaced UUID prefixes in S3/MinIO.
- Presigned S3 GET URLs generated with short-lived expiration.

## 3. Rate Limiting & Security Headers
- HTTP Security Headers enabled across all responses:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none';`
- CORS allowlist restricted to configured origin domains.
- No plaintext credentials or secrets in logs.

## 4. Static Code Security Audit
- `bandit -r backend/app/` audited with zero critical or high vulnerabilities.
- `pip-audit` ran across dependencies.
