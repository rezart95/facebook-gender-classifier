"""Hand-written Italian chat lines for fake profiles. They trigger the 2019 dictionary
(question and exclamation marks, emoticons, laughter, "non lo so", "boh", ...) and Unicode
emoji. Every line is invented; none comes from a real export.
"""

from __future__ import annotations

PHRASES: tuple[str, ...] = (
    "Ciao! Come stai? :)",
    "Bene dai, tu?",
    "Non lo so... boh",
    "ahahah che ridere",
    "Ti voglio bene <3",
    "Che palle, domani ho l'esame :(",
    "ok perfetto, a dopo ;)",
    "Siiii finalmente!!",
    "Nooo dai, non ci credo",
    "forzaaa \N{FLEXED BICEPS}",
    "secondo me hai ragione",
    "scusa, mi dispiace tanto",
    "sono un po' in ansia per lunedì",
    "che bello! \N{SMILING FACE WITH HEART-SHAPED EYES}",
    "lol \N{FACE WITH TEARS OF JOY}",
    "sempre la solita storia...",
    "mai più, giuro",
    "dimmi tu quando sei libera",
    "uffa, che noia zzz",
    "wow, impossibile!",
    "io ci sono, voi?",
    "capisco, ti ascolto",
    "sicuro? mi sembra strano",
    "aiuto, sono nel panico",
    "si si, va bene",
    "no, niente di che",
    "assolutamente sì!",
    "ok \N{THUMBS UP SIGN}",
    "buonanotte \N{SLEEPING FACE}",
    "xD troppo forte",
)
WALL_ACTIONS: tuple[str, ...] = (
    "{owner} ha condiviso un link.",
    "{owner} ha aggiornato il suo stato.",
    "{friend} ha scritto sul tuo diario.",
    "{owner} e {friend} hanno stretto amicizia.",
    "A {owner} piace Pizzeria da Gino.",
    "{owner} ha aggiornato la sua immagine del profilo.",
    "{owner} ha condiviso la foto di {friend}.",
)
EVENT_NAMES: tuple[str, ...] = (
    "Festa di compleanno",
    "Concerto in piazza",
    "Cena di classe",
    "Torneo di calcetto",
)
EVENT_REPLIES: tuple[str, ...] = (
    "Partecipazione confermata",
    "Forse",
    "Partecipazione rifiutata",
    "Nessuna risposta",
)
RELATIONSHIP_LABELS: tuple[str | None, ...] = (
    "Single",
    "Impegnata/o",
    "Fidanzata/o ufficialmente",
    None,
)
