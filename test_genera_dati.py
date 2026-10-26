import random
import unittest
from collections import Counter
from datetime import date, timedelta

import genera_dati as g


class TestCalendario(unittest.TestCase):
    def test_pasqua_nelle_date_giuste(self):
        self.assertEqual(g.pasqua(2024), date(2024, 3, 31))
        self.assertEqual(g.pasqua(2025), date(2025, 4, 20))
        self.assertEqual(g.pasqua(2026), date(2026, 4, 5))

    def test_festivita_include_pasquetta_e_san_giovanni(self):
        feste = g.festivita(2025)
        self.assertEqual(feste.get(date(2025, 4, 21)), "Pasquetta")
        self.assertIn(date(2025, 6, 24), feste)

    def test_stagione_dal_1_marzo_al_15_ottobre(self):
        self.assertTrue(g.e_aperto(date(2025, 3, 1)))
        self.assertFalse(g.e_aperto(date(2025, 2, 28)))
        self.assertTrue(g.e_aperto(date(2025, 10, 15)))
        self.assertFalse(g.e_aperto(date(2025, 10, 16)))

    def test_listino_attuale_con_i_prezzi_della_gelateria(self):
        prezzi = {p["nome"]: g.prezzo(p["id"], 2026) for p in g.PRODOTTI}
        self.assertEqual(prezzi["Cono piccolo"], 3.00)
        self.assertEqual(prezzi["Cono medio"], 3.50)
        self.assertEqual(prezzi["Cono grande"], 4.50)

    def test_vaschette_a_22_euro_al_kg(self):
        prezzi = {p["nome"]: g.prezzo(p["id"], 2026) for p in g.PRODOTTI}
        self.assertEqual(prezzi["Vaschetta 350 g"], 7.70)
        self.assertEqual(prezzi["Vaschetta 500 g"], 11.00)
        self.assertEqual(prezzi["Vaschetta 750 g"], 16.50)
        self.assertEqual(prezzi["Vaschetta 1000 g"], 22.00)
        self.assertEqual(prezzi["Vaschetta 1500 g"], 33.00)

    def test_vaschette_a_prezzi_tondi_negli_anni_passati(self):
        kg = next(p["id"] for p in g.PRODOTTI if p["nome"] == "Vaschetta 1000 g")
        self.assertEqual(g.prezzo(kg, 2024), 20.00)
        self.assertEqual(g.prezzo(kg, 2025), 21.00)

    def test_negli_anni_precedenti_i_prezzi_erano_piu_bassi(self):
        self.assertLess(g.prezzo(1, 2024), g.prezzo(1, 2025))
        self.assertLess(g.prezzo(1, 2025), g.prezzo(1, 2026))


class TestDomanda(unittest.TestCase):
    METEO = {"temp_max": 30.0, "temp_min": 20.0, "pioggia_mm": 0.0}

    def test_pioggia_riduce_le_vendite(self):
        self.assertLess(g.fattore_meteo(7, 30, 10), g.fattore_meteo(7, 30, 0))

    def test_caldo_aumenta_le_vendite(self):
        self.assertGreater(g.fattore_meteo(6, 32, 0), g.fattore_meteo(6, 24, 0))

    def test_sabato_piu_affollato_del_martedi(self):
        feste = g.festivita(2025)
        sabato = g.scontrini_attesi(date(2025, 6, 7), self.METEO, feste)
        martedi = g.scontrini_attesi(date(2025, 6, 10), self.METEO, feste)
        self.assertGreater(sabato, martedi)

    def test_calo_di_meta_agosto(self):
        feste = g.festivita(2025)
        inizio = g.scontrini_attesi(date(2025, 8, 5), self.METEO, feste)
        meta = g.scontrini_attesi(date(2025, 8, 19), self.METEO, feste)
        self.assertLess(meta, inizio)


class TestGusti(unittest.TestCase):
    def test_anguria_solo_in_estate(self):
        self.assertNotIn("Anguria", [x["nome"] for x in g.gusti_disponibili(3)])
        self.assertIn("Anguria", [x["nome"] for x in g.gusti_disponibili(7)])


class TestMeteo(unittest.TestCase):
    def test_legge_open_meteo_saltando_i_valori_mancanti(self):
        risposta = {"daily": {
            "time": ["2025-07-01", "2025-07-02"],
            "temperature_2m_max": [31.2, None],
            "temperature_2m_min": [19.8, None],
            "precipitation_sum": [0.4, None],
        }}
        meteo = g.leggi_risposta_open_meteo(risposta)
        self.assertEqual(list(meteo), [date(2025, 7, 1)])
        self.assertEqual(meteo[date(2025, 7, 1)]["temp_max"], 31.2)

    def test_completa_i_giorni_mancanti_con_meteo_simulato(self):
        d1, d2 = date(2025, 7, 1), date(2025, 7, 2)
        reale = {d1: {"temp_max": 31.2, "temp_min": 19.8, "pioggia_mm": 0.4}}
        meteo = g.completa_meteo(reale, [d1, d2], random.Random(0))
        self.assertEqual(meteo[d1]["fonte"], "Open-Meteo")
        self.assertEqual(meteo[d2]["fonte"], "simulato")
        self.assertIn("temp_max", meteo[d2])


class TestVendite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = random.Random(1)
        giorni = [date(2025, 3, 3) + timedelta(i) for i in range(7)]
        giorni += [date(2025, 7, 14) + timedelta(i) for i in range(7)]
        cls.meteo = g.completa_meteo({}, giorni, rng)
        cls.vendite, cls.gusti = g.genera_vendite(giorni, cls.meteo, rng)

    def test_genera_vendite(self):
        self.assertGreater(len(self.vendite), 500)

    def test_ogni_prodotto_ha_il_numero_giusto_di_gusti(self):
        per_riga = Counter(x["id_riga"] for x in self.gusti)
        richiesti = {p["id"]: p["num_gusti"] for p in g.PRODOTTI}
        for v in self.vendite:
            self.assertEqual(per_riga[v["id_riga"]], richiesti[v["id_prodotto"]])

    def test_i_gusti_venduti_sono_disponibili_nel_mese(self):
        mese_riga = {v["id_riga"]: int(v["data"][5:7]) for v in self.vendite}
        for x in self.gusti:
            disponibili = {gu["id"] for gu in g.gusti_disponibili(mese_riga[x["id_riga"]])}
            self.assertIn(x["id_gusto"], disponibili)

    def test_gli_orari_sono_dentro_l_apertura(self):
        for v in self.vendite:
            self.assertIn(int(v["ora"][:2]), g.ore_apertura(int(v["data"][5:7])))

    def test_id_riga_unici(self):
        ids = [v["id_riga"] for v in self.vendite]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
