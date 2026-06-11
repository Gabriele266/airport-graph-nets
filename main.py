# Tesina Reti e Sistemi complessi, anno 2026
# Politecnico di Torino
# Studenti:
#       - Gabriele Cavallo
#       - Umberto Sapienza

from dataclasses import dataclass
from collections import deque
import numpy as np
import math
import csv
import time
import sys


# ============================================================
# LISTA DEI PAESI EUROPEI DA CONSIDERARE
# ============================================================
# Il dataset OpenFlights contiene aeroporti di tutto il mondo.
# Noi vogliamo lavorare solo sugli aeroporti europei.
#
# Quando leggiamo il file input/airports.dat, controlliamo il paese
# dell'aeroporto. Se il paese e presente in questa lista, allora
# teniamo l'aeroporto. Altrimenti lo ignoriamo.
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


# ============================================================
# CLASSI DATACLASS
# ============================================================
# Una dataclass permette di creare oggetti con attributi senza dover
# scrivere manualmente il metodo __init__.
#
# Airport rappresenta un aeroporto.
# Route rappresenta una rotta diretta tra due aeroporti.


@dataclass
class Airport:
    dataset_id: int
    # ID originale presente nel dataset OpenFlights.
    # Questo ID non e sempre progressivo: possono esserci "buchi".

    new_id: int
    # ID interno creato dal nostro programma.
    # Questo ID e progressivo: 0, 1, 2, 3...
    # Lo usiamo per costruire facilmente la matrice di adiacenza.

    name: str
    # Nome completo dell'aeroporto.

    city: str
    # Citta in cui si trova l'aeroporto.

    country: str
    # Paese in cui si trova l'aeroporto.

    latitude: float
    # Latitudine geografica dell'aeroporto.

    longitude: float
    # Longitudine geografica dell'aeroporto.

    type: str
    # Tipo di struttura nel dataset.


@dataclass
class Route:
    company: str
    # Codice della compagnia aerea.

    airline_id: int
    # ID della compagnia aerea.
    # Se manca nel dataset, useremo -1.

    source_name: str
    # Codice/nome breve dell'aeroporto di partenza nel dataset.

    src_dataset_id: int
    # ID originale OpenFlights dell'aeroporto di partenza.

    destination_name: str
    # Codice/nome breve dell'aeroporto di arrivo nel dataset.

    dest_dataset_id: int
    # ID originale OpenFlights dell'aeroporto di arrivo.

    sd: tuple[int, int]
    # Coppia (source, destination) usando gli ID interni new_id.
    # Esempio: (13, 45) significa rotta dall'aeroporto interno 13 al 45.

    stops: int
    # Numero di fermate della rotta nel dataset.
    # Noi teniamo solo stops = 0, cioe voli diretti.


# ============================================================
# CARICAMENTO AEROPORTI
# ============================================================

def load_european_airports() -> list[Airport]:
    """
    Carica gli aeroporti europei dal file input/airports.dat.

    Il dataset contiene tanti aeroporti, ma noi teniamo solo quelli
    il cui paese e nella lista included_countries.

    Inoltre assegniamo a ogni aeroporto un ID interno progressivo.
    Questo serve perche la matrice di adiacenza usa indici da 0 a N-1.
    """

    airports = []
    new_id = 0

    with open("input/airports.dat", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=",", quotechar="\"")

        for row in reader:
            country = row[3]

            # Se il paese non e europeo secondo la nostra lista,
            # saltiamo questo aeroporto.
            if country not in included_countries:
                continue

            airport = Airport(
                dataset_id=int(row[0]),
                new_id=new_id,
                name=row[1],
                city=row[2],
                country=country,
                latitude=float(row[6]),
                longitude=float(row[7]),
                type=row[12]
            )

            airports.append(airport)

            # Incrementiamo l'ID interno solo quando aggiungiamo davvero
            # un aeroporto alla lista.
            new_id += 1

    return airports


