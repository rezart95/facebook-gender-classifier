# Extraction golden report

Faithful (2019) features recomputed in Python and compared, value by value, with the
2019 feature table. Aggregates only: no participant appears in this report.

- Options: `faithful_12m_correct`
- Profiles compared: 323
- Overall exact-match rate (near-exact): 70.4%
- Overall within 0.05%: 70.5%
- Non-dictionary exact-match rate: 25.7%
- Non-dictionary within 0.05%: 26.3%
- Gender label agreement with 2019: 100.0% of 342 profiles

## By family

| Family | Columns | Exact-match rate | Within 0.05% | Median correlation |
|---|---:|---:|---:|---:|
| messages | 17 | 21.1% | 22.5% | 0.954 |
| message_hours | 23 | 16.0% | 16.7% | 0.982 |
| message_weekdays | 7 | 15.2% | 16.3% | 0.972 |
| wall_hours | 23 | 24.1% | 24.1% | 0.975 |
| wall_weekdays | 7 | 22.3% | 22.6% | 0.982 |
| wall | 12 | 62.3% | 62.3% | 0.997 |
| dictionary | 440 | 79.5% | 79.5% | 0.969 |

## Worst 25 columns

| Feature | 2019 column | Exact | Close | r | Max abs diff |
|---|---|---:|---:|---:|---:|
| `msg_chars_total` | `msg_nchar_stats.total_nchar` | 0.0% | 0.0% | 0.864 | 7.7e+06 |
| `msg_chars_mean` | `msg_nchar_stats.nchar_per_text.Mean` | 0.0% | 0.0% | 0.939 | 52.3 |
| `dict_owner_personal_tu` | `user_personal.tu` | 0.9% | 0.9% | 0.908 | 4.12e+04 |
| `dict_others_personal_tu` | `others_personal.tu` | 0.9% | 0.9% | 0.961 | 3.53e+04 |
| `msg_chars_q3` | `msg_nchar_stats.nchar_per_text.3rd.Qu.` | 5.6% | 5.6% | 0.932 | 55.8 |
| `msg_hour_19` | `msg_freq_ore.19` | 7.7% | 8.0% | 0.971 | 0.0832 |
| `msg_hour_13` | `msg_freq_ore.13` | 8.0% | 9.3% | 0.986 | 0.0423 |
| `msg_hour_16` | `msg_freq_ore.16` | 8.0% | 8.7% | 0.989 | 0.0647 |
| `msg_hour_22` | `msg_freq_ore.22` | 8.0% | 8.7% | 0.983 | 0.077 |
| `msg_hour_23` | `msg_freq_ore.23` | 8.0% | 8.7% | 0.982 | 0.081 |
| `msg_contact_gini` | `msg_Gini_freq_user` | 8.4% | 18.3% | 0.988 | 0.0771 |
| `msg_hour_10` | `msg_freq_ore.10` | 8.4% | 9.9% | 0.972 | 0.0503 |
| `msg_hour_17` | `msg_freq_ore.17` | 8.4% | 9.0% | 0.952 | 0.112 |
| `msg_hour_18` | `msg_freq_ore.18` | 8.4% | 9.6% | 0.977 | 0.0942 |
| `msg_hour_20` | `msg_freq_ore.20` | 8.4% | 8.7% | 0.985 | 0.0369 |
| `msg_hour_21` | `msg_freq_ore.21` | 8.4% | 9.6% | 0.98 | 0.0664 |
| `msg_per_contact` | `msg_mess_medi_friend` | 8.7% | 9.3% | 0.988 | 327 |
| `msg_hour_11` | `msg_freq_ore.11` | 8.7% | 9.6% | 0.978 | 0.104 |
| `msg_hour_14` | `msg_freq_ore.14` | 8.7% | 9.3% | 0.982 | 0.0732 |
| `dict_others_personal_bello` | `others_personal.bello` | 8.7% | 8.7% | 0.973 | 774 |
| `msg_hour_12` | `msg_freq_ore.12` | 9.0% | 9.9% | 0.989 | 0.0364 |
| `msg_hour_15` | `msg_freq_ore.15` | 9.0% | 9.9% | 0.972 | 0.0602 |
| `dict_others_personal_virgole_punti` | `others_personal.virgole_punti` | 9.0% | 9.0% | 0.97 | 8.92e+03 |
| `msg_hour_09` | `msg_freq_ore.09` | 9.6% | 10.2% | 0.981 | 0.0385 |
| `msg_hour_00` | `msg_freq_ore.00` | 9.9% | 10.8% | 0.981 | 0.0948 |

