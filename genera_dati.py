"""
Genera i dati di vendita simulati di una gelateria di Torino.

Il meteo è reale (archivio storico di Open-Meteo); le vendite sono
simulate ma reagiscono al meteo come in una gelateria vera.
Se il download del meteo non riesce, lo script usa un meteo simulato.

Uso:
    python genera_dati.py                  # meteo reale da Open-Meteo
    python genera_dati.py --meteo-simulato # senza connessione

Crea la cartella "dati" con cinque file CSV:
calendario, prodotti, gusti, vendite, gusti_venduti.
Serve solo Python 3.9 o successivo, nessuna libreria da installare.
"""

import csv
import json
import random
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------
# Impostazioni
# ---------------------------------------------------------------

ANNI = [2024, 2025, 2026]
APERTURA = (3, 1)     # 1 marzo
CHIUSURA = (10, 15)   # 15 ottobre
TORINO = {"latitude": 45.07, "longitude": 7.69}
SEME = 42             # stesso seme = stessi dati a ogni esecuzione
CARTELLA = Path(__file__).parent / "dati"

# Scontrini medi in una giornata "normale" di ogni mese
BASE_MESE = {3: 70, 4: 120, 5: 200, 6: 300, 7: 350, 8: 320, 9: 220, 10: 100}
# Temperatura massima tipica di Torino in ogni mese
TEMP_NORMALE = {3: 14, 4: 18, 5: 22, 6: 27, 7: 30, 8: 29, 9: 24, 10: 18}
PROB_PIOGGIA = {3: .25, 4: .35, 5: .40, 6: .30, 7: .20, 8: .25, 9: .25, 10: .30}
# Lunedì ... domenica
FATTORE_GIORNO = [0.80, 0.82, 0.88, 0.95, 1.10, 1.40, 1.45]
CRESCITA_ANNO = {2024: 1.00, 2025: 1.06, 2026: 1.10}
# Prezzi rispetto al listino attuale: negli anni prima costava un po' meno
LISTINO_ANNO = {2024: 0.92, 2025: 0.96, 2026: 1.00}
PREZZO_KG = {2024: 20.00, 2025: 21.00, 2026: 22.00}   # gelato in vaschetta
QUOTA_CARTA = {2024: 0.45, 2025: 0.55, 2026: 0.63}

PRODOTTI = [
    # numero di gusti, prezzo del listino attuale (2026), peso = quanto spesso viene scelto
    # le vaschette hanno il peso in grammi: il prezzo si calcola dal prezzo al kg
    {"id": 1,  "nome": "Cono piccolo",      "tipo": "Cono",      "num_gusti": 2, "prezzo": 3.00,  "peso": 18},
    {"id": 2,  "nome": "Cono medio",        "tipo": "Cono",      "num_gusti": 3, "prezzo": 3.50,  "peso": 14},
    {"id": 3,  "nome": "Cono grande",       "tipo": "Cono",      "num_gusti": 4, "prezzo": 4.50,  "peso": 4},
    {"id": 4,  "nome": "Coppetta piccola",  "tipo": "Coppetta",  "num_gusti": 2, "prezzo": 3.00,  "peso": 16},
    {"id": 5,  "nome": "Coppetta media",    "tipo": "Coppetta",  "num_gusti": 3, "prezzo": 3.50,  "peso": 14},
    {"id": 6,  "nome": "Coppetta grande",   "tipo": "Coppetta",  "num_gusti": 4, "prezzo": 4.50,  "peso": 6},
    {"id": 7,  "nome": "Vaschetta 350 g",   "tipo": "Vaschetta", "num_gusti": 2, "grammi": 350,  "peso": 2},
    {"id": 8,  "nome": "Vaschetta 500 g",   "tipo": "Vaschetta", "num_gusti": 3, "grammi": 500,  "peso": 2},
    {"id": 9,  "nome": "Vaschetta 750 g",   "tipo": "Vaschetta", "num_gusti": 3, "grammi": 750,  "peso": 1},
    {"id": 10, "nome": "Vaschetta 1000 g",  "tipo": "Vaschetta", "num_gusti": 4, "grammi": 1000, "peso": 1},
    {"id": 11, "nome": "Vaschetta 1500 g",  "tipo": "Vaschetta", "num_gusti": 5, "grammi": 1500, "peso": 0.5},
    {"id": 12, "nome": "Frappè",            "tipo": "Bevanda",   "num_gusti": 1, "prezzo": 4.50,  "peso": 4},
    {"id": 13, "nome": "Affogato al caffè", "tipo": "Bevanda",   "num_gusti": 1, "prezzo": 4.00,  "peso": 3},
]

