Written by hand from private diagnostics (aggregates only). Re-running `fbgc golden` regenerates the
tables above and replaces this section, so keep a copy.

**Target revised (owner decision, 2026-11-24).** The original target was ≥ 95% exact. The port reaches
70.5% exact, with median correlations of 0.95–0.997 in every family. The remaining differences come from
quirks of the 2019 R package (myFBr) that the Python port deliberately does not copy. The "then" model in
part 2 uses the original 2019 table, so the thesis numbers still reproduce exactly.

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
- **Gender label.** The 2019 and recomputed labels agree for 99.4% of 344 profiles.
