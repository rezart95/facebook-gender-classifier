# facebook-gender-classifier

A remake of my 2019 bachelor thesis in Statistics (University of Padova, relatore Prof. Livio Finos):
classifying the gender of Facebook users from their activity and personality scales, using data from
the DPSS study by Marino, Finos et al. (2017).

Status: part 1a, foundation and faithful extraction. See
`docs/superpowers/specs/2026-11-23-facebook-gender-classifier-design.md`.

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