# ============================================================
# FUNZIONI DI RICERCA AEROPORTI
# ============================================================

def get_airport_with_dataset_id(id: int, airports: list[Airport]) -> Airport | None:
    """
    Cerca un aeroporto usando l'ID originale del dataset OpenFlights.

    Questo serve quando leggiamo le rotte, perche routes.dat usa gli ID
    originali del dataset, non i nostri ID interni.
    """

    return list(filter(lambda airport: airport.dataset_id == id, airports))[0]


def get_airport_with_internal_id(genid: int, airports: list[Airport]) -> Airport | None:
    """
    Cerca un aeroporto usando l'ID interno creato dal programma.

    Questo serve quando lavoriamo sulla matrice di adiacenza,
    perche righe e colonne della matrice usano proprio questi ID interni.
    """

    return list(filter(lambda airport: airport.new_id == genid, airports))[0]


# ============================================================
# CARICAMENTO ROTTE
# ============================================================

def load_routes(all_airports: list[Airport]) -> list[Route]:
    """
    Carica le rotte dal file input/routes.dat.

    Una rotta viene tenuta solo se:
    - ha un aeroporto di partenza valido;
    - ha un aeroporto di arrivo valido;
    - partenza e arrivo sono entrambi aeroporti europei caricati prima;
    - stops = 0, cioe il volo e diretto.

    Nota importante:
    Per BFS ci interessa sapere se esiste una connessione tra due aeroporti.
    Non ci interessa quale compagnia effettua il volo.
    """

    routes = []

    # Lista degli ID originali degli aeroporti europei.
    # La usiamo per verificare se una rotta riguarda aeroporti europei.
    ok_ids = list(map(lambda airport: airport.dataset_id, all_airports))

    with open("input/routes.dat", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=",", quotechar="\"")

        for row in reader:
            # Nel dataset alcuni campi possono avere valore "\N",
            # cioe dato mancante.
            #
            # Per creare una rotta ci servono obbligatoriamente:
            # row[3] = ID aeroporto sorgente
            # row[5] = ID aeroporto destinazione
            if row[3] == "\\N" or row[5] == "\\N":
                continue

            stops = int(row[7])

            # Teniamo solo voli diretti.
            # Se stops fosse > 0, quella riga rappresenterebbe gia una rotta
            # con fermate interne e non un collegamento diretto semplice.
            if stops != 0:
                continue

            source_dataset_id = int(row[3])
            destination_dataset_id = int(row[5])

            # Controlliamo che entrambi gli aeroporti siano europei.
            if source_dataset_id in ok_ids and destination_dataset_id in ok_ids:

                source_airport = get_airport_with_dataset_id(source_dataset_id, all_airports)
                destination_airport = get_airport_with_dataset_id(destination_dataset_id, all_airports)

                route = Route(
                    company=row[0],

                    # airline_id non e fondamentale per la BFS.
                    # Se manca, mettiamo -1 invece di scartare la rotta.
                    airline_id=int(row[1]) if row[1] != "\\N" else -1,

                    source_name=row[2],
                    src_dataset_id=source_dataset_id,
                    destination_name=row[4],
                    dest_dataset_id=destination_dataset_id,
                    stops=stops,

                    # Qui convertiamo gli ID originali del dataset negli ID interni.
                    sd=(source_airport.new_id, destination_airport.new_id)
                )

                routes.append(route)

    return routes

# ============================================================
# CALCOLO DISTANZA tra due coppie di coordinate
# ============================================================

