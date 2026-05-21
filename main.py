from dataclasses import dataclass
import numpy as np
import math
import csv
import time

# Lista con i nomi di tutti i paesi europei che vogliamo includere
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
# Ad ogni aereoporto viene assegnato un ID interno (diverso da quello fornito dal dataset) in modo tale da semplificare la creazione
# della matrice di adiacenza. Gli id forniti dal dataset (marcati con _dataset) vengono comunque mantenuti per facilitare l'accesso alle informazioni
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

# Caricamento delle rotte:
# Escludo tutti i duplicati delle rotte tra due aereoporti
# Vengono prese solo le rotte che hanno stops = 0 (ossia solo rotte dirette senza scalo)

@dataclass
class Airport:
    dataset_id: int             # Identificatore Univoco fornito da OpenFlights
    new_id: int                 # Identificatore univoco incrementale calcolato dal programma per facilitare la creazione della matrice adiacenza
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
    src_dataset_id: int             # Id dell'aereoporto sorgente fornito dal dataset
    destination_name: str
    dest_dataset_id: int
    sd: tuple[int, int]             # Tupla sorgente-destinazione che utilizza gli id interni generati dal nostro programma
    stops: int

def load_european_airports() -> list[Airport]:
    """Load all airports of european cities"""
    f = open("input/airports.dat")
    reader = csv.reader(f, delimiter=",", quotechar="\"")
    try:
        airports = []
        id = 0
        for row in reader:
            country = row[3]
            if country not in included_countries:
                continue

            airports.append(Airport(
                dataset_id= int(row[0]),
                new_id = id,                # Each airport has his own new id
                name=row[1],
                city=row[2],
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
    Carica tutte le rotte presenti sul file, assicurandosi che arrivino e partano da aereoporti europei e che non richiedano fermate
    (solo rotte dirette senza scalo)
    :param all_airports: Lista di tutti gli aereoporti disponibili
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
                        sd=(get_airport_with_dataset_id(s, all_airports).new_id, get_airport_with_dataset_id(d, all_airports).new_id)   # Mappa gli id forniti da OpenFlights (che contengono dei buchi) con gli id interni generati dal programma (sicuramente incrementali e senza buchi)
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
    Crea il grafo e restituisce la matrice di adiacenza (sorgente-destinazione) con le distanze in linea d'aria associate alle rotte
    disponibili per ogni aereoporto

    Nota: considera la prima rotta disponibile tra i due aereoporti, non gestisce il caso in cui ci siano più rotte disponibili
    :param airports: Lista di tutti gli aereoporti
    :param routes: Lista di tutte le rotte
    :return: Matrice di adiacenza
    """
    tot_airports = len(airports)
    # Creo una matrice identità tot_airports x tot_airports
    adj_matrix = np.full((tot_airports, tot_airports), -1)
    np.fill_diagonal(adj_matrix, 0)

    for route in routes:
        s = route.sd[0]         # internal id of the source airport (not the dataset one)
        s_data = get_airport_with_internal_id(s, airports)
        d = route.sd[1]         # internal id of the destination airport (not the dataset one)
        d_data = get_airport_with_internal_id(d, airports)

        if adj_matrix[s][d] == -1:
            adj_matrix[s][d] = calc_distance(s_data, d_data)

    return adj_matrix

if __name__ == '__main__':
    european_airports = load_european_airports()

    print("European airports alghorithm by Gabriele & Umberto")
    print(f"{len(european_airports)}")
    print(european_airports)

    routes = load_routes(european_airports)
    print(f"Loaded {len(routes)} routes")

    t1 = time.time()
    matrix = create_graph(european_airports, routes)
    t2 = time.time()
    el = t2 - t1
    print(matrix)
    print(f"Adjacency matrix loaded in {el} s ")
