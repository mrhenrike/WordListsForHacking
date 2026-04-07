# Contributing

Thank you for your interest in improving **WordListsForHacking**. This guide
explains how to contribute effectively while preserving attribution and quality.

## Ground Rules

- Use this project **only** for authorized security research, education, and
  contracted penetration testing.
- Do not submit content intended to facilitate unauthorized access.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md) in all interactions.
- Never include real PII, real credentials, or identifiable company data in
  wordlists, patterns, or code.

## How to Contribute

1. **Open an issue first** for substantial changes (new features, large
   refactors, new modules).
2. **Fork** the repository and create a **feature branch** from `main`.
3. **Keep commits focused** — one logical change per commit.
4. **Test locally** before opening a pull request.
5. **Open a pull request** with a clear description.

## Code Style

- **Type hints** on all function signatures.
- **Docstrings** in Google style for every class and public function.
- **Logging** via `logging` module — never `print()` in library code.
- **No hardcoded sensitive data** — use `.env` and configuration files.
- **No unnecessary imports** — keep modules lean.
- Follow existing module structure in `wfh_modules/`.

## Adding a New Module

1. Create `wfh_modules/your_module.py` following the existing pattern.
2. Add the CLI subcommand in `wfh.py` → `build_parser()`.
3. Add the handler function `cmd_your_module()` in `wfh.py`.
4. Add the interactive menu entry if appropriate.
5. Update `requirements.txt` if new dependencies are needed.
6. Update the README with documentation and examples.

## Wordlist Contributions

- **No real PII** — no real names tied to real companies.
- **No real credentials** — no actual passwords from breaches.
- **Structural patterns only** — abstract shapes, not raw data.
- Deduplicate entries before submitting.
- Follow existing file naming conventions (`*.lst`).

## Pull Request Template

When opening a PR, include:

```
## What changed
<Brief description>

## Why
<Motivation / issue reference>

## How to test
<Steps to verify the change>

## Checklist
- [ ] Type hints on all new functions
- [ ] Docstrings on all public functions
- [ ] No hardcoded sensitive data
- [ ] Tested locally
- [ ] README updated (if applicable)
```

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
`MAJOR.MINOR.PATCH` (e.g., `1.7.0`).

- **MAJOR**: Breaking changes to CLI interface or module API.
- **MINOR**: New features, new modules, new patterns.
- **PATCH**: Bug fixes, documentation updates, minor improvements.

## Attribution

All contributions are attributed to **André Henrique**
([@mrhenrike](https://github.com/mrhenrike)) as the project maintainer.
Contributors are acknowledged in release notes and the GitHub contributors list.

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](LICENSE).