## Known gaps

Maintained by hand in `docs/extraction-golden-gaps.md`, from private diagnostics (aggregates only).
`fbgc golden` copies this file into the report verbatim.

**Target revised (owner decision, 2026-11-24).** The original target was ≥ 95% exact.

- **Overall:** the port reaches 70.4% near-exact, or 70.5% within 0.05%.
- **Non-dictionary columns:** 25.7% near-exact. These 89 columns are the ones not dominated by sparse
  dictionary counts.
- **Correlation:** the median correlation is 0.95–0.997 in every family.

The remaining differences come from quirks of the 2019 R package (myFBr) that the Python port deliberately
does not copy. The "then" model in part 2 uses the original 2019 table, so the thesis numbers still
reproduce exactly.

Exports with no readable download date are excluded under the 12-month window. Three such exports exist,
on top of three in unsupported UI languages.

- **Observation window: 12 months, not 6.**
  - The theses describe "the last 6 months". The data shows the 2019 counts cover about one year before
    each download: the median inferred start is 364 days before download in both waves.
  - The port uses `--window 12m`.
  - Message and wall counts still match exactly for only about 50 of 323 profiles, whatever edge rule is
    used: aware or naive time, 365 days or 12 months, date-level bounds.
  - A fixed calendar start per wave (16 April 2014 and 27 October 2014) fits slightly better, at 69 of 323.
    This suggests 2019 used per-wave dates. It was not adopted, because those dates are undocumented.
  - Effect: low exact rates, despite r ≈ 0.95–0.98, in `messages`, `message_hours`, `message_weekdays`,
    `wall_hours` and `wall_weekdays`.
- **Text length and punctuation on pages that are not valid XML** (248 of the 323 compared profiles).
  - 2019 texts are about 3 characters longer per message.
  - 2019 counts about 21 more `,` `;` `.` per profile.
  - This is consistent with myFBr's fallback path serialising the HTML, with entities such as `&#232;`,
    instead of reading the text. The port reads the text.
  - Effect: `msg_chars_*`, `dict_*_virgole_punti` and other punctuation-sensitive counts.
- **Contact counts on XML-valid pages** (75 profiles).
  - 2019's `msg_n_user` is always higher, by a median of 74.
  - This is likely a sender/timestamp misalignment in myFBr's XML path.
  - Effect: `msg_n_contacts`, `msg_per_contact`, the top-3 shares, the Gini index and the contact gender
    shares.
- **Dictionary words.**
  - The 31 published myFBr patterns are ported byte-exact (cross-checked against the R source).
  - The 79 other words were rebuilt, because their 2019 regexes were never published.
  - Calibration keeps the best of four variants per word. 23 of 79 reach ≥ 95% exact (see
    `extraction-dictionary-calibration.md`).
  - Closing the rest needs the original word list from the 2019 project.
- **Weekday labels.**
  - The 2019 data used correct weekday labels.
  - The variant reproducing lubridate's Sunday-first relabelling scores r ≈ −0.07, against 0.97 for
    correct.
- **Length statistics are unrounded.**
  - 321 of 325 2019 mean lengths carry more than 4 significant digits.
  - So 2019 ran on R ≥ 3.4, whose `summary()` does not round. The port matches.
- **Gender label.** The 2019 and recomputed labels agree for 100% of the 342 profiles where both are present.
