# facebook-gender-classifier

A remake of my 2019 bachelor thesis in Statistics (University of Padova, relatore Prof. Livio Finos):
classifying the gender of Facebook users from their activity and personality scales, using data from
the DPSS study by Marino, Finos et al. (2017).

Status: part 1a, foundation and faithful extraction. See `docs/extraction-golden-report.md` for how
the recomputed features compare with the 2019 table.

## Privacy

The original Facebook exports contain private messages, including those of friends who never consented.
They never enter this repository. The pipeline runs only on the owner's machine, against a private folder
outside the repo, and this repository holds code, invented test profiles and aggregate reports only.

## Credits

- Marino, Finos, Vieno, Lenzi, Spada (2017), *Objective Facebook behaviour: Differences between problematic
  and non-problematic users*, Computers in Human Behavior 73, 541–546.
- myFBr (Finos, Marino, Meneghetti, Righetto, Rebecchi) and TextWiller (Finos et al.), both GPL ≥ 2.

## Licence

GPL-3.0-or-later.

## Running the extraction (owner's machine only)

```bash
export FBGC_RAW_DIR=/path/outside/the/repo/with/wave1-and-wave2
export FBGC_PRIVATE_DIR=/another/path/outside/the/repo
uv run fbgc inventory
uv run fbgc extract
```

Outputs keyed by real folder codes stay in `FBGC_PRIVATE_DIR`. Only aggregate reports
(`docs/extraction-*.md`) are committed. See `docs/extraction-golden-report.md` for how the
faithful features compare with the 2019 table.

## Anonymization (owner's machine only)

The anonymized tables use pseudonymous IDs keyed by a secret of at least 32 characters. The
secret never leaves the machine and is never written to any file.

```bash
# Paste the secret (32+ characters) when asked: it is not echoed and stays out of shell history.
read -rs FBGC_ID_SECRET && export FBGC_ID_SECRET
uv run fbgc anonymize --survey /path/outside/the/repo/datiScale_w1w2.Rdata
```

This writes `participants.parquet` and `features_long.parquet` under
`$FBGC_PRIVATE_DIR/anonymized/` and prints aggregate counts only.

## Database (local)

```bash
docker compose -f infra/docker-compose.yml up -d
export DATABASE_URL=postgresql+psycopg://fbgc:fbgc-local-only@127.0.0.1:5433/fbgc
uv run alembic -c core/alembic.ini upgrade head
uv run fbgc load --synthetic   # or --private, on the owner's machine and a local database only
```

`fbgc load` replaces the catalogue, the participants, their feature values and the demo traces in
one transaction, so it can be run again safely.
