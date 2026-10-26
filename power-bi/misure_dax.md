# Dashboard gelateria: misure DAX

Come si usa: in Power BI, vista Report o Dati, *Nuova misura* (o *Nuova colonna*), poi incolla una formula alla volta.
Consiglio: crea una tabella vuota "Misure" (*Inserisci dati*) e tienici dentro tutte le misure, così sono in ordine.

## Prima di tutto: ordinamento

- `calendario[nome_mese]` → *Ordina per colonna* → `mese`
- `calendario[nome_giorno]` → *Ordina per colonna* → `giorno_settimana`
- `calendario` → *Contrassegna come tabella di date* → colonna `data`

## Misure di base

```dax
Incasso = SUM(vendite[importo])
```
```dax
Scontrini = DISTINCTCOUNT(vendite[id_scontrino])
```
```dax
Scontrino medio = DIVIDE([Incasso], [Scontrini])
```
```dax
Articoli venduti = COUNTROWS(vendite)
```
```dax
Incasso medio giornaliero = AVERAGEX(VALUES(calendario[data]), [Incasso])
```

## Confronto con l'anno prima

```dax
Incasso anno prec = CALCULATE([Incasso], SAMEPERIODLASTYEAR(calendario[data]))
```
```dax
Variazione % = DIVIDE([Incasso] - [Incasso anno prec], [Incasso anno prec])
```
Formato: percentuale. Per il 2024 resta vuota, ed è normale: non c'è un anno prima.

## Prodotti e pagamenti

```dax
Kg in vaschetta = DIVIDE(SUMX(vendite, RELATED(prodotti[grammi])), 1000)
```
```dax
Incasso vaschette = CALCULATE([Incasso], prodotti[tipo] = "Vaschetta")
```
```dax
Quota incasso vaschette = DIVIDE([Incasso vaschette], [Incasso])
```
```dax
Quota carta = DIVIDE(CALCULATE([Scontrini], vendite[pagamento] = "Carta"), [Scontrini])
```

## Gusti

```dax
Gusti serviti = COUNTROWS(gusti_venduti)
```
```dax
Quota frutta = DIVIDE(CALCULATE([Gusti serviti], gusti[categoria] = "Frutta"), [Gusti serviti])
```

## Colonne calcolate

In `calendario` (i numeri davanti servono solo a ordinare le fasce nei grafici):

```dax
Fascia pioggia =
IF(
    ISBLANK(calendario[pioggia_mm]), BLANK(),
    SWITCH(
        TRUE(),
        calendario[pioggia_mm] < 1, "1 Asciutto",
        calendario[pioggia_mm] < 5, "2 Pioggia debole",
        calendario[pioggia_mm] < 15, "3 Pioggia",
        "4 Temporale"
    )
)
```
```dax
Fascia temperatura =
IF(
    ISBLANK(calendario[temp_max]), BLANK(),
    SWITCH(
        TRUE(),
        calendario[temp_max] < 15, "1 Sotto 15°",
        calendario[temp_max] < 20, "2 Da 15 a 20°",
        calendario[temp_max] < 25, "3 Da 20 a 25°",
        calendario[temp_max] < 30, "4 Da 25 a 30°",
        "5 Sopra 30°"
    )
)
```

In `vendite`:

```dax
Ora = HOUR(vendite[ora])
```
Se la colonna `ora` non viene riconosciuta come ora, in Power Query impostala sul tipo *Ora*.

## Come controllare che i numeri siano giusti

- `Articoli venduti` totale = numero di righe di `vendite.csv` meno l'intestazione.
- `Incasso` totale = somma della colonna `importo` calcolata in Excel sullo stesso file.
- Se l'incasso è 100 volte più grande o piccolo, il problema sono i decimali: ricarica `importo` con impostazioni locali *Inglese (Stati Uniti)*.