def calc_distance(s_data: Airport, d_data: Airport) -> float:
    """
    Calcola la distanza in linea d'aria tra due aeroporti.

    Usiamo latitudine e longitudine.
    La formula usata e quella dell'haversine.

    La distanza restituita e in metri.
    Nel grafo poi la convertiamo in chilometri.

    Attenzione:
    La BFS non usa questa distanza per scegliere il percorso.
    BFS cerca il numero minimo di voli, non i chilometri minimi.
    """

    s_lat_rad = np.radians(s_data.latitude)
    s_long_rad = np.radians(s_data.longitude)
    d_lat_rad = np.radians(d_data.latitude)
    d_long_rad = np.radians(d_data.longitude)

    earth_radius = 6371000

    distance = 2 * earth_radius * math.asin(
        math.sqrt(
            math.pow(math.sin((s_lat_rad - d_lat_rad) / 2), 2)
            + math.cos(s_lat_rad)
            * math.cos(d_lat_rad)
            * math.pow(math.sin((s_long_rad - d_long_rad) / 2), 2)
        )
    )

    return distance

# ============================================================
# CREAZIONE GRAFO
# ============================================================

def create_graph(airports: list[Airport], routes: list[Route]):
    """
    Crea la matrice di adiacenza del grafo.

    Se abbiamo N aeroporti, creiamo una matrice N x N.

    Significato di adj_matrix[i][j]:
    - -1 significa: non esiste una rotta tra aeroporto i e aeroporto j
    -  0 significa: i e j sono lo stesso aeroporto
    - >0 significa: esiste una rotta, e il valore e la distanza in km

    In questa versione rendiamo il grafo BIDIREZIONALE:
    se nel dataset esiste A -> B, inseriamo anche B -> A.

    Perche?
    Perche nel tuo progetto vuoi studiare la connettivita e trovare un
    percorso minimo tra aeroporti. Rendere il grafo bidirezionale riduce
    i casi in cui due aeroporti sembrano non collegati solo per il verso
    delle rotte nel dataset.
    """

    total_airports = len(airports)

    # All'inizio mettiamo -1 ovunque:
    # significa che non conosciamo nessuna rotta tra gli aeroporti.
    adj_matrix = np.full((total_airports, total_airports), -1)

    # La diagonale rappresenta aeroporto -> stesso aeroporto.
    # La distanza da un aeroporto a se stesso e 0.
    np.fill_diagonal(adj_matrix, 0)

    for route in routes:
        source_id = route.sd[0]
        destination_id = route.sd[1]

        source_airport = get_airport_with_internal_id(source_id, airports)
        destination_airport = get_airport_with_internal_id(destination_id, airports)

        distance_km = calc_distance(source_airport, destination_airport) / 1000

        # Inseriamo la rotta originale: source -> destination.
        if adj_matrix[source_id][destination_id] == -1:
            adj_matrix[source_id][destination_id] = distance_km

        # Inseriamo anche la rotta inversa: destination -> source.
        # Questo rende il grafo non orientato, cioe bidirezionale.
        if adj_matrix[destination_id][source_id] == -1:
            adj_matrix[destination_id][source_id] = distance_km

    return adj_matrix


# ============================================================
# BFS PER PERCORSO MINIMO
# ============================================================

