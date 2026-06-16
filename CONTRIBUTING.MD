# Contributing to Vagrantfile Generator

Thanks for your interest in contributing.

## Setup

See [docs/dev/local-setup.md](./docs/dev/local-setup.md) for a full development environment setup. In short:

```bash
./setup-local-dev.sh
# Press F5 in VS Code, or run backend + frontend manually
```

## Running Tests

```bash
# Backend unit/integration tests
cd backend && source .venv/bin/activate && pytest tests/ -v

# E2E tests (Playwright)
cd frontend && npx playwright test
```

See [docs/dev/testing/e2e-guide.md](./docs/dev/testing/e2e-guide.md) for E2E setup details.

## Making Changes

1. **Fork** the repository
2. **Create a branch** for your change
3. **Keep changes focused** — small, single-purpose PRs are more likely to get reviewed
4. **Add tests** for new features or bug fixes where practical
5. **Open a PR** with a clear description of what changed and why

## Code Style

- **Backend**: Follow PEP 8. Keep service logic in `backend/src/services/`, routes in `backend/src/api/`.
- **Frontend**: The UI uses Alpine.js with Tailwind CSS. Keep modals in `frontend/src/modals/`, views in `frontend/src/views/`.
- No strict linter config exists yet — just be consistent with existing code.

## Ideas & Roadmap

See the in-app footer or [docs/dev/roadmap.md](./docs/dev/roadmap.md) for planned features and improvements.

> **A note on the codebase**: This project was built largely with AI assistance. The code is functional but not always elegant — contributions that improve structure, consistency, or test coverage are especially welcome.

## License

MIT — see [LICENSE](LICENSE) for details. By contributing, you agree that your work will be licensed under the same terms.
