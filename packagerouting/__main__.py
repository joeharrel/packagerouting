import csv
import os
import re
from datetime import date, time, datetime
from collections import defaultdict
from typing import Dict

from packagerouting.datastructures import HashTable, Graph
from packagerouting.entities import Constraint, Package


START_OF_DAY = datetime.combine(date.today(), time(8,0,0))
END_OF_DAY = datetime.combine(date.today(), time(23,59,59))

distance_graph: Graph = None
package_table: HashTable = None
location_dict: Dict = None
dependencies: Dict = None


def load_data():
    """Loads data from csv files."""
    global distance_graph, package_table, location_dict, dependencies
    distance_graph, package_table, location_dict, dependencies = Graph(), HashTable(), {}, defaultdict(set)
    basepath = os.path.dirname(__file__)
    if basepath:
        basepath += "/"

    with open(f"{basepath}data/distances.csv") as file:
        reader = csv.reader(file, delimiter=',', quotechar='"')
        columns = next(reader)
        for line in reader:
            for i in range(1, len(line)):
                distance_graph.add_edge(line[0], columns[i], float(line[i]))

    with open(f"{basepath}data/packages.csv") as file:
        reader = csv.reader(file, delimiter=',', quotechar='"')
        columns = next(reader)
        for line in reader:
            pkg = parse_package(*line)
            package_table[line[0]] = pkg
        for id in dependencies:
            for dep in dependencies[id]:
                package_table[id].constraints[Constraint.DELIVER_WITH].add(dep)

    with open(f"{basepath}data/locations.csv") as file:
        reader = csv.DictReader(file, delimiter=',', quotechar='"')
        for line in reader:
            id = line.pop("Location ID")
            location_dict[id] = line


def parse_time(time: str, military: bool = False):
    """Parse a time string into a datetime object with today's date."""
    TODAY_STRING = date.today().strftime("%Y-%m-%d")
    STANDARD = "%Y-%m-%d %I:%M %p"
    MILITARY = "%Y-%m-%d %H:%M"
    if time == "EOD":
        return END_OF_DAY
    else:
        return datetime.strptime(f"{TODAY_STRING} {time}", MILITARY if military else STANDARD)


def parse_package(id: str, location: str, time: str, mass: str, note: str):
    """Parse a package string to create a Package object."""
    pkg = Package(id, location, parse_time(time), float(mass), note or None)
    if not note:
        return pkg
    matches = re.findall(r"(\d+:\d+\s*[a|p]m)|(?(1)|(\d+))", note)
    if note[0] == "W":
        # Wrong address listed, (effectively delayed until 10:20 am then update location to id 20)
        pkg.constraints[Constraint.DELAYED] = parse_time("10:20 am")
        pkg.constraints[Constraint.WRONG_ADDRESS] = "20"
        pkg.location_id = '20'
    elif note[0] == "D":
        # Delayed on flight---will not arrive to depot until <time>
        pkg.constraints[Constraint.DELAYED] = parse_time(matches[0][0])
    elif note[0] == "M":
        # Must be delivered with <id, id>
        dependencies[pkg.id].add(pkg.id)
        for m in matches:
            dependencies[pkg.id].update(dependencies[m[1]], [m[1]])
        for id in dependencies[pkg.id]:
            dependencies[id] = dependencies[pkg.id]
    elif note[0] == "C":
        # Can only be on truck <id>
        pkg.constraints[Constraint.TRUCK] = matches[0][1]
    return pkg


def main():
    load_data()


if __name__ == "__main__":
    main()
