# Tests

Tests are grouped by the kind of guarantee they provide.

## Layout

```text
tests/
├── unit/          # Fast tests for one module or function
├── integration/   # Tests that cross module boundaries with mocked externals
├── contracts/     # Tests for provider and API contracts
└── e2e/           # End-to-end tests; added only when needed
```

## Running tests

Run all tests:

```bash
python -m unittest discover -s tests -v
```

Run integration tests:

```bash
python -m unittest discover -s tests/integration -v
```

## Conventions

- Keep unit tests fast and free of network access.
- Use mocks or fakes for external services in integration tests.
- Name test files after the behavior they cover.
- Do not require real credentials, clusters, or provider accounts to run the
  default test suite.
