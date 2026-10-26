# Gelateria: dashboard vendite

Progetto personale di Business Intelligence. Simula tre stagioni di vendite di una gelateria
artigianale di Torino (marzo 2024 – ottobre 2026) e le analizza in una dashboard interattiva con menu laterale, filtro per anno e tema chiaro o scuro.

**Domanda a cui risponde:** quando conviene avere più personale e più scorte, e come cambiano
le vendite con meteo, festività, stagione e gusti?

## Cosa c'è dentro

| File | A cosa serve |
|---|---|
| `genera_dati.py` | Crea i dati: scontrini, prodotti, gusti, calendario con meteo. Scarica il meteo reale di Torino da Open-Meteo; se non riesce usa un meteo simulato. |
| `crea_dashboard.py` | Legge i CSV, calcola i totali e crea `dashboard.html`. |
| `modello_dashboard.html` | La pagina della dashboard: stile panna e rosa, con tema scuro al cioccolato, grafici disegnati in SVG, nessuna libreria esterna. |
| `dashboard.html` | La dashboard già pronta: si apre con un doppio clic. |
| `rappresentazione-statica.html` | L'app fotografata: tutte le pagine una sotto l'altra, senza JavaScript, identiche alla dashboard. |
| `crea_statica.py` | Ricrea la versione statica (facoltativo, serve Playwright). |
| `dati/` | I 5 file CSV (circa 230.000 righe di vendite). |
| `test_*.py` | 33 test automatici che controllano i calcoli. |
| `power-bi/misure_dax.md` | Misure DAX e colonne calcolate, per rifare la stessa analisi in Power BI. |
| `screenshot/` | Immagini delle quattro pagine. |

## Come si usa

Serve Python 3.9 o successivo (python.org). Non c'è nulla da installare.

```
python genera_dati.py       # crea la cartella dati
python -m unittest discover # controlla i calcoli (33 test)
python crea_dashboard.py    # crea dashboard.html
```

Facoltativo, per rifare la versione statica dopo aver cambiato i dati:

```
pip install playwright
playwright install chromium
python crea_statica.py
```

Su Windows basta un doppio clic su `avvia.bat`. Con `python genera_dati.py --meteo-simulato`
non serve internet.

**Nota sui dati inclusi.** I CSV e la dashboard in questa cartella usano un meteo simulato.
Lanciando `genera_dati.py` con la connessione attiva, il meteo diventa quello reale di Torino
e i numeri cambiano un po'. La nota in fondo alla dashboard dice sempre quanti giorni sono reali.

## Le pagine

1. **Panoramica:** incasso, scontrini, scontrino medio, quota carta, andamento mensile, giorni migliori.
2. **Meteo:** quanto pesano pioggia e caldo, confrontando ogni giornata con la media del suo mese.
3. **Gusti e prodotti:** classifica dei gusti, frutta contro creme, peso delle vaschette.
4. **Orari:** mappa dei picchi per giorno della settimana e ora.
5. **Informazioni:** da dove arrivano i dati, cosa tiene conto la simulazione, glossario.

## Come sono fatti i dati

Le vendite sono simulate, non provengono da un'attività reale. Lo script tiene conto di:
giorno della settimana, festività (compreso San Giovanni, patrono di Torino), stagionalità,
calo di metà agosto, orari di apertura, caldo e pioggia, gusti stagionali, crescita negli anni,
aumento dei prezzi e diffusione dei pagamenti con carta. Il seme casuale è fisso:
gli stessi comandi producono sempre gli stessi dati.

## Pubblicarla online

`dashboard.html` è un file unico: si può caricare così com'è su GitHub Pages o Netlify.
