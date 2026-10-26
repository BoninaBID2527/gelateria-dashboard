"""
Crea la dashboard interattiva (dashboard.html) a partire dai CSV della cartella "dati".

Uso:
    python genera_dati.py      # prima: crea i CSV
    python crea_dashboard.py   # poi: crea dashboard.html

Il file prodotto è una sola pagina: si apre con un doppio clic, funziona senza
internet e si può pubblicare così com'è (GitHub Pages, Netlify, il tuo sito).
Serve solo Python 3.9 o successivo, nessuna libreria da installare.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

QUI = Path(__file__).parent


def leggi_csv(percorso):
    with open(percorso, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def aggrega(cartella):
    """Riduce centinaia di migliaia di righe ai pochi numeri che servono ai grafici."""
    cartella = Path(cartella)
    calendario = {r["data"]: r for r in leggi_csv(cartella / "calendario.csv")}
    prodotti = {int(r["id"]): r for r in leggi_csv(cartella / "prodotti.csv")}
    gusti = {int(r["id"]): r for r in leggi_csv(cartella / "gusti.csv")}

    giorni = {}
    scontrini_visti = set()
    orari = defaultdict(lambda: [[0] * 24 for _ in range(7)])
    prodotti_anno = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))
    riga_periodo = {}

    for r in leggi_csv(cartella / "vendite.csv"):
        data = r["data"]
        cal = calendario[data]
        anno, mese = int(cal["anno"]), int(cal["mese"])
        giorno_sett = int(cal["giorno_settimana"])
        importo = float(r["importo"])
        prodotto = prodotti[int(r["id_prodotto"])]

        g = giorni.get(data)
        if g is None:
            g = giorni[data] = {
                "data": data, "anno": anno, "mese": mese, "gs": giorno_sett,
                "inc": 0.0, "scon": 0, "art": 0, "kg": 0.0, "carta": 0,
                "tmax": float(cal["temp_max"]), "pioggia": float(cal["pioggia_mm"]),
                "fest": cal["festivita"],
            }
        g["inc"] += importo
        g["art"] += 1
        if prodotto["grammi"]:
            g["kg"] += int(prodotto["grammi"]) / 1000

        if r["id_scontrino"] not in scontrini_visti:   # uno scontrino ha più righe
            scontrini_visti.add(r["id_scontrino"])
            g["scon"] += 1
            if r["pagamento"] == "Carta":
                g["carta"] += 1
            orari[anno][giorno_sett - 1][int(r["ora"][:2])] += 1

        agg = prodotti_anno[anno][int(r["id_prodotto"])]
        agg[0] += 1
        agg[1] += importo
        riga_periodo[int(r["id_riga"])] = (anno, mese)

    conteggi = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for r in leggi_csv(cartella / "gusti_venduti.csv"):
        anno, mese = riga_periodo[int(r["id_riga"])]
        conteggi[anno][mese][gusti[int(r["id_gusto"])]["nome"]] += 1

    lista = sorted(giorni.values(), key=lambda g: g["data"])
    for g in lista:
        g["inc"] = round(g["inc"], 2)
        g["kg"] = round(g["kg"], 3)

    fonti = defaultdict(int)
    for g in lista:
        fonti[calendario[g["data"]]["fonte_meteo"]] += 1

    return {
        "anni": sorted({g["anno"] for g in lista}),
        "giorni": lista,
        "orari": {a: m for a, m in orari.items()},
        "gusti": {
            "categorie": {g["nome"]: g["categoria"] for g in gusti.values()},
            "conteggi": {a: {m: dict(n) for m, n in mesi.items()} for a, mesi in conteggi.items()},
        },
        "prodotti": {
            a: [{"nome": prodotti[i]["nome"], "tipo": prodotti[i]["tipo"],
                 "grammi": int(prodotti[i]["grammi"] or 0),
                 "righe": righe, "incasso": round(inc, 2)}
                for i, (righe, inc) in sorted(per_prodotto.items())]
            for a, per_prodotto in prodotti_anno.items()
        },
        "meteo_fonti": dict(fonti),
    }


def crea_html(dati, modello):
    testo = json.dumps(dati, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return modello.replace("/*DATI*/null", testo)


def main():
    print("Leggo i CSV e calcolo i totali...")
    dati = aggrega(QUI / "dati")
    modello = (QUI / "modello_dashboard.html").read_text(encoding="utf-8")
    destinazione = QUI / "dashboard.html"
    destinazione.write_text(crea_html(dati, modello), encoding="utf-8")
    print(f"Fatto: {destinazione} ({destinazione.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
