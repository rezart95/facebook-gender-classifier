# Data files for the faithful (2019) features

- `textwiller_first_names.csv`: the `vocabolarioNomiPropri` first-name list from TextWiller
  (Livio Finos and contributors, https://github.com/livioivil/TextWiller, GPL ≥ 2), exported with
  `tools/export_textwiller_names.py`. Generic first names and organisation markers; no participant data.
- `dictionary_words.yaml`: the 79 dictionary words of the 2019 feature table. Rebuilt in 2026 because
  the original regexes were never published; `fbgc calibrate-dictionary` picks each word's variant.