def bfs_shortest_path(adj_matrix, source_id: int, destination_id: int) -> list[int] | None:
    """
    Trova il percorso minimo in numero di voli usando BFS.

    BFS significa Breadth First Search, cioe visita in ampiezza.

    Perche BFS e adatta a questo problema?
    Perche ogni rotta conta come 1 volo.
    Quindi vogliamo minimizzare il numero di archi attraversati.

    BFS visita il grafo a livelli:
    - prima tutti gli aeroporti raggiungibili con 1 volo;
    - poi tutti quelli raggiungibili con 2 voli;
    - poi tutti quelli raggiungibili con 3 voli;
    - e cosi via.

    Quindi appena BFS trova la destinazione, siamo sicuri che quello
    sia il percorso con il numero minimo di voli.

    La funzione restituisce:
    - una lista di ID interni se trova un percorso;
    - None se non esiste nessun percorso.
    """

    # Caso banale: partenza e arrivo coincidono.
    if source_id == destination_id:
        return [source_id]

    # deque e una coda efficiente.
    # BFS usa una coda FIFO: il primo inserito e' il primo estratto.
    queue = deque([source_id])

    # visited contiene gli aeroporti gia visitati.
    # Serve per evitare cicli e ripetizioni.
    visited = {source_id}

    # previous serve per ricostruire il percorso alla fine.
    #
    # Se previous[B] = A, significa:
    # "siamo arrivati all'aeroporto B passando da A".
    previous = {source_id: None}

    while queue:
        # Prendiamo il prossimo aeroporto da esplorare.
        current_id = queue.popleft()

        # Guardiamo tutti i possibili vicini di current_id.
        # La riga adj_matrix[current_id] contiene tutte le connessioni
        # da current_id verso gli altri aeroporti.
        for neighbor_id, distance in enumerate(adj_matrix[current_id]):

            # Se distance <= 0 non e una rotta utile:
            # -1 = nessuna rotta
            #  0 = stesso aeroporto
            if distance <= 0:
                continue

            # Se il vicino e gia stato visitato, lo saltiamo.
            if neighbor_id in visited:
                continue

            # Segniamo il vicino come visitato.
            visited.add(neighbor_id)

            # Memorizziamo da dove siamo arrivati.
            previous[neighbor_id] = current_id

            # Ottimizzazione importante:
            # appena troviamo la destinazione, ci fermiamo.
            # Non serve visitare tutto il grafo.
            if neighbor_id == destination_id:
                return rebuild_path(previous, destination_id)

            # Se non era la destinazione, lo aggiungiamo alla coda
            # per esplorarlo successivamente.
            queue.append(neighbor_id)

    # Se la coda si svuota, non abbiamo trovato la destinazione.
    return None


def rebuild_path(previous: dict, destination_id: int) -> list[int]:
    """
    Ricostruisce il percorso finale dopo la BFS.

    Durante BFS non salviamo direttamente tutto il percorso.
    Salviamo solo il padre di ogni nodo.

    Esempio:
    previous[10] = 5
    previous[5] = 2
    previous[2] = 0

    Significa che il percorso e:
    0 -> 2 -> 5 -> 10

    Per ricostruirlo, partiamo dalla destinazione e risaliamo all'indietro
    fino alla sorgente. Poi invertiamo la lista.
    """

    path = []
    current_id = destination_id

    while current_id is not None:
        path.append(current_id)
        current_id = previous[current_id]

    # Ora path e al contrario:
    # destinazione -> ... -> partenza
    #
    # Lo invertiamo per ottenere:
    # partenza -> ... -> destinazione
    path.reverse()

    return path


# ============================================================
# COMPONENTI CONNESSE
# ============================================================

def find_connected_component(adj_matrix, start_id: int) -> set[int]:
    """
    Trova tutti gli aeroporti collegati a start_id.

    Questa e una BFS diversa da bfs_shortest_path:
    - non cerca una destinazione specifica;
    - visita tutta la componente connessa.

    Una componente connessa e un gruppo di aeroporti in cui ogni aeroporto
    puo raggiungere gli altri aeroporti del gruppo.
    """

    queue = deque([start_id])
    visited = {start_id}

    while queue:
        current_id = queue.popleft()

        for neighbor_id, distance in enumerate(adj_matrix[current_id]):
            if distance <= 0:
                continue

            if neighbor_id in visited:
                continue

            visited.add(neighbor_id)
            queue.append(neighbor_id)

    return visited


