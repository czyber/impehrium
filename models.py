import datetime
import uuid

from pydantic import UUID5, UUID4
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.db import Base


def uuid4_str() -> str:
    return str(uuid.uuid4())


class Server(Base):
    __tablename__ = "servers"

    id: Mapped[str | None] = mapped_column(primary_key=True, default=uuid4_str)
    name: Mapped[str]
    started_at: Mapped[datetime.datetime | None] = mapped_column(default=datetime.datetime.now)
    ended_at: Mapped[datetime.datetime | None] = None
    players: Mapped[list["Player"]] = relationship('Player', back_populates='server')


class Player(Base):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    server_id: Mapped[str] = mapped_column(ForeignKey("servers.id"))
    username: Mapped[str]
    password_hash: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    server: Mapped[Server] = relationship(back_populates="players")
    planets: Mapped[list["Planet"]] = relationship(
        back_populates="owner_player",
        primaryjoin="""and_(
            Player.id == foreign(Planet.owner_id),
            Planet.owner_type == 'player',
            )""",
        viewonly=True,
    )


class NPC(Base):
    __tablename__ = "npcs"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    server_id: Mapped[str] = mapped_column(ForeignKey("servers.id"))
    name: Mapped[str]
    ai_type: Mapped[str | None]
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

class Planet(Base):
    __tablename__ = "planets"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    server_id: Mapped[str] = mapped_column(ForeignKey("servers.id"))
    owner_type: Mapped[str | None]
    owner_id: Mapped[str | None]

    name: Mapped[str]
    coord_x: Mapped[int]
    coord_y: Mapped[int]
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    resources: Mapped["PlanetResources"] = relationship(back_populates="planet", uselist=False)
    buildings: Mapped[list["PlanetBuilding"]] = relationship(back_populates="planet")

    owner_player: Mapped[Player | None] = relationship(
    Player,
    primaryjoin="""and_(
        foreign(Planet.owner_id) == Player.id,
        Planet.owner_type == 'player',
    )""",
    viewonly=True,
)

    __table_args__ = (
        CheckConstraint(
            "(owner_type IS NULL AND owner_id IS NULL) OR (owner_type IS NOT NULL AND owner_id IS NOT NULL)",
            name="planet_owner_check"
        ),
    )

class PlanetResources(Base):
    __tablename__ = "planet_resources"

    planet_id: Mapped[str] = mapped_column(ForeignKey("planets.id"), primary_key=True)
    metal: Mapped[float] = mapped_column(default=0)
    energy: Mapped[float] = mapped_column(default=0)
    last_updated: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    planet: Mapped[Planet] = relationship(back_populates="resources")


class BuildingDefinition(Base):
    __tablename__ = "building_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    building_type: Mapped[str]
    level: Mapped[int] = mapped_column(default=0)
    metal_cost: Mapped[int] = mapped_column(default=0)
    energy_cost: Mapped[int] = mapped_column(default=0)
    build_time_seconds: Mapped[int] = mapped_column(default=0)
    metal_production_per_minute: Mapped[int] = mapped_column(default=0)
    energy_production_per_minute: Mapped[int] = mapped_column(default=0)


class PlanetBuilding(Base):
    __tablename__ = "planet_buildings"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    planet_id: Mapped[str] = mapped_column(ForeignKey("planets.id"))
    building_type: Mapped[str]
    level: Mapped[int] = mapped_column(default=0)

    planet: Mapped[Planet] = relationship(back_populates="buildings")


class PlanetBuildingQueue(Base):
    __tablename__ = "planet_building_queue"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    planet_id: Mapped[str] = mapped_column(ForeignKey("planets.id"))
    building_type: Mapped[str]
    target_level: Mapped[int] = mapped_column(default=0)
    complete_at: Mapped[datetime.datetime]


class PlayerFleet(Base):
    __tablename__ = "player_fleets"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4_str)
    owner_id: Mapped[str] = mapped_column(ForeignKey("players.id"))
    server_id: Mapped[str] = mapped_column(ForeignKey("servers.id"))
    origin_planet_id: Mapped[str] = mapped_column(ForeignKey("planets.id"))
    target_planet_id: Mapped[str] = mapped_column(ForeignKey("planets.id"))
    depart_at: Mapped[datetime.datetime]
    arrive_at: Mapped[datetime.datetime]

    ships: Mapped[list["FleetShip"]] = relationship(back_populates="fleet")


class FleetShip(Base):
    __tablename__ = "fleet_ships"

    fleet_id: Mapped[str] = mapped_column(ForeignKey("player_fleets.id"), primary_key=True)
    ship_type: Mapped[str] = mapped_column(primary_key=True)
    quantity: Mapped[int] = mapped_column(default=0)

    fleet: Mapped[PlayerFleet] = relationship(back_populates="ships")
