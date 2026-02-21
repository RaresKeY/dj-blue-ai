# Quality & Testing

## Test Layers
- **Unit:** `<path + purpose>`
- **Integration:** `<path + purpose>`
- **E2E/Gameplay/API:** `<path + purpose>`

## Quality Gates
- **Linting:** `<command>`
- **Type checks:** `<command>`
- **Tests:** `<command>`
- **Coverage threshold:** `<target>`

## Critical Assertions
- <critical behavior that must never regress>
- <critical behavior that must never regress>

## Release Readiness Checklist
- [ ] All tests green in CI
- [ ] Backward compatibility verified
- [ ] Key user flows smoke-tested
- [ ] Rollback plan documented
