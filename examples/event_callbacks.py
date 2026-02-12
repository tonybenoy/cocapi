"""Event polling with callback decorators.

Demonstrates:
- @stream.on(EventType) decorator for event-driven style
- Wildcard callback that fires on every event
- Programmatic callback registration with add_callback()
- stream.run() for blocking callback dispatch

This is an alternative to the async for pattern in event_polling.py.
Both styles can be mixed.
"""

import asyncio

from cocapi import ApiConfig, CocApi
from cocapi.events import EventStream, EventType, Event


async def main() -> None:
    config = ApiConfig(enable_caching=False)

    async with CocApi("YOUR_API_TOKEN", config=config) as api:
        stream = EventStream(api)
        stream.watch_clans(["#2PP"], interval=60)
        stream.watch_wars(["#2PP"], interval=30)
        stream.watch_players(["#900PUCPV"], interval=120)
        stream.watch_maintenance(interval=30)

        # --- Typed callbacks with decorators ---

        @stream.on(EventType.MEMBER_JOINED)
        async def on_join(event: Event) -> None:
            name = event.metadata["member_name"]
            print(f"[JOIN] {name} joined {event.tag}")

        @stream.on(EventType.MEMBER_LEFT)
        async def on_leave(event: Event) -> None:
            name = event.metadata["member_name"]
            print(f"[LEAVE] {name} left {event.tag}")

        @stream.on(EventType.MEMBER_ROLE_CHANGED)
        async def on_role(event: Event) -> None:
            name = event.metadata["member_name"]
            old_r = event.metadata["old_role"]
            new_r = event.metadata["new_role"]
            print(f"[ROLE] {name}: {old_r} -> {new_r}")

        @stream.on(EventType.WAR_STATE_CHANGED)
        async def on_war(event: Event) -> None:
            fr = event.metadata["war_state_from"]
            to = event.metadata["war_state_to"]
            print(f"[WAR] {event.tag}: {fr} -> {to}")

        @stream.on(EventType.WAR_ATTACK_NEW)
        async def on_attack(event: Event) -> None:
            stars = event.metadata["stars"]
            attacker = event.metadata["attacker_tag"]
            defender = event.metadata["defender_tag"]
            print(f"[ATTACK] {attacker} -> {defender}: {stars} stars")

        @stream.on(EventType.TROOP_UPGRADED)
        async def on_troop(event: Event) -> None:
            name = event.metadata["name"]
            print(f"[TROOP] {name}: lv{event.metadata['old_level']} -> lv{event.metadata['new_level']}")

        @stream.on(EventType.HERO_UPGRADED)
        async def on_hero(event: Event) -> None:
            name = event.metadata["name"]
            print(f"[HERO] {name}: lv{event.metadata['old_level']} -> lv{event.metadata['new_level']}")

        @stream.on(EventType.TOWNHALL_UPGRADED)
        async def on_th(event: Event) -> None:
            print(f"[TH] {event.tag}: TH{event.metadata['old_value']} -> TH{event.metadata['new_value']}")

        @stream.on(EventType.MAINTENANCE_START)
        async def on_maint_start(event: Event) -> None:
            print("[MAINT] API is under maintenance!")

        @stream.on(EventType.MAINTENANCE_END)
        async def on_maint_end(event: Event) -> None:
            print(f"[MAINT] Back online after {event.metadata['duration_seconds']}s")

        # --- Wildcard: fires on every event ---

        @stream.on(None)
        async def on_any(event: Event) -> None:
            if event.event_type == EventType.POLL_ERROR:
                print(f"[ERROR] {event.tag}: {event.metadata.get('error')}")

        # --- Programmatic registration ---

        async def on_clan_update(event: Event) -> None:
            fields = [c.field for c in event.changes]
            print(f"[CLAN] {event.tag} changed: {fields}")

        stream.add_callback(on_clan_update, EventType.CLAN_UPDATED)

        # Blocks until stream.stop() is called
        await stream.run()


asyncio.run(main())
