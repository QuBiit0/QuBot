# API Design Standards

## REST Checklist
- [ ] Nouns (recursos) en plural: `/users`, `/products`.
- [ ] Verbos HTTP correctos: GET, POST, PUT, DELETE.
- [ ] Status codes semánticos: 200, 201, 400, 401, 403, 404, 500.
- [ ] Snake_case para JSON responses.

## OpenAPI (Swagger)
Todo endpoint debe estar documentado en `openapi.yaml` o mediante decoradores de código (FastAPI/NestJS).

## Versioning
Usar URI versioning: `/v1/resources` o Header versioning.
