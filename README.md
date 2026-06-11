# Airports Network analysis
By Gabriele Cavallo & Umberto Sapienza
Politecnico di Torino, anno 2026, corso di Reti e Sistemi Complessi

  
Nella repository si trova il codice sorgente del programma realizzato per l'analisi della connettività degli aereoporti europei.  
Struttura dei file e cartelle: 
- `main.py` Codice sorgente principale
- `input` Cartella con i file di input per il progetto e i dataset utilizzati

## Come eseguirlo
Eseguire lo script `main.py` tramite un interprete Python

## Caratteristiche e funzionalità
* Caricamento degli aereoporti europei e delle connessioni dirette tramite dataset OpenFlights
* Creazione del grafo tramite matrice di adiacenza
* Calcolo del percorso minimo tra 2 aereoporti a piacere tra quelli disponibili
* Confronto dell'algoritmo DFS (applicato al percorso minimo) con BFS
* Valutazione dei tempi di esecuzione