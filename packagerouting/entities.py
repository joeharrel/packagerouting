from datetime import datetime
from typing import Optional, DefaultDict, Tuple, Any
from enum import Enum, auto
from collections import defaultdict
from dataclasses import dataclass


class Constraint(Enum):
    WRONG_ADDRESS = auto()
    DELIVER_WITH = auto()
    DELAYED = auto()
    TRUCK = auto()

class Status(Enum):
    AT_HUB = auto()
    DELAYED = auto()
    EN_ROUTE = auto()
    DELIVERED = auto()


@dataclass
class Package:
    """Package class models a package to be delivered."""
    def __init__(self, id: str, location_id: str, deadline: datetime, mass: float, notes: Optional[str] = None):
        self.id: str = id
        self.location_id: str = location_id
        self.deadline: datetime = deadline
        self.mass: float = mass
        self.notes: str = notes
        self.status: Tuple[Status, Any] = (Status.AT_HUB, None)
        self.constraints: DefaultDict[(Constraint, Any)] = defaultdict(set)


@dataclass
class Truck:
    """Truck class models a delivery truck and its associated constraints and mileage."""
    def __init__(self, id: str):
        self.id: str = id
        self.capacity: int = 16
        self.mph: int = 18
        self.mileage: int = 0