GUSTI = [
    # Creme
    {"id": 1,  "nome": "Nocciola",            "categoria": "Creme",  "dal_mese": 3, "al_mese": 10, "popolarita": 10},
    {"id": 2,  "nome": "Pistacchio",          "categoria": "Creme",  "dal_mese": 3, "al_mese": 10, "popolarita": 10},
    {"id": 3,  "nome": "Cioccolato fondente", "categoria": "Creme",  "dal_mese": 3, "al_mese": 10, "popolarita": 9},
    {"id": 4,  "nome": "Gianduja",            "categoria": "Creme",  "dal_mese": 3, "al_mese": 10, "popolarita": 8},
    {"id": 5,  "nome": "Stracciatella",       "categoria": "Creme",  "dal_mese": 3, "al_mese": 10, "popolarita": 9},
    {"id": 6,  "nome": "Fiordilatte",         "categoria": "Creme",  "dal_mese": 3, "al_mese": 10, "popolarita": 6},
    {"id": 7,  "nome": "Crema",               "categoria": "Creme",  "dal_mese": 3, "al_mese": 10, "popolarita": 5},
    {"id": 8,  "nome": "Caffè",               "categoria": "Creme",  "dal_mese": 3, "al_mese": 10, "popolarita": 4},
    {"id": 9,  "nome": "Bacio",               "categoria": "Creme",  "dal_mese": 3, "al_mese": 10, "popolarita": 5},
    {"id": 10, "nome": "Bicerin",             "categoria": "Creme",  "dal_mese": 3, "al_mese": 10, "popolarita": 3},
    {"id": 11, "nome": "Zabaione",            "categoria": "Creme",  "dal_mese": 9, "al_mese": 4,  "popolarita": 3},
    {"id": 12, "nome": "Marron glacé",        "categoria": "Creme",  "dal_mese": 9, "al_mese": 10, "popolarita": 4},
    # Frutta (sorbetti, vegani)
    {"id": 13, "nome": "Limone",              "categoria": "Frutta", "dal_mese": 3, "al_mese": 10, "popolarita": 7},
    {"id": 14, "nome": "Fragola",             "categoria": "Frutta", "dal_mese": 4, "al_mese": 9,  "popolarita": 7},
    {"id": 15, "nome": "Lampone",             "categoria": "Frutta", "dal_mese": 3, "al_mese": 10, "popolarita": 4},
    {"id": 16, "nome": "Frutti di bosco",     "categoria": "Frutta", "dal_mese": 3, "al_mese": 10, "popolarita": 5},
    {"id": 17, "nome": "Mango",               "categoria": "Frutta", "dal_mese": 3, "al_mese": 10, "popolarita": 5},
    {"id": 18, "nome": "Pesca",               "categoria": "Frutta", "dal_mese": 6, "al_mese": 9,  "popolarita": 6},
    {"id": 19, "nome": "Melone",              "categoria": "Frutta", "dal_mese": 6, "al_mese": 8,  "popolarita": 6},
    {"id": 20, "nome": "Anguria",             "categoria": "Frutta", "dal_mese": 7, "al_mese": 8,  "popolarita": 6},
    {"id": 21, "nome": "Fico",                "categoria": "Frutta", "dal_mese": 8, "al_mese": 10, "popolarita": 4},
]

MESI = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
        "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]


# ---------------------------------------------------------------
# Calendario
# ---------------------------------------------------------------

def pasqua(anno):
    """Data della Pasqua (algoritmo di Meeus)."""
    a, b, c = anno % 19, anno // 100, anno % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mese = (h + l - 7 * m + 114) // 31
    giorno = (h + l - 7 * m + 114) % 31 + 1
    return date(anno, mese, giorno)


