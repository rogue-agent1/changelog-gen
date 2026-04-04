# changelog_gen

Changelog generator from git history with conventional commit parsing.

## Usage

```bash
python3 changelog_gen.py generate --repo . -v "2.0.0"
python3 changelog_gen.py generate --since v1.0.0 --until v2.0.0
python3 changelog_gen.py stats --repo .
python3 changelog_gen.py tags --repo .
```

## Features

- Conventional commit parsing (feat, fix, docs, etc.)
- Breaking change detection
- Grouped markdown output with emoji
- Tag-to-tag changelog generation
- Commit statistics
- Scope tracking
- Zero dependencies (uses git CLI)