def find_largest_connected_component(adj_matrix) -> set[int]:
    """
    Trova la componente connessa piu grande del grafo.

    Perche serve?
    Perche anche se abbiamo tante rotte, alcuni aeroporti possono essere
    isolati o appartenere a piccoli gruppi separati.

    Se scegli due aeroporti in componenti diverse, nessun algoritmo potra
    trovare un percorso tra loro, perche quel percorso non esiste nel grafo.

    Per questo calcoliamo la componente piu grande e consigliamo all'utente
    di scegliere aeroporti da quella lista.
    """

    all_visited = set()
    largest_component = set()

    for airport_id in range(len(adj_matrix)):

        # Se questo aeroporto e gia stato visitato come parte di una
        # componente precedente, non serve ripartire da lui.
        if airport_id in all_visited:
            continue

        component = find_connected_component(adj_matrix, airport_id)

        # Aggiungiamo tutti gli aeroporti di questa componente
        # all'insieme globale dei gia visitati.
        all_visited.update(component)

        # Se questa componente e piu grande della migliore trovata finora,
        # la salviamo come componente principale.
        if len(component) > len(largest_component):
            largest_component = component

    return largest_component


# ============================================================
# STAMPA RISULTATI
# ============================================================

def print_path(path: list[int], airports: list[Airport]) -> None:
    """
    Stampa il percorso minimo trovato dalla BFS.

    Se il percorso contiene:
    A -> B -> C

    allora:
    - voli = 2
    - scali = 1, perche B e intermedio.
    """

    number_of_flights = len(path) - 1
    number_of_stops = max(0, number_of_flights - 1)

    print("\nPercorso minimo trovato:")

    for airport_id in path:
        airport = get_airport_with_internal_id(airport_id, airports)
        print(f"- ID {airport.new_id}: {airport.name} ({airport.city}, {airport.country})")

    print(f"\nNumero minimo di voli: {number_of_flights}")
    print(f"Numero minimo di scali: {number_of_stops}")


def print_airports_in_component(
    airports: list[Airport],
    component: set[int],
    max_to_print: int = 100
) -> None:
    """
    Stampa alcuni aeroporti appartenenti alla componente principale.

    Se scegli due aeroporti da questa lista, e molto piu probabile
    che la BFS trovi un percorso, perche appartengono allo stesso gruppo
    collegato del grafo.

    max_to_print evita di stampare centinaia o migliaia di righe.
    """

    print(f"\nAeroporti nella componente principale: {len(component)}")
    print(f"Stampo i primi {max_to_print} aeroporti della componente principale:\n")

    count = 0

    for airport in airports:
        if airport.new_id not in component:
            continue

        print(f"ID {airport.new_id}: {airport.name} - {airport.city}, {airport.country}")
        count += 1

        if count == max_to_print:
            break


def search_airports_by_city(airports: list[Airport], component: set[int]) -> None:
    """
    Permette all'utente di cercare aeroporti per citta.

    Questa funzione e utile per non dover scorrere manualmente tutta la lista.
    Cerca solo dentro la componente principale, cosi mostra aeroporti piu utili.
    """

    city = input("\nCerca una citta' nella componente principale, oppure premi INVIO per saltare: ")

    if city.strip() == "":
        return

    city = city.lower()
    found = False

    print("\nRisultati ricerca:")

    for airport in airports:
        if airport.new_id not in component:
            continue

        if city in airport.city.lower() or city in airport.name.lower():
            print(f"ID {airport.new_id}: {airport.name} - {airport.city}, {airport.country}")
            found = True

    if not found:
        print("Nessun aeroporto trovato con questa ricerca.")

def dfs_shortest_path(source_id: int, destination_id: int, adj_matrix) -> list[int] | None:
    """
    Ricerca del cammino minimo tra due aereoporti tramite algoritmo DFS.
    L'implementazione è ricorsiva
    :return: Una lista con il percorso minimo tra i due aereoporti oppure None se non è presente un percorso
    """

    # Caso banale: partenza e arrivo coincidono.
    if source_id == destination_id:
        return [source_id]

    paths: list[list[int]] = []     # Dizionario con la lista di tutti i percorsi trovati che portano da A a B
                                        # Ogni percorso è composto da una lista degli ID
    # Trovare i nodi adiacenti ad A
    # Se non ci sono adiacenti, la ricorsione termina e il percorso non viene aggiunto
    # Per ogni nodo adiacente, vedere se è B --> In tal caso il percorso è finito e posso aggiungerlo alla lista
    # Altrimenti per ogni nodo ripetere la cosa
    explore_adiacent(source_id, [source_id], adj_matrix, destination_id, paths)

    # Ricerco il percorso minimo scorrendo tutti i percorsi e cercando quello che richiede meno scali
    # Alternativamente potrei scorrerli e cercare quello che percorre la distanza minore
    shortest_path = [0, 0, 0, 0, 0, 0, 0, 0, 0]         # Inizializzo con un vettore più lungo del più lungo dei percorsi che posso trovare
    for index, path in enumerate(paths):
        if len(path) < len(shortest_path):
            shortest_path = path

    return shortest_path

