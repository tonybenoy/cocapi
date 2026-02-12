"""
cocapi CLI — query the Clash of Clans API from the terminal.

Requires the ``cli`` extra::

    pip install 'cocapi[cli]'
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

try:
    import typer
except ImportError:
    print(
        "The cocapi CLI requires typer. Install it with:\n  pip install 'cocapi[cli]'"
    )
    sys.exit(1)

from cocapi import ApiConfig, CocApi
from cocapi.key_manager import _DEFAULT_KEY_STORAGE_PATH, _load_cached_keys

app = typer.Typer(
    name="cocapi",
    help="Query the Clash of Clans API from the terminal.",
    no_args_is_help=True,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TOKEN_HELP = "API token (or set COCAPI_TOKEN env var)."
_EMAIL_HELP = "Developer portal email (alternative to --token)."
_PASSWORD_HELP = "Developer portal password (used with --email)."


def _get_api(
    token: str | None = None,
    email: str | None = None,
    password: str | None = None,
) -> CocApi:
    """Resolve an API instance from token, credentials, env var, or persisted key."""
    # 1. Explicit token
    resolved = token or os.environ.get("COCAPI_TOKEN")
    if resolved:
        return CocApi(resolved)

    # 2. Email/password credentials
    email = email or os.environ.get("COCAPI_EMAIL")
    password = password or os.environ.get("COCAPI_PASSWORD")
    if email and password:
        config = ApiConfig(persist_keys=True)
        return CocApi.from_credentials(email, password, config=config)

    # 3. Persisted key from a previous login
    cached = _load_cached_keys(_DEFAULT_KEY_STORAGE_PATH, "cocapi_auto")
    if cached:
        tokens, _ip = cached
        try:
            return CocApi(tokens[0])
        except ValueError:
            pass  # Token expired or IP changed — fall through

    typer.echo(
        "Error: no credentials found. Use one of:\n"
        "  cocapi login --email <EMAIL> --password <PASS>\n"
        "  cocapi <command> --token <TOKEN>\n"
        "  export COCAPI_TOKEN=<TOKEN>",
        err=True,
    )
    raise typer.Exit(1)


def _output(data: Any, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(data, indent=2, default=str))
        return

    if isinstance(data, dict) and data.get("result") == "error":
        typer.echo(f"Error: {data.get('message', 'Unknown error')}", err=True)
        raise typer.Exit(1)

    if isinstance(data, dict) and "items" in data:
        _print_items(data["items"])
    elif isinstance(data, dict):
        _print_dict(data)
    else:
        typer.echo(json.dumps(data, indent=2, default=str))


def _print_dict(d: dict[str, Any], indent: int = 0) -> None:
    prefix = "  " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            typer.echo(f"{prefix}{k}:")
            _print_dict(v, indent + 1)
        elif isinstance(v, list):
            typer.echo(f"{prefix}{k}: [{len(v)} items]")
        else:
            typer.echo(f"{prefix}{k}: {v}")


def _print_items(items: list[dict[str, Any]]) -> None:
    for item in items:
        parts: list[str] = []
        for key in ("tag", "name", "id", "rank", "trophies", "clanLevel", "members"):
            if key in item:
                parts.append(f"{key}={item[key]}")
        typer.echo("  ".join(parts) if parts else json.dumps(item, default=str))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def login(
    email: str = typer.Option(..., "--email", "-e", help="Developer portal email."),
    password: str = typer.Option(
        ..., "--password", "-p", help="Developer portal password."
    ),
) -> None:
    """Log in with developer portal credentials and persist the API key.

    After logging in, all other commands will use the persisted key
    automatically — no --token needed.
    """
    config = ApiConfig(persist_keys=True)
    try:
        api = CocApi.from_credentials(email, password, config=config)
    except Exception as e:
        typer.echo(f"Login failed: {e}", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"Logged in. Token persisted to {_DEFAULT_KEY_STORAGE_PATH}")
    typer.echo(f"Token: {api.token[:20]}...")


@app.command()
def clan(
    tag: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get clan information."""
    _output(_get_api(token, email, password).clan_tag(tag), as_json)


@app.command()
def player(
    tag: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get player information."""
    _output(_get_api(token, email, password).players(tag), as_json)


@app.command()
def members(
    tag: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    limit: int = typer.Option(50, "--limit", "-l", help="Max members to show."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List clan members."""
    _output(
        _get_api(token, email, password).clan_members(tag, {"limit": limit}), as_json
    )


@app.command()
def war(
    tag: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get current clan war."""
    _output(_get_api(token, email, password).clan_current_war(tag), as_json)


@app.command()
def search(
    name: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    limit: int = typer.Option(10, "--limit", "-l", help="Max results."),
    war_frequency: str | None = typer.Option(
        None, "--war-frequency", help="Filter: always, moreThanOncePerWeek, etc."
    ),
    location_id: int | None = typer.Option(None, "--location-id", help="Filter by location ID."),
    min_members: int | None = typer.Option(None, "--min-members", help="Filter by min members."),
    max_members: int | None = typer.Option(None, "--max-members", help="Filter by max members."),
    min_clan_points: int | None = typer.Option(None, "--min-points", help="Filter by min clan points."),
    min_clan_level: int | None = typer.Option(None, "--min-level", help="Filter by min clan level."),
    label_ids: str | None = typer.Option(None, "--label-ids", help="Comma-separated label IDs."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Search clans by name."""
    _output(
        _get_api(token, email, password).clan(
            name,
            limit,
            war_frequency=war_frequency,
            location_id=location_id,
            min_members=min_members,
            max_members=max_members,
            min_clan_points=min_clan_points,
            min_clan_level=min_clan_level,
            label_ids=label_ids,
        ),
        as_json,
    )


@app.command()
def leagues(
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List leagues."""
    _output(_get_api(token, email, password).league(), as_json)


@app.command()
def goldpass(
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get current gold pass season."""
    _output(_get_api(token, email, password).goldpass(), as_json)


@app.command()
def locations(
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List locations."""
    _output(_get_api(token, email, password).location({"limit": limit}), as_json)
