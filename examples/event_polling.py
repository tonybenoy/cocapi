"""Event polling with async for.

Demonstrates:
- Setting up EventStream to monitor clans, wars, and players
- Using async for to consume events
- Inspecting Change objects for field-level diffs
- Event metadata (member names, war states, attack details)
- State persistence for restart recovery

Requires async mode. Polls the API at configurable intervals and emits
structured Event objects when changes are detected.
"""

import asyncio

from cocapi import ApiConfig, CocApi
from cocapi.events import EventStream, EventType


async def main() -> None:
    # Disable caching so polls always hit the live API
    config = ApiConfig(enable_caching=False)

    async with CocApi("YOUR_API_TOKEN", config=config) as api:
        stream = EventStream(
            api,
            queue_size=1000,  # Bounded queue for backpressure
            persist_path="poll_state.json",  # Save state across restarts
        )

        # Register resources to watch (each with its own poll interval)
        stream.watch_clans(["#2PP", "#2P2G0C0G"], interval=60)
        stream.watch_wars(["#2PP"], interval=30)
        stream.watch_players(
            ["#900PUCPV"],
            interval=120,
            include_fields=frozenset({"trophies", "donations", "warStars"}),
        )

        async with stream:  # Starts watchers, stops on exit
            async for event in stream:
                print(f"[{event.event_type.value}] {event.tag}")

                # Field-level changes
                for change in event.changes:
                    print(f"  {change.field}: {change.old_value} -> {change.new_value}")

                # Event-specific metadata
                if event.event_type == EventType.MEMBER_JOINED:
                    print(f"  Welcome {event.metadata['member_name']}!")

                elif event.event_type == EventType.MEMBER_LEFT:
                    print(f"  Goodbye {event.metadata['member_name']}")

                elif event.event_type == EventType.WAR_STATE_CHANGED:
                    fr = event.metadata["war_state_from"]
                    to = event.metadata["war_state_to"]
                    print(f"  War: {fr} -> {to}")

                elif event.event_type == EventType.WAR_ATTACK_NEW:
                    stars = event.metadata["stars"]
                    attacker = event.metadata["attacker_tag"]
                    print(f"  New attack: {attacker} scored {stars} stars")

                elif event.event_type == EventType.POLL_ERROR:
                    print(f"  Error: {event.metadata['error']}")


asyncio.run(main())
