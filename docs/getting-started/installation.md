# Installation

## Requirements

- Python 3.10 or higher

## Install with pip

```bash
pip install cocapi
```

### Optional Extras

```bash
# Typed response models (Pydantic)
pip install 'cocapi[pydantic]'

# Command-line interface
pip install 'cocapi[cli]'

# Everything
pip install 'cocapi[pydantic,cli]'
```

## Install with uv

```bash
uv add cocapi

# With extras
uv add 'cocapi[pydantic,cli]'
```

## Verify Installation

```python
import cocapi
print(cocapi.__version__)
```

## Dependencies

cocapi has a single required dependency:

- [httpx](https://www.python-httpx.org/) — HTTP client with async support

Optional dependencies are installed via extras:

| Extra | Package | Purpose |
|---|---|---|
| `pydantic` | pydantic >= 2.0 | Typed response models |
| `cli` | typer >= 0.9 | Command-line interface |
