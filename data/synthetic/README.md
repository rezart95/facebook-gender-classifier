# Synthetic data

Every row in this folder is synthetic. No row belongs to, or was copied from, a participant,
and the gender labels are synthetic too.

- `participants.csv`: one synthetic person per row (`S001`, `S002`, ...): wave, gender, age band,
  relationship category, and whether the person has messages and survey scores.
- `features.parquet`: the same people, one column per feature of `catalogue/features.yaml`
  (the faithful 2019 features and the survey scales).

How it was made (`fbgc synth-data`, fixed seed):

- Only aggregate statistics of the anonymized data were used: per feature, the 1–99% quantiles in
  1% steps, clipped further for features with few values so that the stored tails sit at or
  inside the 5th smallest and 5th largest value (the k = 5 of the anonymization); features with
  fewer than 20 observed values are left out; and the missing rate;
  jointly, the Spearman correlations of the features and gender.
  Wave, age band and relationship were drawn from their overall shares.
- Rows were sampled from a Gaussian copula. Counts were rounded to whole numbers, other values kept
  to 4 decimals, and missing values put back at the real rates.
- Correlations were shrunk toward zero by 0.25 (`--shrinkage 0.25`) so that the privacy check passes.
- Privacy check: the 5th percentile of the distance from each synthetic row to its closest real row
  is at least the 5th percentile of the distance between real rows, and the real rows must be
  distinct (that percentile is above 0), or the data is not written.

Columns are drawn jointly but each row is new, so identities that hold in the real data (for
example, the 24 hour shares of a person summing to 1) do not hold here. Use this data to try the
code and the website, not to draw conclusions about the study.
