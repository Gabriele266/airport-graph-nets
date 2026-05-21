# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from dataclasses import dataclass
import csv

# List with all the included countries in this simulation
included_countries = [
    "Albania",
    "Andorra",
    "Austria",
    "Belgium",
    "Bosnia and Herzegovina",
    "Bulgaria",
    "Croatia",
    "Cyprus",
    "Czech Republic",
    "Denmark",
    "Estonia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hungary",
    "Iceland",
    "Ireland",
    "Italy",
    "Kosovo",
    "Latvia",
    "Liechtenstein",
    "Lithuania",
    "Luxembourg",
    "Malta",
    "Moldova",
    "Monaco",
    "Montenegro",
    "Netherlands",
    "North Macedonia",
    "Norway",
    "Poland",
    "Portugal",
    "Romania",
    "San Marino",
    "Serbia",
    "Slovakia",
    "Slovenia",
    "Spain",
    "Sweden",
    "Switzerland",
    "United Kingdom",
    "Vatican City",
]

@dataclass
class Airport:
    id: int
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    type: str

def clear(input: str) -> str:
    return input.replace("\"", "")

def load_file() -> list[Airport]:
    f = open("input/airports.dat")
    reader = csv.reader(f, delimiter=",", quotechar="\"")
    try:

        airports = []
        for row in reader:
            airports.append(Airport(
                id = int(row[0]),
                name=clear(row[1]),
                city=clear(row[2]),
                country=clear(row[3]),
                latitude=float(row[6]),
                longitude=float(row[7]),
                type=row[12]
            ))

        return airports
    except ValueError as e:
        print(e)

def filter_airports_by_box(lat_start: float, lat_end: float, long_start: float, long_end: float, airports: list[Airport]) -> list[Airport]:
    """
    Filters the list of all the airports using a box of coordinates. All the airports that fit the box will be included, the other will be
    removed
    :param lat_start: Start of the box for latitude
    :param lat_end:
    :param long_start: Start of the box for longitude
    :param long_end:
    :param airports List of input airports
    :raises ValueError if coordinate box is invalid
    :return: The list of all the airports fitting the box
    """
    res = list()
    # Input check
    if lat_end < lat_start:
        raise ValueError(f"Latitude box error {lat_start}-{lat_end}")

    if long_end < long_start:
        raise ValueError(f"Longitude box error {long_start}-{long_end}")

    for airport in airports:
        if lat_start <= airport.latitude <= lat_end:
            if long_start <= airport.longitude <= long_end:
                res.append(airport)

    return res

def filter_airports_by_country(airports: list[Airport], ok_countries: list[str])-> list[Airport]:
    return list(filter(lambda t: t.country in ok_countries, airports))

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    all_airports = load_file()
    # Bounding box for getting only the european countries, exluding Ucraine and Russia because they have lots of airports
    min_lat = 34.0
    max_lat = 72.0
    min_lon = -25.0
    max_lon = 22.0

    european_airports = filter_airports_by_country(all_airports, included_countries)
    print("European airports alghorithm by Gabriele & Umberto")
    print(f"{len(european_airports)} loaded over a total of {len(all_airports)}")
    print(european_airports)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
