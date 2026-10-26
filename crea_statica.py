"""
Crea rappresentazione-statica.html: una fotografia dell'app, senza JavaScript.

Prende le pagine dalla dashboard vera (dashboard.html), così grafica e numeri sono
sempre identici all'app, e le mette una sotto l'altra in un unico file che si apre
ovunque, anche dentro un'email o in un'anteprima.

Uso:
    python crea_dashboard.py   # prima: crea dashboard.html
    python crea_statica.py     # poi: crea rappresentazione-statica.html

Serve Playwright (solo per questo script, non per il resto del progetto):
    pip install playwright
    playwright install chromium
"""

import re
from pathlib import Path

QUI = Path(__file__).parent


def estrai_css(modello):
    """Restituisce lo stile completo e le sole variabili del tema scuro."""
    stile = re.search(r"<style>(.*?)</style>", modello, re.S).group(1)
    scuro = re.search(r'\[data-tema="scuro"\] \{(.*?)\n  \}', stile, re.S).group(1)
    return stile, scuro


CSS_STATICO = """
  html { scroll-behavior: smooth; }
  main { gap: 0; max-width: 1260px; }
  section.pagina { display: grid; gap: 1.4rem; scroll-margin-top: 1rem; padding-bottom: 2.75rem; }
  section.pagina + section.pagina { border-top: 1px dashed var(--bordo); padding-top: 2.75rem; }
  a.voce { text-decoration: none; }
  .alto { position: static; }
  .seg button { pointer-events: none; }

  /* voce di menu evidenziata: la pagina a cui punta il link, senza script */
  html:not(:has(:target)) a.voce[href="#panoramica"],
  html:has(#panoramica:target) a.voce[href="#panoramica"],
  html:has(#meteo:target) a.voce[href="#meteo"],
  html:has(#gusti:target) a.voce[href="#gusti"],
  html:has(#orari:target) a.voce[href="#orari"],
  html:has(#info:target) a.voce[href="#info"] {
    background: var(--voce-attiva); color: var(--su-voce-attiva); font-weight: 650;
    box-shadow: 0 4px 12px -4px rgba(150, 60, 85, .35);
  }

  @media (max-width: 1000px) {
    .lato, .lato:not(.aperto) { position: sticky; top: 0; height: auto; width: auto; margin: 0; transform: none;
      border-radius: 0 0 22px 22px; box-shadow: 0 12px 26px -18px rgba(150, 50, 80, .55); }
    .lato::before, .lato::after, .lato-piede, .marchio small, .menu h6, .menu hr { display: none; }
    .marchio { padding: .8rem 1rem .3rem; }
    .menu { display: flex; overflow-x: auto; gap: .3rem; padding: .2rem .75rem .8rem; }
    .voce { width: auto; flex: none; white-space: nowrap; }
    section.pagina { scroll-margin-top: 8rem; }
  }
"""


def componi_html(parti, modello):
    css, scuro = estrai_css(modello)
    nav = "".join(
        f'<a class="voce" href="#{k}">{icona}{nome}</a>'
        for k, nome, icona in parti["menu"] if k != "info"
    )
    info = next((m for m in parti["menu"] if m[0] == "info"), None)
    menu = f'<h6>Analisi</h6>{nav}' + (
        f'<hr><h6>Risorse</h6><a class="voce" href="#info">{info[2]}{info[1]}</a>' if info else "")
    sezioni = "".join(
        f'<section class="pagina" id="{p["k"]}">'
        f'<div class="testa-pagina"><div class="icona-pagina">{p["icona"]}</div>'
        f'<div><h1>{p["nome"]}</h1><p>{p["sotto"]}</p></div></div>{p["html"]}</section>'
        for p in parti["pagine"]
    )
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gelateria · Dashboard vendite (anteprima statica)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{css}{CSS_STATICO}
  @media (prefers-color-scheme: dark) {{ :root {{{scuro}}} }}
</style>
</head>
<body>
<div class="app">
  <aside class="lato" aria-label="Menu">
    {parti["marchio"]}
    <nav class="menu">{menu}</nav>
    <div class="lato-piede">{parti["piede"]}</div>
  </aside>
  <div class="corpo">
    <header class="alto">
      <span class="chip periodo"><i></i><span>{parti["periodo"]} · anteprima statica</span></span>
      <div class="spazio"></div>
      <div class="seg" role="group" aria-label="Anno">{parti["seg"]}</div>
    </header>
    <main>{sezioni}</main>
  </div>
</div>
</body>
</html>
"""


def cattura(percorso_dashboard):
    """Apre la dashboard vera in un browser e ne legge tutte le pagine (tutti gli anni)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        pagina = browser.new_page(viewport={"width": 1440, "height": 900})
        pagina.goto(Path(percorso_dashboard).resolve().as_uri())
        pagina.wait_for_selector("#pagina .kpi, #pagina .pannello")
        parti = pagina.evaluate("""() => {
          anno = "tutti";
          const pagine = Object.entries(PAGINE).map(([k, P]) => ({
            k, nome: P.nome, sotto: P.sotto, icona: ico(P.icona, 26), html: P.fn() }));
          const menu = Object.entries(PAGINE).map(([k, P]) => [k, P.nome, ico(P.icona, 19)]);
          return {
            pagine, menu,
            marchio: document.querySelector(".marchio").outerHTML,
            piede: document.querySelector("#piede").innerHTML,
            periodo: document.querySelector("#periodo").textContent.replace(/ · dati simulati$/, "") + " · dati simulati",
            seg: ["tutti", ...D.anni].map((a) => `<button type="button" tabindex="-1" aria-pressed="${a === "tutti"}">${a === "tutti" ? "Tutti" : a}</button>`).join(""),
          };
        }""")
        browser.close()
    return parti


def main():
    modello = (QUI / "modello_dashboard.html").read_text(encoding="utf-8")
    parti = cattura(QUI / "dashboard.html")
    destinazione = QUI / "rappresentazione-statica.html"
    destinazione.write_text(componi_html(parti, modello), encoding="utf-8")
    print(f"Fatto: {destinazione} ({destinazione.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
