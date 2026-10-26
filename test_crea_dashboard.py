import csv
import json
import tempfile
import unittest
from pathlib import Path

import crea_dashboard as c

CALENDARIO = [
    {"data": "2025-07-01", "anno": 2025, "mese": 7, "giorno_settimana": 2, "festivita": "",
     "aperto": 1, "temp_max": 30.0, "pioggia_mm": 0.0, "fonte_meteo": "Open-Meteo"},
    {"data": "2025-07-02", "anno": 2025, "mese": 7, "giorno_settimana": 3, "festivita": "",
     "aperto": 1, "temp_max": 22.5, "pioggia_mm": 6.0, "fonte_meteo": "simulato"},
]
VENDITE = [
    (1, 1, "2025-07-01", "16:10:00", 1, "3.00", "Carta"),
    (2, 1, "2025-07-01", "16:10:00", 2, "3.50", "Carta"),
    (3, 2, "2025-07-01", "21:30:00", 3, "22.00", "Contanti"),
    (4, 3, "2025-07-02", "16:45:00", 1, "3.00", "Contanti"),
]
PRODOTTI = [(1, "Cono piccolo", "Cono", 2, ""), (2, "Cono medio", "Cono", 3, ""),
            (3, "Vaschetta 1000 g", "Vaschetta", 4, 1000)]
GUSTI = [(1, "Nocciola", "Creme", 3, 10, 0), (2, "Limone", "Frutta", 3, 10, 1)]
GUSTI_VENDUTI = [(1, 1), (1, 2), (2, 1), (3, 1), (4, 2)]


def scrivi(cartella, nome, intestazione, righe):
    with open(Path(cartella) / f"{nome}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(intestazione)
        for r in righe:
            w.writerow(r if not isinstance(r, dict) else [r[k] for k in intestazione])


class TestAggrega(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = cls.tmp.name
        scrivi(d, "calendario", list(CALENDARIO[0]), CALENDARIO)
        scrivi(d, "vendite", ["id_riga", "id_scontrino", "data", "ora", "id_prodotto", "importo", "pagamento"], VENDITE)
        scrivi(d, "prodotti", ["id", "nome", "tipo", "num_gusti", "grammi"], PRODOTTI)
        scrivi(d, "gusti", ["id", "nome", "categoria", "dal_mese", "al_mese", "vegano"], GUSTI)
        scrivi(d, "gusti_venduti", ["id_riga", "id_gusto"], GUSTI_VENDUTI)
        cls.dati = c.aggrega(d)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_totali_del_primo_giorno(self):
        g = self.dati["giorni"][0]
        self.assertEqual(g["data"], "2025-07-01")
        self.assertEqual(g["inc"], 28.50)
        self.assertEqual(g["scon"], 2)       # due scontrini, non tre righe
        self.assertEqual(g["art"], 3)
        self.assertEqual(g["kg"], 1.0)
        self.assertEqual(g["carta"], 1)
        self.assertEqual(g["gs"], 2)
        self.assertEqual((g["tmax"], g["pioggia"]), (30.0, 0.0))

    def test_secondo_giorno(self):
        g = self.dati["giorni"][1]
        self.assertEqual((g["inc"], g["scon"], g["kg"], g["carta"]), (3.0, 1, 0, 0))
        self.assertEqual(g["pioggia"], 6.0)

    def test_scontrini_per_giorno_e_ora(self):
        m = self.dati["orari"][2025]
        self.assertEqual(m[1][16], 1)   # martedì alle 16
        self.assertEqual(m[1][21], 1)   # martedì alle 21
        self.assertEqual(m[2][16], 1)   # mercoledì alle 16
        self.assertEqual(sum(map(sum, m)), 3)

    def test_gusti_per_mese(self):
        conteggi = self.dati["gusti"]["conteggi"][2025][7]
        self.assertEqual(conteggi["Nocciola"], 3)
        self.assertEqual(conteggi["Limone"], 2)
        self.assertEqual(self.dati["gusti"]["categorie"]["Limone"], "Frutta")

    def test_prodotti_per_anno(self):
        per_nome = {p["nome"]: p for p in self.dati["prodotti"][2025]}
        self.assertEqual(per_nome["Vaschetta 1000 g"]["righe"], 1)
        self.assertEqual(per_nome["Vaschetta 1000 g"]["incasso"], 22.0)
        self.assertEqual(per_nome["Cono piccolo"]["righe"], 2)

    def test_fonti_del_meteo(self):
        self.assertEqual(self.dati["meteo_fonti"], {"Open-Meteo": 1, "simulato": 1})
        self.assertEqual(self.dati["anni"], [2025])


class TestHtml(unittest.TestCase):
    def test_i_dati_finiscono_nella_pagina_e_il_segnaposto_sparisce(self):
        modello = "<script>const D = /*DATI*/null;</script>"
        html = c.crea_html({"a": "</script>"}, modello)
        self.assertNotIn("/*DATI*/", html)
        self.assertNotIn("</script>\"", html)          # il testo pericoloso è neutralizzato
        self.assertIn('"a"', html)


if __name__ == "__main__":
    unittest.main()
