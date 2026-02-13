# CLI

cocapi includes an optional command-line interface.

## Installation

```bash
pip install 'cocapi[cli]'
```

## Authentication

### Login with Credentials (Persisted)

Log in once with your developer portal email/password. The API key is saved to `~/.cocapi/keys.json` and reused automatically:

```bash
cocapi login --email you@example.com --password yourpass

# Now all commands work without --token
cocapi clan "#2PP"
```

### Other Methods

```bash
# Explicit token
cocapi clan "#2PP" --token YOUR_TOKEN

# Environment variable
export COCAPI_TOKEN="YOUR_TOKEN"
cocapi clan "#2PP"

# Inline credentials (also persisted)
cocapi clan "#2PP" --email you@example.com --password yourpass
```

## Commands

Add `--json` to any command for raw JSON output. Add `--limit N` where supported.

### Clans

```bash
cocapi clan "#2PP"                                           # Clan info
cocapi members "#2PP" --limit 10                             # Clan members
cocapi war "#2PP"                                            # Current war
cocapi warlog "#2PP"                                         # War log
cocapi cwl "#2PP"                                            # CWL league group
cocapi raids "#2PP"                                          # Capital raid seasons
cocapi search "clash" --limit 5                              # Search clans
cocapi search "war" --min-level 10 --war-frequency always    # Advanced search
```

### Players

```bash
cocapi player "#900PUCPV"                    # Player info
cocapi verify-token "#900PUCPV" "abc123"     # Verify in-game token
```

### Locations & Rankings

```bash
cocapi locations                                    # List all locations
cocapi location 32000006                            # Specific location
cocapi rankings 32000087 clans                      # Clan rankings
cocapi rankings 32000087 players                    # Player rankings
cocapi rankings 32000087 clans-builder-base         # Builder base clan rankings
cocapi rankings 32000087 players-builder-base       # Builder base player rankings
cocapi rankings 32000087 capitals                   # Capital rankings
```

### Leagues

```bash
cocapi leagues                               # List leagues
cocapi league 29000022                       # Specific league
cocapi league-seasons 29000022               # Legend League seasons
cocapi league-seasons 29000022 2025-01       # Season rankings
cocapi war-leagues                           # List war leagues
cocapi capital-leagues                       # List capital leagues
cocapi builder-base-leagues                  # List builder base leagues
cocapi league-tiers                          # List league tiers
```

### Other

```bash
cocapi goldpass                  # Current gold pass season
cocapi labels clans              # Clan labels
cocapi labels players            # Player labels
cocapi cwl-war "#WARTAG"         # Specific CWL war
```
