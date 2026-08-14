# Third-party licences — `coco-diagram`

This skill is adapted from [diagram-design](https://github.com/cathrynlavery/diagram-design) by Cathryn Lavery, MIT, upstream v2.3.2. That upstream MIT notice is reproduced verbatim in [`LICENSE`](LICENSE) beside this file.

Upstream in turn bundles icon artwork from the third-party sources below, and that artwork ships here too — the icon path data lives inline in [`references/primitive-icons.md`](references/primitive-icons.md) and [`assets/icons.html`](assets/icons.html). Each source is redistributed under its own licence, reproduced by reference below. This file exists so those obligations travel with the copy rather than resting on inline mentions alone.

## Tabler Icons

- **Licence:** MIT
- **Upstream:** https://github.com/tabler/tabler-icons
- **Licence text:** https://github.com/tabler/tabler-icons/blob/main/LICENSE
- **Used for:** the stroked icons in `references/primitive-icons.md` and `assets/icons.html` — the Compute, People, Network, Data, Kubernetes, Action and DevOps categories, plus the stroked brand outlines for Docker, Terraform, AWS, Azure and GitHub.

## Simple Icons

- **Licence:** CC0 1.0 Universal (public-domain dedication — no attribution obligation, recorded for completeness)
- **Upstream:** https://github.com/simple-icons/simple-icons
- **Licence text:** https://github.com/simple-icons/simple-icons/blob/develop/LICENSE.md
- **Used for:** the filled brand silhouettes — Kubernetes, Google Cloud, PostgreSQL, Nginx, Gitea, Keycloak, MinIO, Apache NiFi, Apache Airflow, Trino, Apache Superset, Jupyter, Python and R.

## log-z/logos

- **Licence:** MIT
- **Upstream:** https://github.com/log-z/logos/tree/main/website-logos
- **Licence text:** https://github.com/log-z/logos/blob/main/LICENSE
- **Used for:** the filled brand silhouettes that neither Simple Icons nor Tabler carries — currently MySQL, Redis and StarRocks.

## Devicon

- **Licence:** MIT
- **Upstream:** https://github.com/devicons/devicon
- **Licence text:** https://github.com/devicons/devicon/blob/master/LICENSE
- **Used for:** the RStudio and SPSS icons. Note that upstream's icon build tooling (`scripts/vendor/icons/`) is **not** vendored into this skill; only the rendered icon paths are.

## One-off sourced icons

The SAS mark originates from [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:SAS_logo_horiz.svg) and is in the public domain. The Stata mark originates from the IcePanel Technology Icons collection published via techicons.dev; **upstream declares no licence for it**, so its provenance is recorded here rather than asserted as licensed. If that ambiguity matters for your use, drop the Stata icon.

## Trademarks

Brand logos remain the trademarks of their respective owners. Their inclusion in this icon set is for documentation and illustrative use only, and does not imply endorsement, sponsorship, or affiliation.
