# Extraction golden report

Faithful (2019) features recomputed in Python and compared, value by value, with the
2019 feature table. Aggregates only: no participant appears in this report.

- Options: `faithful_12m_correct`
- Profiles compared: 323
- Overall exact-match rate: 70.5% (target: at least 95%)
- Gender label agreement with 2019: 99.4% of 344 profiles

## By family

| Family | Columns | Exact-match rate | Median correlation |
|---|---:|---:|---:|
| messages | 17 | 22.5% | 0.954 |
| message_hours | 23 | 16.7% | 0.982 |
| message_weekdays | 7 | 16.3% | 0.972 |
| wall_hours | 23 | 24.1% | 0.975 |
| wall_weekdays | 7 | 22.6% | 0.982 |
| wall | 12 | 62.3% | 0.997 |
| dictionary | 440 | 79.5% | 0.969 |

## Worst 25 columns

| Feature | 2019 column | Exact | r | Max abs diff |
|---|---|---:|---:|---:|
| `msg_chars_total` | `msg_nchar_stats.total_nchar` | 0.0% | 0.864 | 7.7e+06 |
| `msg_chars_mean` | `msg_nchar_stats.nchar_per_text.Mean` | 0.0% | 0.939 | 52.3 |
| `dict_owner_personal_tu` | `user_personal.tu` | 0.9% | 0.908 | 4.12e+04 |
| `dict_others_personal_tu` | `others_personal.tu` | 0.9% | 0.961 | 3.53e+04 |
| `msg_chars_q3` | `msg_nchar_stats.nchar_per_text.3rd.Qu.` | 5.6% | 0.932 | 55.8 |
| `msg_hour_19` | `msg_freq_ore.19` | 8.0% | 0.971 | 0.0832 |
| `msg_hour_16` | `msg_freq_ore.16` | 8.7% | 0.989 | 0.0647 |
| `msg_hour_20` | `msg_freq_ore.20` | 8.7% | 0.985 | 0.0369 |
| `msg_hour_22` | `msg_freq_ore.22` | 8.7% | 0.983 | 0.077 |
| `msg_hour_23` | `msg_freq_ore.23` | 8.7% | 0.982 | 0.081 |
| `dict_others_personal_bello` | `others_personal.bello` | 8.7% | 0.973 | 774 |
| `msg_hour_17` | `msg_freq_ore.17` | 9.0% | 0.952 | 0.112 |
| `dict_others_personal_virgole_punti` | `others_personal.virgole_punti` | 9.0% | 0.97 | 8.92e+03 |
| `msg_per_contact` | `msg_mess_medi_friend` | 9.3% | 0.988 | 327 |
| `msg_hour_13` | `msg_freq_ore.13` | 9.3% | 0.986 | 0.0423 |
| `msg_hour_14` | `msg_freq_ore.14` | 9.3% | 0.982 | 0.0732 |
| `msg_hour_11` | `msg_freq_ore.11` | 9.6% | 0.978 | 0.104 |
| `msg_hour_18` | `msg_freq_ore.18` | 9.6% | 0.977 | 0.0942 |
| `msg_hour_21` | `msg_freq_ore.21` | 9.6% | 0.98 | 0.0664 |
| `msg_hour_10` | `msg_freq_ore.10` | 9.9% | 0.972 | 0.0503 |
| `msg_hour_12` | `msg_freq_ore.12` | 9.9% | 0.989 | 0.0364 |
| `msg_hour_15` | `msg_freq_ore.15` | 9.9% | 0.972 | 0.0602 |
| `dict_owner_personal_si` | `user_personal.si` | 9.9% | 0.972 | 1.69e+03 |
| `msg_hour_09` | `msg_freq_ore.09` | 10.2% | 0.981 | 0.0385 |
| `dict_owner_personal_bello` | `user_personal.bello` | 10.5% | 0.969 | 393 |

## Known gaps

See docs/extraction-golden-gaps.md.
