# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from dataclasses import dataclass
import numpy as np
import math
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

# Matrice di adiacenza
# ---------------------------- nodo
# |     a_sd
# |
# |
# |
# nodo
# L'elemento a_sd indica il costo della connessione tra l'aereoporto s e l'aereoporto d (rispettivamente source e destination)
# se è negativo (-1), non c'è connessione
# se è > 0 allora c'è una connessione con il costo
# se è = 0 allora è una connessione tra lo stesso aereoporto
# Nel nostro caso il costo è la distanza tra i due aereoporti in linea d'aria
# La riga indica l'aereoporto sorgente

# Ogni volta che carico una rotta, aggiungo una tupla (i, j) in un set, se non esiste già
# Così escludo tutti i duplicati delle rotte tra due aereoporti
# Prendo solo le rotte che hanno stops = 0 (ossia solo rotte dirette senza scalo)

# Poi faccio una funzione che converte una tupla (partenza, destinazione) nella sua distanza con la formula


@dataclass
class Airport:
    dataset_id: int
    new_id: int
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    type: str

@dataclass
class Route:
    company: str
    airline_id: int
    source_name: str
    src_dataset_id: int             # Id of the source airport using the dataset one
    destination_name: str
    dest_dataset_id: int
    sd: tuple[int, int]             # Tuple with source-destination using program-generated ids
    stops: int

def clear(input: str) -> str:
    return input.replace("\"", "")

def load_european_airports() -> list[Airport]:
    """Load all airports of european cities"""
    f = open("input/airports.dat")
    reader = csv.reader(f, delimiter=",", quotechar="\"")
    try:
        airports = []
        id = 0
        for row in reader:
            country = clear(row[3])
            if country not in included_countries:
                continue

            airports.append(Airport(
                dataset_id= int(row[0]),
                new_id = id,                # Each airport has his own new id
                name=clear(row[1]),
                city=clear(row[2]),
                country=country,
                latitude=float(row[6]),
                longitude=float(row[7]),
                type=row[12]
            ))
            id += 1

        return airports
    except ValueError as e:
        print(e)

def load_routes(all_airports: list[Airport]) -> list[Route]:
    """
    Load all routes from airport A to B ensuring that there are no stops between them and that they belong only to the list we want to work with
    :param all_airports: List of all the airports we work with
    :return:
    """
    f = open("input/routes.dat")
    ok_ids = list(map(lambda airport: airport.dataset_id, all_airports))
    reader = csv.reader(f, delimiter=",", quotechar="\"")

    try:
        routes = []
        for row in reader:
            stops = int(row[7])
            if stops == 0 and row[1] != "\\N" and row[3] != "\\N" and row[5] != "\\N":
                # Only single-connections
                s = int(row[3])
                d = int(row[5])

                if s in ok_ids and d in ok_ids:         # Check that the airport starts from an airport in the right area and ends in airport in area
                    routes.append(Route(
                        company=row[0],
                        airline_id=int(row[1]),
                        source_name=row[2],
                        src_dataset_id=s,
                        destination_name=row[4],
                        dest_dataset_id=d,
                        stops=stops,
                        sd=(get_airport_with_dataset_id(s, all_airports).new_id, get_airport_with_dataset_id(d, all_airports).new_id)
                    ))

        return routes
    except ValueError as e:
        print(e)

def get_airport_with_dataset_id(id: int, a: list[Airport]) -> Airport | None:
    return list(filter(lambda t: t.dataset_id == id, a))[0]


def get_airport_with_internal_id(genid: int, a: list[Airport]) -> Airport | None:
    return list(filter(lambda t: t.new_id == genid, a))[0]

def calc_distance(s_data: Airport, d_data: Airport) -> float:
    s_lat_rad = np.radians(s_data.latitude)
    s_long_rad = np.radians(s_data.longitude)
    d_lat_rad = np.radians(d_data.latitude)
    d_long_rad = np.radians(d_data.longitude)

    R = 6371000     # Medium earth radius
    d = 2 * R * math.asin(
        math.sqrt(
            math.pow((math.sin((s_lat_rad - d_lat_rad)/2)), 2) + (
                math.cos(s_lat_rad) * math.cos(d_lat_rad) * math.pow(math.sin((s_long_rad - d_long_rad) / 2), 2)
            )
        ))

    return d

def create_graph(airports: list[Airport], routes: list[Route]):
    """
    Create the graph and return the adjacency matrix
    :param airports:
    :param routes:
    :return:
    """
    tot_airports = len(airports)
    # Creo una matrice identità tot_airports x tot_airports
    matrix = np.full((tot_airports, tot_airports), -1)
    np.fill_diagonal(matrix, 0)

    for route in routes:
        s = route.sd[0]         # internal id of the source airport (not the dataset one)
        s_data = get_airport_with_internal_id(s, airports)
        d = route.sd[1]         # internal id of the destination airport (not the dataset one)
        d_data = get_airport_with_internal_id(d, airports)

        if matrix[s][d] == -1:
            matrix[s][d] = calc_distance(s_data, d_data)

    return matrix

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    european_airports = load_european_airports()

    print("European airports alghorithm by Gabriele & Umberto")
    print(f"{len(european_airports)}")
    print(european_airports)

    routes = load_routes(european_airports)
    print(f"Loaded {len(routes)} routes")

    matrix = create_graph(european_airports, routes)
    print(matrix)