def festivita(anno):
    """Festività italiane, più San Giovanni (patrono di Torino)."""
    p = pasqua(anno)
    return {
        date(anno, 1, 1): "Capodanno",
        date(anno, 1, 6): "Epifania",
        p: "Pasqua",
        p + timedelta(1): "Pasquetta",
        date(anno, 4, 25): "Festa della Liberazione",
        date(anno, 5, 1): "Festa dei lavoratori",
        date(anno, 6, 2): "Festa della Repubblica",
        date(anno, 6, 24): "San Giovanni",
        date(anno, 8, 15): "Ferragosto",
        date(anno, 11, 1): "Ognissanti",
        date(anno, 12, 8): "Immacolata",
        date(anno, 12, 25): "Natale",
        date(anno, 12, 26): "Santo Stefano",
    }


def e_aperto(giorno):
    return date(giorno.year, *APERTURA) <= giorno <= date(giorno.year, *CHIUSURA)


def ore_apertura(mese):
    """Ore in cui la gelateria serve clienti (ora di inizio di ogni fascia)."""
    if mese in (6, 7, 8):
        return range(12, 24)   # 12:00 - 24:00
    if mese in (5, 9):
        return range(12, 22)   # 12:00 - 22:00
    return range(13, 20)       # 13:00 - 20:00


def prezzo(id_prodotto, anno):
    p = next(p for p in PRODOTTI if p["id"] == id_prodotto)
    if "grammi" in p:
        valore = PREZZO_KG[anno] * p["grammi"] / 1000
    else:
        valore = p["prezzo"] * LISTINO_ANNO[anno]
    return round(valore, 1)   # arrotonda a 10 centesimi


# ---------------------------------------------------------------
# Meteo
# ---------------------------------------------------------------

def scarica_meteo(inizio, fine):
    parametri = {
        **TORINO,
        "start_date": inizio.isoformat(),
        "end_date": fine.isoformat(),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Europe/Rome",
    }
    url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(parametri)
    with urllib.request.urlopen(url, timeout=60) as risposta:
        return leggi_risposta_open_meteo(json.load(risposta))


def leggi_risposta_open_meteo(dati):
    giornaliero = dati["daily"]
    meteo = {}
    for i, giorno in enumerate(giornaliero["time"]):
        valori = (giornaliero["temperature_2m_max"][i],
                  giornaliero["temperature_2m_min"][i],
                  giornaliero["precipitation_sum"][i])
        if None in valori:
            continue
        meteo[date.fromisoformat(giorno)] = {
            "temp_max": valori[0], "temp_min": valori[1], "pioggia_mm": valori[2]}
    return meteo


def completa_meteo(meteo, giorni, rng):
    """Aggiunge la fonte e simula i giorni che mancano."""
    completo = {}
    anomalia = 0.0
    for giorno in giorni:
        if giorno in meteo:
            completo[giorno] = {**meteo[giorno], "fonte": "Open-Meteo"}
            continue
        # anomalia che cambia piano piano: ondate di caldo e giornate fresche
        anomalia = 0.7 * anomalia + rng.gauss(0, 2)
        piove = rng.random() < PROB_PIOGGIA[giorno.month]
        massima = TEMP_NORMALE[giorno.month] + anomalia - (4 if piove else 0)
        completo[giorno] = {
            "temp_max": round(massima, 1),
            "temp_min": round(massima - rng.uniform(8, 12), 1),
            "pioggia_mm": round(rng.expovariate(1 / 8), 1) if piove else 0.0,
            "fonte": "simulato",
        }
    return completo


# ---------------------------------------------------------------
# Domanda: quanti clienti arrivano
# ---------------------------------------------------------------

def fattore_meteo(mese, temp_max, pioggia_mm):
    caldo = min(max(1 + 0.05 * (temp_max - TEMP_NORMALE[mese]), 0.5), 1.5)
    if pioggia_mm < 1:
        pioggia = 1.0
    elif pioggia_mm < 5:
        pioggia = 0.8
    elif pioggia_mm < 15:
        pioggia = 0.6
    else:
        pioggia = 0.45
    return caldo * pioggia