def calculate_path_distance(path: list[int], adj_matrix)-> float:
    """
    Calcola la distanza totale percorsa in linea d'aria utilizzando questo path
    :param path: Lista di id degli aereoporti da seguire
    :param adj_matrix: Matrice di adiancenza
    :return: Distanza totale del percorso in linea d'aria in chilometri
    """
    total_airports_in_path = len(path)      # Numero totale di aereoporti nel percorso
    if total_airports_in_path == 0:
        return 0

    d = 0
    previous = path[0]
    for i in range(1, total_airports_in_path):
        d += adj_matrix[previous][path[i]]
        previous = path[i]

    return d

def explore_adiacent(node: int,
                     previous_explored_nodes: list[int],
                     adj_matrix,
                     destination_id: int,
                     paths_found: list[list[int]]
                     ):
    """
    Funzione ricorsiva che viene chiamata per esplorare tramite DFS il grafo delle connessioni tra gli aereoporti
    :param node:
    :param previous_explored_nodes:
    :param adj_matrix:
    :param destination_id:
    :param paths_found:
    :return:
    """

    if len(previous_explored_nodes) >= 4:
        return

    for node_index, distance in enumerate(adj_matrix[node]):
        if distance <= 0:                                       # Significa che i due nodi non sono connessi oppure sono lo stesso nodo
            continue

        if node_index == destination_id:                        # Ho trovato un nuovo percorso che parte da A e arriva a B
            paths_found.append(previous_explored_nodes + [node_index])         # Aggiungo alla lista dei percorsi trovati
        elif node_index not in previous_explored_nodes:         # Nuovo nodo che posso raggiungere e che non ho ancora esplorato
            explore_adiacent(node_index, (previous_explored_nodes + [node_index]), adj_matrix, destination_id, paths_found)         # Ri-eseguo l'esplorazione sul nodo chiamando ricorsivamente

# ============================================================
# PROGRAMMA PRINCIPALE
# ============================================================

