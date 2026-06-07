# John Jumper — Key Publications and Canonical Works

Sources:
- https://www.nature.com/articles/s41586-021-03819-2 (AlphaFold 2, Nature 2021)
- https://www.nature.com/articles/s41586-024-07487-w (AlphaFold 3, Nature 2024)
- https://www.nature.com/articles/d41586-024-01385-x (Nature news piece on AlphaFold 3)
- https://www.nature.com/articles/s41586-024-08416-7 (AlphaFold 3 addendum)
- https://arxiv.org/abs/2409.08022 (AlphaProteo arXiv, Sep 2024)
- https://scholar.google.com/citations?user=a5goOh8AAAAJ&hl=en (Google Scholar)

## Defining paper: AlphaFold 2 (Nature 2021)

- **Title:** "Highly accurate protein structure prediction with AlphaFold"
- **Authors:** Jumper J., Evans R., Pritzel A., Green T., Figurnov M., Ronneberger O., Tunyasuvunakool K., Bates R., Žídek A., Potapenko A. et al.
- **Venue:** Nature, July 15, 2021
- **DOI:** 10.1038/s41586-021-03819-2
- **One-liner:** Solved the 50-year-old protein structure prediction problem. Median backbone error of 0.96 Å on CASP14 free-modelling targets — equivalent to experimental crystallography accuracy.
- **Why it matters:** Jumper is first author. This is the Nobel-cited paper. Architecture: Evoformer (MSA + pair representation, alternating attention), Structure Module, iterative refinement, AlphaFold-confidence (pLDDT, PAE) outputs. The companion AlphaFold Protein Structure Database (with EMBL-EBI) became the most-used scientific database in biology within 3 years.

## Generalisation paper: AlphaFold 3 (Nature 2024)

- **Title:** "Accurate structure prediction of biomolecular interactions with AlphaFold 3"
- **Authors:** Abramson J., Adler J., Dunger J., ... Jumper J. et al. (Jumper as senior author / corresponding author block)
- **Venue:** Nature, May 8, 2024
- **DOI:** 10.1038/s41586-024-07487-w
- **One-liner:** Generalises AlphaFold 2 from proteins-only to proteins + DNA + RNA + small-molecule ligands + ions + modified residues. Switches from Evoformer + structure module to a diffusion-based architecture. 50%+ accuracy improvement on protein-ligand and protein-nucleic-acid interactions.
- **Release pattern:** Initially server-only via AlphaFold Server (free for academic use, capped). Code and weights released for non-commercial use Nov 2024. Publicly available with non-commercial restriction Feb 2025.

## AlphaProteo (arXiv 2024)

- **Title:** "De novo design of high-affinity protein binders with AlphaProteo"
- **Venue:** arXiv:2409.08022, September 2024
- **One-liner:** Generative protein-binder design. 3× to 300× better binding affinity than prior methods on tested targets (e.g. VEGF-A, BHRF1, TrkA). Wet-lab validated.
- **Why it matters:** This is the "AlphaFold for design" successor — moves from prediction (given a sequence, what's the structure?) to design (given a target, what's a binder sequence?). The category that maps directly onto drug discovery.

## AlphaMissense (Science 2023)

- **Title:** "Accurate proteome-wide missense variant effect prediction with AlphaMissense"
- **Venue:** Science, September 2023
- **One-liner:** Predicts pathogenicity of missense variants across the human proteome. Classifies 71M of 216M possible variants as likely-pathogenic or likely-benign with high agreement to clinical labels.

## AlphaGenome (announced 2025)

- Full genomic interpretation. Predicts gene regulation, splicing, chromatin features from DNA sequence.

## Selected co-authored works

- Senior at Google DeepMind on the broader AlphaFold-Multimer and AlphaFold-latest model lineage.
- PhD-era work on machine-learning coarse-grained protein dynamics (Sosnick / Freed lab, UChicago) — methodological seed of the AlphaFold approach.
- Brief D.E. Shaw Research period (~2011-2012) on long-timescale MD simulation pipelines.

## Citation profile

Google Scholar h-index and citation count are dominated by the 2021 AlphaFold paper, which is one of the most-cited biology papers of the 21st century (>30,000 citations within four years of publication). This single paper makes him one of the most-cited mid-career researchers in computational biology.