def scontrini_attesi(giorno, meteo, festivi):
    fattore = FATTORE_GIORNO[giorno.weekday()]
    if giorno in festivi:
        fattore = max(fattore, 1.4)
    if festivi.get(giorno) == "San Giovanni":
        fattore = 1.7   # fuochi d'artificio sul Po: serata piena
    if giorno.month == 8 and 8 <= giorno.day <= 25:
        fattore *= 0.62  # Torino si svuota per le ferie
    return (BASE_MESE[giorno.month] * fattore * CRESCITA_ANNO[giorno.year]
            * fattore_meteo(giorno.month, meteo["temp_max"], meteo["pioggia_mm"]))


def peso_ora(ora, temp_max):
    curva = {12: .5, 13: .7, 14: .9, 15: 1.2, 16: 1.5, 17: 1.5, 18: 1.2,
             19: .7, 20: .8, 21: 1.3, 22: 1.2, 23: .7}
    peso = curva[ora]
    if temp_max >= 30 and ora >= 21:
        peso *= 1.4   # nelle serate afose si esce dopo cena
    return peso


# ---------------------------------------------------------------
# Cosa compra ogni cliente
# ---------------------------------------------------------------

def gusti_disponibili(mese):
    def disponibile(g):
        if g["dal_mese"] <= g["al_mese"]:
            return g["dal_mese"] <= mese <= g["al_mese"]
        return mese >= g["dal_mese"] or mese <= g["al_mese"]   # es. settembre-aprile
    return [g for g in GUSTI if disponibile(g)]


def pesi_gusti(gusti, anno, temp_max):
    pesi = []
    for g in gusti:
        peso = g["popolarita"]
        if g["categoria"] == "Frutta":
            peso *= min(max(1 + 0.04 * (temp_max - 22), 0.5), 1.6)
        else:
            peso *= min(max(1 - 0.02 * (temp_max - 22), 0.7), 1.3)
        if g["nome"] == "Pistacchio":
            peso *= 1 + 0.15 * (anno - 2024)   # gusto in crescita
        pesi.append(peso)
    return pesi


def pesi_prodotti(festivo, ora, temp_max):
    pesi = []
    for p in PRODOTTI:
        peso = p["peso"]
        if p["tipo"] == "Vaschetta":
            peso *= 2.5 if festivo else 1
            peso *= 1.5 if ora >= 20 else 1
        if p["nome"] == "Frappè" and temp_max >= 28:
            peso *= 2
        if p["nome"] == "Affogato al caffè" and temp_max < 20:
            peso *= 2
        pesi.append(peso)
    return pesi


def scegli_senza_ripetere(rng, elementi, pesi, quanti):
    elementi, pesi, scelti = list(elementi), list(pesi), []
    for _ in range(quanti):
        i = rng.choices(range(len(elementi)), weights=pesi)[0]
        scelti.append(elementi.pop(i))
        pesi.pop(i)
    return scelti


def genera_vendite(giorni, meteo, rng):
    vendite, gusti_venduti = [], []
    id_scontrino = id_riga = 0
    for giorno in giorni:
        anno = giorno.year
        festivi = festivita(anno)
        m = meteo[giorno]
        festivo = giorno in festivi or giorno.weekday() == 6
        ore = list(ore_apertura(giorno.month))
        pesi_ore = [peso_ora(o, m["temp_max"]) for o in ore]
        disponibili = gusti_disponibili(giorno.month)
        pesi_g = pesi_gusti(disponibili, anno, m["temp_max"])
        n_scontrini = round(scontrini_attesi(giorno, m, festivi) * rng.lognormvariate(0, 0.1))
        pezzi_possibili = [50, 30, 13, 7] if giorno.weekday() >= 5 else [58, 27, 10, 5]

        orari = sorted((rng.choices(ore, weights=pesi_ore)[0], rng.randrange(3600))
                       for _ in range(n_scontrini))
        for ora, secondi in orari:
            id_scontrino += 1
            orario = f"{ora:02d}:{secondi // 60:02d}:{secondi % 60:02d}"
            pezzi = rng.choices([1, 2, 3, 4], weights=pezzi_possibili)[0]
            prodotti = rng.choices(PRODOTTI, weights=pesi_prodotti(festivo, ora, m["temp_max"]), k=pezzi)
            totale = sum(prezzo(p["id"], anno) for p in prodotti)
            quota = min(max(QUOTA_CARTA[anno] + 0.03 * (totale - 5), 0.1), 0.95)
            pagamento = "Carta" if rng.random() < quota else "Contanti"
            for p in prodotti:
                id_riga += 1
                vendite.append({
                    "id_riga": id_riga, "id_scontrino": id_scontrino,
                    "data": giorno.isoformat(), "ora": orario,
                    "id_prodotto": p["id"], "importo": f"{prezzo(p['id'], anno):.2f}",
                    "pagamento": pagamento,
                })
                for g in scegli_senza_ripetere(rng, disponibili, pesi_g, p["num_gusti"]):
                    gusti_venduti.append({"id_riga": id_riga, "id_gusto": g["id"]})
    return vendite, gusti_venduti


