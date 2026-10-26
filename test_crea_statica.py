import unittest

import crea_statica as s

MODELLO = """<html><head><style>
  :root { --bg: #FFF; color-scheme: light; }
  [data-tema="scuro"] {
    --bg: #111;
    color-scheme: dark;
  }
  .kpi { color: red; }
</style></head><body></body></html>"""

PARTI = {
    "css": "", "marchio": '<div class="marchio">Gelateria</div>', "piede": "230.226 prodotti",
    "periodo": "1 mar 2024 – 15 ott 2026 · dati simulati", "seg": '<button aria-pressed="true">Tutti</button>',
    "menu": [("panoramica", "Panoramica", "<svg/>"), ("meteo", "Meteo", "<svg/>"), ("info", "Informazioni", "<svg/>")],
    "pagine": [
        {"k": "panoramica", "nome": "Panoramica", "sotto": "In sintesi", "icona": "<svg/>", "html": "<div class='kpi'>1</div>"},
        {"k": "meteo", "nome": "Meteo", "sotto": "Pioggia e caldo", "icona": "<svg/>", "html": "<div class='kpi'>2</div>"},
        {"k": "info", "nome": "Informazioni", "sotto": "Dati", "icona": "<svg/>", "html": "<div class='kpi'>3</div>"},
    ],
}


class TestEstraiCss(unittest.TestCase):
    def test_separa_lo_stile_dalle_variabili_del_tema_scuro(self):
        css, scuro = s.estrai_css(MODELLO)
        self.assertIn(".kpi", css)
        self.assertIn("--bg: #111", scuro)
        self.assertNotIn("[data-tema", scuro)


class TestComponi(unittest.TestCase):
    def setUp(self):
        self.html = s.componi_html(PARTI, MODELLO)

    def test_non_contiene_javascript(self):
        self.assertNotIn("<script", self.html.lower())
        self.assertNotIn("onclick", self.html.lower())

    def test_ogni_pagina_ha_la_sua_sezione_e_il_suo_link(self):
        for k in ("panoramica", "meteo", "info"):
            self.assertIn(f'id="{k}"', self.html)
            self.assertIn(f'href="#{k}"', self.html)

    def test_le_pagine_sono_nell_ordine_giusto(self):
        self.assertLess(self.html.index('id="panoramica"'), self.html.index('id="meteo"'))
        self.assertLess(self.html.index('id="meteo"'), self.html.index('id="info"'))

    def test_il_tema_scuro_segue_il_telefono_senza_script(self):
        self.assertIn("prefers-color-scheme: dark", self.html)
        self.assertIn("--bg: #111", self.html)

    def test_dichiara_di_essere_un_anteprima_statica(self):
        self.assertIn("anteprima statica", self.html)

    def test_il_testo_dentro_le_sezioni_viene_conservato(self):
        self.assertIn("<div class='kpi'>2</div>", self.html)
        self.assertIn("Pioggia e caldo", self.html)


if __name__ == "__main__":
    unittest.main()
