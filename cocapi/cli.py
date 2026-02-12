"""
cocapi CLI — query the Clash of Clans API from the terminal.

Requires the ``cli`` extra::

    pip install 'cocapi[cli]'
"""

from __future__ import annotations

import json
import os
from typing import Any

try:
    import typer
except ImportError:
    raise ImportError(
        "The cocapi CLI requires typer. Install it with:\n  pip install 'cocapi[cli]'"
    ) from None

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
    location_id: int | None = typer.Option(
        None, "--location-id", help="Filter by location ID."
    ),
    min_members: int | None = typer.Option(
        None, "--min-members", help="Filter by min members."
    ),
    max_members: int | None = typer.Option(
        None, "--max-members", help="Filter by max members."
    ),
    min_clan_points: int | None = typer.Option(
        None, "--min-points", help="Filter by min clan points."
    ),
    min_clan_level: int | None = typer.Option(
        None, "--min-level", help="Filter by min clan level."
    ),
    label_ids: str | None = typer.Option(
        None, "--label-ids", help="Comma-separated label IDs."
    ),
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


@app.command()
def warlog(
    tag: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    limit: int = typer.Option(20, "--limit", "-l", help="Max entries."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get clan war log."""
    _output(
        _get_api(token, email, password).clan_war_log(tag, {"limit": limit}), as_json
    )


@app.command()
def cwl(
    tag: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get clan's current CWL league group."""
    _output(_get_api(token, email, password).clan_leaguegroup(tag), as_json)


@app.command()
def raids(
    tag: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    limit: int = typer.Option(5, "--limit", "-l", help="Max seasons."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get clan capital raid seasons."""
    _output(
        _get_api(token, email, password).clan_capitalraidseasons(tag, {"limit": limit}),
        as_json,
    )


@app.command(name="cwl-war")
def cwl_war(
    war_tag: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get a specific CWL war by war tag."""
    _output(_get_api(token, email, password).warleague(war_tag), as_json)


@app.command(name="location")
def location_info(
    location_id: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get info for a specific location by ID."""
    _output(_get_api(token, email, password).location_id(location_id), as_json)


@app.command(name="rankings")
def rankings(
    location_id: str,
    ranking_type: str = typer.Argument(
        help="Type: clans, players, clans-builder-base, players-builder-base, capitals."
    ),
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get rankings for a location.

    Examples:

        cocapi rankings 32000087 clans

        cocapi rankings 32000087 players --limit 50

        cocapi rankings 32000087 capitals
    """
    api = _get_api(token, email, password)
    params = {"limit": limit}
    methods = {
        "clans": api.location_id_clan_rank,
        "players": api.location_id_player_rank,
        "clans-builder-base": api.location_clans_builder_base,
        "players-builder-base": api.location_players_builder_base,
        "capitals": api.location_capital_rankings,
    }
    method = methods.get(ranking_type)
    if method is None:
        typer.echo(
            f"Error: unknown ranking type '{ranking_type}'. "
            f"Choose from: {', '.join(methods)}",
            err=True,
        )
        raise typer.Exit(1)
    _output(method(location_id, params), as_json)


@app.command(name="league")
def league_info(
    league_id: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Get info for a specific league by ID."""
    _output(_get_api(token, email, password).league_id(league_id), as_json)


@app.command(name="league-seasons")
def league_seasons(
    league_id: str,
    season_id: str | None = typer.Argument(
        None, help="Season ID (e.g. 2025-01) for rankings."
    ),
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List league seasons, or get rankings for a specific season.

    Examples:

        cocapi league-seasons 29000022

        cocapi league-seasons 29000022 2025-01 --limit 100
    """
    api = _get_api(token, email, password)
    if season_id:
        _output(api.league_season_id(league_id, season_id, {"limit": limit}), as_json)
    else:
        _output(api.league_season(league_id, {"limit": limit}), as_json)


@app.command(name="war-leagues")
def war_leagues(
    league_id: str | None = typer.Argument(None, help="War league ID for details."),
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List war leagues, or get a specific war league by ID."""
    api = _get_api(token, email, password)
    if league_id:
        _output(api.warleagues_id(league_id), as_json)
    else:
        _output(api.warleagues(), as_json)


@app.command(name="capital-leagues")
def capital_leagues(
    league_id: str | None = typer.Argument(None, help="Capital league ID for details."),
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List capital leagues, or get a specific capital league by ID."""
    api = _get_api(token, email, password)
    if league_id:
        _output(api.capitalleagues_id(league_id), as_json)
    else:
        _output(api.capitalleagues({"limit": limit}), as_json)


@app.command(name="builder-base-leagues")
def builder_base_leagues(
    league_id: str | None = typer.Argument(
        None, help="Builder base league ID for details."
    ),
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List builder base leagues, or get a specific one by ID."""
    api = _get_api(token, email, password)
    if league_id:
        _output(api.builderbaseleagues_id(league_id), as_json)
    else:
        _output(api.builderbaseleagues({"limit": limit}), as_json)


@app.command(name="league-tiers")
def league_tiers(
    tier_id: str | None = typer.Argument(None, help="League tier ID for details."),
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results."),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List league tiers, or get a specific tier by ID."""
    api = _get_api(token, email, password)
    if tier_id:
        _output(api.leaguetiers_id(tier_id), as_json)
    else:
        _output(api.leaguetiers({"limit": limit}), as_json)


@app.command()
def labels(
    label_type: str = typer.Argument(help="Type: clans or players."),
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """List labels for clans or players.

    Examples:

        cocapi labels clans

        cocapi labels players
    """
    api = _get_api(token, email, password)
    if label_type == "clans":
        _output(api.labels_clans(), as_json)
    elif label_type == "players":
        _output(api.labels_players(), as_json)
    else:
        typer.echo(
            f"Error: unknown label type '{label_type}'. Choose from: clans, players",
            err=True,
        )
        raise typer.Exit(1)


@app.command(name="verify-token")
def verify_token(
    player_tag: str,
    player_token: str,
    token: str | None = typer.Option(None, "--token", "-t", help=_TOKEN_HELP),
    email: str | None = typer.Option(None, "--email", "-e", help=_EMAIL_HELP),
    password: str | None = typer.Option(None, "--password", "-p", help=_PASSWORD_HELP),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON."),
) -> None:
    """Verify a player API token (from in-game settings)."""
    _output(
        _get_api(token, email, password).verify_player_token(player_tag, player_token),
        as_json,
    )
