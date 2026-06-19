# Testing

AegisFlow uses `pytest` for unit, API-contract, persistence, and database-integrity testing.

## Run the suite

```bash
pytest -q
```

List every collected test without executing it:

```bash
pytest --collect-only -q
```

## Isolation strategy

The test suite does **not** connect to the PostgreSQL database configured in `.env`.
`tests/conftest.py` replaces the storage-layer session factories with one isolated,
in-memory SQLite database and recreates the schema for the test session.

A small SQLite compatibility function implements PostgreSQL's `char_length` call so
the existing model constraints can be exercised without changing application code.
This provides fast, deterministic local tests while keeping development data safe.
PostgreSQL migrations should still be applied and inspected separately because SQLite
is not a complete substitute for the production database dialect.

## Coverage areas

The suite covers:

- health endpoint contract
- event request validation and normalization
- every supported event type and side
- numeric and asset-length boundaries
- risk approval, rejection, and mismatch branches
- event persistence, retrieval, listing, and clearing
- tenant validation, creation, retrieval, listing, and clearing
- UUID and timestamp response contracts
- event and tenant database constraints
- per-test database isolation

## Known gaps

`tests/test_known_gaps.py` contains strict `xfail` tests for unfinished behavior:

- tenant routes are not yet mounted in `app.main`
- malformed event IDs are not rejected at the route boundary
- duplicate and overlong tenant names are not mapped to client-facing errors
- delete-all route paths and response contracts are not finalized

Strict expected failures are intentional. When one of these behaviors is fixed, pytest
reports an `XPASS` failure so the test must be moved into the normal passing suite.