if __name__ == '__main__':
    sys.setrecursionlimit(5000)             # Aumenta il limite massimo di ricorsioni per evitare che python blocchi il DFS troppo presto

    print("\nAlgoritmi sulla connettivita' degli aeroporti europei by Gabriele & Umberto\nAnno 2026, Politecnico di Torino, corso di Reti e sistemi complessi")

    # ------------------------------------------------------------
    # 1. Caricamento aeroporti
    # ------------------------------------------------------------
    european_airports: list[Airport] = load_european_airports()
    print(f"Aeroporti caricati: {len(european_airports)}")

    # Se non e stato caricato nessun aeroporto, il programma non puo continuare.
    # Una matrice 0 x 0 causerebbe errori nella BFS.
    if len(european_airports) == 0:
        print("Errore: non e' stato caricato nessun aeroporto.")
        print("Controlla che input/airports.dat esista e che i paesi siano scritti in inglese.")
        exit()

    # ------------------------------------------------------------
    # 2. Caricamento rotte
    # ------------------------------------------------------------
    routes = load_routes(european_airports)
    print(f"Rotte caricate: {len(routes)}")

    if len(routes) == 0:
        print("Errore: non e' stata caricata nessuna rotta.")
        print("Controlla che input/routes.dat esista e sia nel formato corretto.")
        exit()

    # ------------------------------------------------------------
    # 3. Creazione matrice di adiacenza
    # ------------------------------------------------------------
    t1 = time.time()
    matrix = create_graph(european_airports, routes)
    t2 = time.time()

    print(f"Matrice di adiacenza caricata in {t2 - t1} s")

    # ------------------------------------------------------------
    # 4. Calcolo componente principale
    # ------------------------------------------------------------
    # Questo evita il problema di scegliere aeroporti non collegati.
    # Se due aeroporti non sono nella stessa componente, non esiste
    # nessun percorso tra loro nel grafo.
    largest_component = find_largest_connected_component(matrix)

    print_airports_in_component(
        european_airports,
        largest_component,
        max_to_print=100
    )

    # Ricerca opzionale per citta/nome aeroporto.
    search_airports_by_city(european_airports, largest_component)

    # ------------------------------------------------------------
    # 5. Lettura input utente
    # ------------------------------------------------------------
    partenza = int(input("\nInserisci ID interno aeroporto di partenza: "))
    arrivo = int(input("Inserisci ID interno aeroporto di arrivo: "))

    # Controllo che gli ID esistano nella lista degli aeroporti.
    if partenza < 0 or partenza >= len(european_airports):
        print("Errore: ID di partenza non valido.")
        exit()

    if arrivo < 0 or arrivo >= len(european_airports):
        print("Errore: ID di arrivo non valido.")
        exit()

    # Controllo che entrambi gli aeroporti siano nella componente principale.
    # Se uno dei due non e nella componente principale, potrebbe non esserci
    # un percorso verso l'altro.
    if partenza not in largest_component:
        print("Errore: l'aeroporto di partenza non e' nella componente principale.")
        print("Scegli un ID tra quelli stampati nella lista della componente principale.")
        exit()

    if arrivo not in largest_component:
        print("Errore: l'aeroporto di arrivo non e' nella componente principale.")
        print("Scegli un ID tra quelli stampati nella lista della componente principale.")
        exit()

    partenza_details = get_airport_with_internal_id(partenza, european_airports)
    arrivo_details = get_airport_with_dataset_id(arrivo, european_airports)
    print(f"""\nHai scelto di partire dall'aereoporto di: {partenza_details.name} in {partenza_details.country}\n
Per arrivare all'aereoporto di: {arrivo_details.name} in {arrivo_details.country}\n\n
Confronto degli algoritmi BFS e DFS (rispettivamente):\n
    """)

    t1 = time.time()
    # ------------------------------------------------------------
    # 6. BFS per percorso minimo
    # ------------------------------------------------------------
    path = bfs_shortest_path(matrix, partenza, arrivo)
    t2 = time.time()
    r1 = t2 - t1

    print("--------------------- Soluzione BFS ------------------")
    print(f"Tempo impegato tramite algoritmo BFS: {r1} secondi")
    if path is None:
        print("\nNon esiste un percorso tra i due aeroporti.")
    else:
        print_path(path, european_airports)
        print(f"Distanza totale percorso: {calculate_path_distance(path, matrix)} km")
    print()

    # ------------------------------------------------------------
    # DFS
    # ------------------------------------------------------------
    t1 = time.time()
    path2 = dfs_shortest_path(partenza, arrivo, matrix)
    t2 = time.time()
    r2 = t2 - t1
    print("--------------------- Soluzione DFS ------------------")
    print(f"Tempo impiegato utilizzando il DFS: {r2} secondi")
    if path is None:
        print("\nNon esiste un percorso tra i due aeroporti con questo algoritmo.")
    else:
        print_path(path2, european_airports)
        print(f"Distanza totale percorso 2: {calculate_path_distance(path2, matrix)} km")
    print()
    print(f"Ratio dei tempi di esecuzione (tempo BFS/tempo DFS)%: {(r1/r2) * 100}%")
