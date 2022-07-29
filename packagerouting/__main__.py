import csv
import os

from packagerouting.datastructures import HashTable, Graph


distance_graph = package_table = location_dict = None


def load_data():
    """Loads data from csv files."""
    global distance_graph, package_table, location_dict
    distance_graph, package_table, location_dict = Graph(), HashTable(), {}
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
        reader = csv.DictReader(file, delimiter=',', quotechar='"')
        for line in reader:
            id = line.pop("Package ID")
            package_table[id] = line

    with open(f"{basepath}data/locations.csv") as file:
        reader = csv.DictReader(file, delimiter=',', quotechar='"')
        for line in reader:
            id = line.pop("Location ID")
            location_dict[id] = line


def main():
    load_data()


if __name__ == "__main__":
    main()
