import asyncio

from sqlalchemy.orm import Session
from models import (
    Server, Player, NPC, Planet, PlanetResources, BuildingDefinition,
    PlanetBuilding
)
import datetime
import random

from utils.db import sessionmanager, get_db


async def seed_database():
    async with sessionmanager.session() as session:
        now = datetime.datetime.utcnow()

        # 1. Create Server
        server = Server(name="Test Server", started_at=now)
        session.add(server)
        await session.flush()

        # 2. Create Building Definitions
        building_defs = []
        for building_type in ["mine", "power_plant", "shipyard"]:
            for level in range(1, 4):
                defn = BuildingDefinition(
                    building_type=building_type,
                    level=level,
                    metal_cost=100 * level,
                    energy_cost=50 * level,
                    build_time_seconds=level * 60,
                )
                building_defs.append(defn)
        session.add_all(building_defs)
        await session.flush()

        # 3. Add Players
        players = []
        for i in range(2):
            player = Player(
                server=server,
                username=f"player{i+1}",
                password_hash="dummyhash",  # in production, hash it!
            )
            players.append(player)
        session.add_all(players)
        await session.flush()

        # 4. Create Planets (1 for each player)
        planets = []
        for i, player in enumerate(players):
            planet = Planet(
                server_id=server.id,
                owner_type="player",
                owner_id=player.id,
                name=f"Planet {chr(65+i)}",
                coord_x=random.randint(0, 20),
                coord_y=random.randint(0, 20),
                created_at=now,
            )
            planets.append(planet)
        session.add_all(planets)
        await session.flush()

        # 5. Add Resources & Buildings to Planets
        for planet in planets:
            session.add(PlanetResources(
                planet=planet,
                metal=500,
                energy=300
            ))
            session.add_all([
                PlanetBuilding(
                    planet=planet,
                    building_type="mine",
                    level=1
                ),
                PlanetBuilding(
                    planet=planet,
                    building_type="power_plant",
                    level=1
                )
            ])

        await session.commit()
        print("✅ Seed data added.")

if __name__ == "__main__":
    asyncio.run(seed_database())