# ---------------------------------------------------------------
# Scrittura dei file
# ---------------------------------------------------------------

def calendario(meteo):
    righe = []
    giorno = date(ANNI[0], 1, 1)
    while giorno <= date(ANNI[-1], 12, 31):
        m = meteo.get(giorno, {})
        righe.append({
            "data": giorno.isoformat(), "anno": giorno.year, "mese": giorno.month,
            "nome_mese": MESI[giorno.month], "giorno_settimana": giorno.isoweekday(),
            "nome_giorno": GIORNI[giorno.weekday()],
            "weekend": int(giorno.weekday() >= 5),
            "festivita": festivita(giorno.year).get(giorno, ""),
            "aperto": int(e_aperto(giorno)),
            "temp_max": m.get("temp_max", ""), "temp_min": m.get("temp_min", ""),
            "pioggia_mm": m.get("pioggia_mm", ""), "fonte_meteo": m.get("fonte", ""),
        })
        giorno += timedelta(1)
    return righe


def scrivi_csv(nome, righe):
    CARTELLA.mkdir(exist_ok=True)
    with open(CARTELLA / f"{nome}.csv", "w", newline="", encoding="utf-8") as f:
        scrittore = csv.DictWriter(f, fieldnames=list(righe[0]))
        scrittore.writeheader()
        scrittore.writerows(righe)
    print(f"  {nome}.csv: {len(righe):,} righe".replace(",", "."))


def main():
    rng = random.Random(SEME)
    primo, ultimo = date(ANNI[0], 1, 1), date(ANNI[-1], 12, 31)
    giorni = [primo + timedelta(i) for i in range((ultimo - primo).days + 1)]
    giorni = [g for g in giorni if e_aperto(g)]

    meteo_reale = {}
    if "--meteo-simulato" not in sys.argv:
        print("Scarico il meteo di Torino da Open-Meteo...")
        try:
            meteo_reale = scarica_meteo(giorni[0], giorni[-1])
        except Exception as errore:
            print(f"  Download non riuscito ({errore}): uso il meteo simulato.")
    meteo = completa_meteo(meteo_reale, giorni, rng)
    simulati = sum(m["fonte"] == "simulato" for m in meteo.values())
    if simulati:
        print(f"  Giorni con meteo simulato: {simulati} su {len(giorni)}")

    print("Genero le vendite...")
    vendite, gusti_venduti = genera_vendite(giorni, meteo, rng)

    print(f"Scrivo i file in {CARTELLA}")
    scrivi_csv("calendario", calendario(meteo))
    scrivi_csv("prodotti", [{k: p.get(k, "") for k in ("id", "nome", "tipo", "num_gusti", "grammi")}
                            for p in PRODOTTI])
    scrivi_csv("gusti", [{k: g[k] for k in ("id", "nome", "categoria", "dal_mese", "al_mese")}
                         | {"vegano": int(g["categoria"] == "Frutta")} for g in GUSTI])
    scrivi_csv("vendite", vendite)
    scrivi_csv("gusti_venduti", gusti_venduti)
    print("Fatto.")


if __name__ == "__main__":
    main()
