import csv
import os
import re
from datetime import date, time, datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List

from packagerouting.datastructures import HashTable, Graph
from packagerouting.entities import Package, Truck, Constraint, Status


START_OF_DAY = datetime.combine(date.today(), time(8,0,0))
END_OF_DAY = datetime.combine(date.today(), time(23,59,59))

distance_graph: Graph = None
package_table: HashTable = None
location_dict: Dict = None
dependencies: Dict = None
routes: List[Dict] = None
trucks: List[Truck] = None


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


def build_route(deliverable: HashTable, dist_graph: Graph, start: datetime, truck: Truck, skew: float = 0):
    """
    Constructs a route utilizing shortest path and selection variables to adjust selection criteria, 
    O(n²) time and O(k) space where n is the number of deliverable packages and k is the length of the route.
    """
    dummy = Package("dummy", "1", END_OF_DAY, 0)    # Dummy package to serve as starting location
    route = {"start": start, "ordered": deque([{"package": dummy}]), "contains": {}, "dependents": {}, "truck": truck}
    while len(route["ordered"]) + len(route["dependents"]) < truck.capacity + 1 and len(deliverable) > 0:
        section = route["ordered"]
        min_dist = float('inf')
        min_id = None
        # Really just a big min function
        for id in deliverable:
            pack = deliverable[id]
            if pack.constraints:
                if Constraint.DELAYED in pack.constraints:
                    if route["start"] < pack.constraints[Constraint.DELAYED]:
                        continue
                if Constraint.TRUCK in pack.constraints:
                    if route["truck"] is not None and route["truck"].id != pack.constraints[Constraint.TRUCK]:
                        continue
            curr_dist = dist_graph.get_dist(section[-1]["package"].location_id, pack.location_id).weight
            if pack.deadline < END_OF_DAY:
                curr_dist -= skew   # Skew the distance based on some factor to make a selection more "favorable"
            if curr_dist < min_dist or curr_dist == min_dist and pack.deadline < END_OF_DAY:
                min_dist = curr_dist
                min_id = id
        # Got our min, pop it and load it
        min_pack = deliverable.pop(min_id)
        section.append({"package": min_pack})
        route["dependents"].pop(min_pack.id, None)
        route["contains"][min_pack.id] = min_pack
        if min_pack.constraints:
            if Constraint.DELIVER_WITH in min_pack.constraints:
                for id in min_pack.constraints[Constraint.DELIVER_WITH]:
                    if id in route["contains"]:
                        continue
                    route["dependents"][id] = deliverable[id]
    # Annoying leftover things
    route["ordered"].append({"package": dummy})
    jam_dependents_in(route, deliverable, dist_graph)
    slap_stats_on(route, dist_graph)
    return route


def jam_dependents_in(route: Dict, deliverable: HashTable, dist_graph: Graph):
    """
    Inserts straggling dependents that weren't previously placed in the route, 
    O(n*k) time and O(k) space where n is the length of the route and k is the number of dependents
    """
    real_route = route["ordered"]
    for id in route["dependents"]:
        pack = deliverable.pop(id)
        min_i = None
        min_dist = float('inf')
        for i in range(1, len(real_route)):
            # Sever distance between two packages, calculate new distance with this dependent between
            before = dist_graph.get_dist(real_route[i-1]["package"].location_id, pack.location_id).weight
            after = dist_graph.get_dist(real_route[i]["package"].location_id, pack.location_id).weight
            sever = dist_graph.get_dist(real_route[i-1]["package"].location_id, real_route[i]["package"].location_id).weight
            curr_dist = before + after - sever
            if curr_dist < min_dist:
                min_dist = curr_dist
                min_i = i
        real_route.insert(min_i, {"package": pack})


def slap_stats_on(route: Dict, dist_graph: Graph):
    """Slaps some stats on a route like time and distance for easier processing."""
    real_route = route["ordered"]
    total_time = route["start"]
    total_dist = 0
    for i in range(len(real_route)):
        dist = 0 if i == 0 else dist_graph.get_dist(real_route[i-1]["package"].location_id, real_route[i]["package"].location_id).weight
        total_time += timedelta(hours=dist/18)
        total_dist += dist
        real_route[i]["time"] = total_time
        real_route[i]["distance"] = total_dist
    route["total_distance"] = real_route[-1]["distance"]


def route_generator(package_table: HashTable, dist_graph: Graph, trucks: List[Truck]):
    """Generates routes by considering passed in variables to alter selection criteria, O(n²) time and O(n) space."""
    if not package_table or not distance_graph:
        print("No data for simulation.")
    global routes
    routes = []
    deliverable = HashTable()
    for id in package_table:
        pack = package_table[id]
        deliverable[pack.id] = pack
    # I don't like that I hardcoded 3 specific routes with start times and assigned trucks.
    # Would be more robust if there were routines to calculate the ideal number and time/truck/skew combinations.
    routes.append(build_route(deliverable, dist_graph, START_OF_DAY, truck=trucks[0], skew=0.5))
    routes.append(build_route(deliverable, dist_graph, datetime.combine(date.today(), time(9,5,0)), truck=trucks[1], skew=0.5))
    routes.append(build_route(deliverable, dist_graph, datetime.combine(date.today(), time(11,0,0)), truck=trucks[1], skew=0.5))
    return routes


def run_sim(target_time: datetime = END_OF_DAY):
    """Sets status of packages according to target_time, generates routes and trucks if required."""
    global routes, trucks
    if trucks is None:
        trucks = [Truck('1'), Truck('2'), Truck('3')]
    if routes is None:
        routes = route_generator(package_table, distance_graph, trucks)
    # Set status based on target_time
    for truck in trucks:
        truck.mileage = 0
    for route in routes:
        if route["start"] <= target_time:
            # Deliver those packages
            added_miles = 0
            for item in route["ordered"]:
                if item["time"] <= target_time:
                    item["package"].status = (Status.DELIVERED, item["time"])
                    added_miles = item["distance"]
                else:
                    item["package"].status = (Status.EN_ROUTE, route["truck"])
            for truck in trucks:
                if route["truck"].id == truck.id:
                    truck.mileage += added_miles
        else:
            for item in route["ordered"]:
                item["package"].status = (Status.AT_HUB, None)
                if Constraint.DELAYED in item["package"].constraints:
                    if item["package"].constraints[Constraint.DELAYED] > target_time:
                        item["package"].status = (Status.DELAYED, item["package"].constraints[Constraint.DELAYED])


def user_interface():
    run_sim()
    for id in package_table:
        package = package_table[id]
        print(f"{package.id} {package.status}")


def main():
    try:
        load_data()
    except FileNotFoundError:
        print("Error loading data.")
    else:
        user_interface()

if __name__ == "__main__":
    main()
