#!/usr/bin/env python3
"""
Deterministic Synthetic Genomic & OMOP Phenotype Data Generator.
Produces synthetic multi-sample VCF files and corresponding OMOP CDM tables.

STRICT PHI SAFEGUARD:
This script produces strictly synthetic coordinates and simulated variant calls.
No real human genomic data is used or emitted.
"""

import os
import random
import csv
from datetime import date

# Set deterministic seed for reproducible lab benchmarking
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

SAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SAMPLES_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

SAMPLE_IDS = [f"sample_{i:03d}" for i in range(1, 11)]

# Simulated genomic loci across Chr1, Chr2, Chr7, Chr13, Chr17, Chr19, Chr21, Chr22 (GRCh38 coordinates)
SYNTHETIC_LOCI = [
    # chr, start, end, ref, alt, gene_symbol, simulated_pathogenicity, target_phenotype_concept
    ("chr21", 25891796, 25891796, "A", "G", "APP", "PATHOGENIC", 43530807), # 43530807: Early onset Alzheimer disease
    ("chr21", 25891820, 25891820, "C", "T", "APP", "BENIGN", None),
    ("chr21", 25892010, 25892010, "G", "A", "APP", "BENIGN", None),
    ("chr21", 33039603, 33039603, "G", "A", "SOD1", "PATHOGENIC", 374919),   # 374919: Amyotrophic lateral sclerosis
    ("chr21", 33039650, 33039650, "T", "C", "SOD1", "VUS", None),
    ("chr21", 33040100, 33040100, "C", "T", "SOD1", "BENIGN", None),
    ("chr21", 41480000, 41480000, "C", "A", "RUNX1", "BENIGN", None),
    ("chr21", 41482500, 41482500, "T", "C", "RUNX1", "VUS", None),
    ("chr22", 17071756, 17071756, "T", "C", "BCR", "BENIGN", None),
    ("chr22", 17073200, 17073200, "G", "A", "BCR", "BENIGN", None),
    ("chr22", 23223844, 23223844, "G", "T", "SMARCB1", "PATHOGENIC", 4180790), # 4180790: Malignant rhabdoid tumor
    ("chr22", 23225100, 23225100, "A", "G", "SMARCB1", "BENIGN", None),
    ("chr22", 29697660, 29697660, "A", "C", "NF2", "PATHOGENIC", 4216183),   # 4216183: Neurofibromatosis type 2
    ("chr22", 29697700, 29697700, "G", "A", "NF2", "BENIGN", None),
    ("chr22", 37680000, 37680000, "C", "T", "LARGE1", "BENIGN", None),
    ("chr22", 28688400, 28688400, "T", "C", "CHEK2", "PATHOGENIC", 4329847),
    # Chr1 - MTHFR, GBA1, PCSK9, CFH
    ("chr1", 11796321, 11796321, "C", "T", "MTHFR", "VUS", None),
    ("chr1", 11796450, 11796450, "A", "C", "MTHFR", "BENIGN", None),
    ("chr1", 155235843, 155235843, "T", "C", "GBA1", "PATHOGENIC", 4048039), # Gaucher disease
    ("chr1", 155236100, 155236100, "G", "A", "GBA1", "BENIGN", None),
    ("chr1", 55039981, 55039981, "G", "A", "PCSK9", "PATHOGENIC", 313217),   # Hypercholesterolemia
    ("chr1", 55041200, 55041200, "C", "T", "PCSK9", "BENIGN", None),
    ("chr1", 196659237, 196659237, "T", "C", "CFH", "PATHOGENIC", 37311061),
    # Chr2 - MSH2, MSH6, MYH9
    ("chr2", 47414434, 47414434, "A", "T", "MSH2", "PATHOGENIC", 4312442), # Lynch syndrome
    ("chr2", 47416000, 47416000, "C", "T", "MSH2", "BENIGN", None),
    ("chr2", 47783151, 47783151, "G", "C", "MSH6", "PATHOGENIC", 4312442),
    ("chr2", 36441582, 36441582, "A", "G", "MYH9", "BENIGN", None),
    # Chr7 - CFTR (Cystic Fibrosis), EGFR, BRAF
    ("chr7", 117559590, 117559590, "C", "T", "CFTR", "PATHOGENIC", 4144111), # Cystic fibrosis
    ("chr7", 117559800, 117559800, "G", "A", "CFTR", "BENIGN", None),
    ("chr7", 55181378, 55181378, "C", "T", "EGFR", "PATHOGENIC", 4178818),  # Lung cancer
    ("chr7", 55182500, 55182500, "A", "G", "EGFR", "BENIGN", None),
    ("chr7", 140753336, 140753336, "A", "T", "BRAF", "PATHOGENIC", 4112853), # Melanoma V600E
    # Chr13 - BRCA2, RB1, GJB2
    ("chr13", 32338148, 32338148, "C", "T", "BRCA2", "PATHOGENIC", 4112853), # Breast/ovarian cancer
    ("chr13", 32338780, 32338780, "G", "A", "BRCA2", "BENIGN", None),
    ("chr13", 48303750, 48303750, "C", "T", "RB1", "PATHOGENIC", 4180790),
    ("chr13", 20188981, 20188981, "G", "A", "GJB2", "PATHOGENIC", 378419),
    # Chr17 - BRCA1, TP53, ERBB2
    ("chr17", 43044295, 43044295, "A", "G", "BRCA1", "PATHOGENIC", 4112853), # Breast/ovarian cancer
    ("chr17", 43045802, 43045802, "T", "C", "BRCA1", "BENIGN", None),
    ("chr17", 7673802, 7673802, "C", "T", "TP53", "PATHOGENIC", 4112853),   # Li-Fraumeni syndrome
    ("chr17", 7674220, 7674220, "G", "A", "TP53", "BENIGN", None),
    ("chr17", 39724731, 39724731, "C", "T", "ERBB2", "VUS", None),
    # Chr19 - APOE (Alzheimer's risk), LDLR (Hypercholesterolemia)
    ("chr19", 44908684, 44908684, "T", "C", "APOE", "PATHOGENIC", 43530807), # APOE-e4
    ("chr19", 44908822, 44908822, "C", "T", "APOE", "BENIGN", None),
    ("chr19", 11100236, 11100236, "G", "A", "LDLR", "PATHOGENIC", 313217),   # Hypercholesterolemia
    ("chr19", 15174351, 15174351, "C", "T", "NOTCH3", "PATHOGENIC", 4144111), # CADASIL
]

def generate_vcf(output_path: str, samples: list[str]):
    """Generates a multi-sample VCF 4.2 file with synthetic calls."""
    header = [
        "##fileformat=VCFv4.2",
        f"##fileDate={date.today().strftime('%Y%m%d')}",
        "##source=HLSSyntheticCohortGenerator",
        "##reference=GRCh38",
        '##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">',
        '##INFO=<ID=GENE,Number=1,Type=String,Description="Simulated Gene Symbol">',
        '##INFO=<ID=CLNSIG,Number=1,Type=String,Description="Simulated Clinical Significance">',
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
        '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read Depth">',
        '##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype Quality">',
        '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allelic Depths for Ref and Alt">',
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + "\t".join(samples)
    ]

    records = []
    for chrom, start, _, ref, alt, gene, clnsig, _ in SYNTHETIC_LOCI:
        # Pre-assign genotypes per sample:
        # For pathogenic variants, ensure specific carriers:
        # APP 25891796: carrier samples 002, 005, 008 (heterozygous 0/1)
        # SOD1 33039603: carrier samples 003, 007 (heterozygous 0/1)
        # SMARCB1 23223844: carrier sample 004 (heterozygous 0/1)
        # NF2 29697660: carrier sample 001 (homozygous 1/1), 009 (heterozygous 0/1)
        sample_calls = []
        alt_count = 0
        total_alleles = len(samples) * 2

        for sample in samples:
            s_num = int(sample.split("_")[1])
            gt = "0/0"
            if chrom == "chr21" and start == 25891796 and s_num in [2, 5, 8]:
                gt = "0/1"
            elif chrom == "chr21" and start == 33039603 and s_num in [3, 7]:
                gt = "0/1"
            elif chrom == "chr22" and start == 23223844 and s_num in [4]:
                gt = "0/1"
            elif chrom == "chr22" and start == 29697660 and s_num == 1:
                gt = "1/1"
            elif chrom == "chr22" and start == 29697660 and s_num == 9:
                gt = "0/1"
            elif clnsig == "BENIGN":
                # Random distribution for common variants
                prob = random.random()
                if prob < 0.20:
                    gt = "1/1"
                elif prob < 0.55:
                    gt = "0/1"
                else:
                    gt = "0/0"
            else:
                # Occasional random rare call
                if random.random() < 0.10:
                    gt = "0/1"

            if gt == "0/1":
                alt_count += 1
                dp = random.randint(28, 65)
                gq = random.randint(70, 99)
                ad_ref = dp // 2 + random.randint(-3, 3)
                ad_alt = dp - ad_ref
            elif gt == "1/1":
                alt_count += 2
                dp = random.randint(30, 70)
                gq = 99
                ad_ref = random.randint(0, 2)
                ad_alt = dp - ad_ref
            else:
                dp = random.randint(25, 55)
                gq = random.randint(60, 99)
                ad_ref = dp
                ad_alt = 0

            sample_calls.append(f"{gt}:{dp}:{gq}:{ad_ref},{ad_alt}")

        af = alt_count / total_alleles if total_alleles > 0 else 0.0
        info_field = f"AF={af:.4f};GENE={gene};CLNSIG={clnsig}"
        qual = "99.0"
        filter_field = "PASS"
        var_id = f"syn_{chrom}_{start}_{ref}_{alt}"

        line = f"{chrom}\t{start}\t{var_id}\t{ref}\t{alt}\t{qual}\t{filter_field}\t{info_field}\tGT:DP:GQ:AD\t" + "\t".join(sample_calls)
        records.append(line)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n")
        f.write("\n".join(records) + "\n")
    print(f"Generated synthetic VCF: {output_path} ({len(records)} loci, {len(samples)} samples)")

def generate_omop_tables(output_dir: str, samples: list[str]):
    """Generates synthetic OMOP CDM person and condition_occurrence CSV tables."""
    person_path = os.path.join(output_dir, "person.csv")
    condition_path = os.path.join(output_dir, "condition_occurrence.csv")

    persons = []
    conditions = []
    cond_id_counter = 1001

    # Deterministic mapping for clinical phenotype
    for sample in samples:
        s_num = int(sample.split("_")[1])
        person_id = 10000 + s_num
        gender_concept_id = 8507 if s_num % 2 == 0 else 8532 # 8507: Male, 8532: Female
        year_of_birth = 1960 + (s_num * 3) % 40

        persons.append({
            "person_id": person_id,
            "gender_concept_id": gender_concept_id,
            "year_of_birth": year_of_birth,
            "month_of_birth": 6,
            "day_of_birth": 15,
            "race_concept_id": 8527,
            "ethnicity_concept_id": 38003564,
            "sample_id": sample
        })

        # Associate carriers with OMOP conditions:
        # s_num in [2, 5, 8] -> APP variant carrier -> Alzheimer's (43530807)
        if s_num in [2, 5, 8]:
            conditions.append({
                "condition_occurrence_id": cond_id_counter,
                "person_id": person_id,
                "condition_concept_id": 43530807,
                "condition_start_date": f"{year_of_birth + 52}-03-12",
                "condition_type_concept_id": 32817 # EHR clinical observation
            })
            cond_id_counter += 1

        # s_num in [3, 7] -> SOD1 variant carrier -> ALS (374919)
        if s_num in [3, 7]:
            conditions.append({
                "condition_occurrence_id": cond_id_counter,
                "person_id": person_id,
                "condition_concept_id": 374919,
                "condition_start_date": f"{year_of_birth + 48}-08-20",
                "condition_type_concept_id": 32817
            })
            cond_id_counter += 1

        # s_num == 1 -> NF2 carrier -> Neurofibromatosis (4216183)
        if s_num == 1:
            conditions.append({
                "condition_occurrence_id": cond_id_counter,
                "person_id": person_id,
                "condition_concept_id": 4216183,
                "condition_start_date": f"{year_of_birth + 25}-11-04",
                "condition_type_concept_id": 32817
            })
            cond_id_counter += 1

    # Write person.csv
    with open(person_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["person_id", "gender_concept_id", "year_of_birth", "month_of_birth", "day_of_birth", "race_concept_id", "ethnicity_concept_id", "sample_id"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(persons)
    print(f"Generated synthetic OMOP table: {person_path} ({len(persons)} records)")

    # Write condition_occurrence.csv
    with open(condition_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["condition_occurrence_id", "person_id", "condition_concept_id", "condition_start_date", "condition_type_concept_id"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(conditions)
    print(f"Generated synthetic OMOP table: {condition_path} ({len(conditions)} records)")

def main():
    print("=== Generating Synthetic Cohort Dataset ===")
    # 1. Full cohort VCF (10 samples)
    full_vcf = os.path.join(DATA_DIR, "cohort_10samples.vcf")
    generate_vcf(full_vcf, SAMPLE_IDS)

    # 2. Initial batch (samples 1-5) for baseline load
    batch1_vcf = os.path.join(DATA_DIR, "cohort_batch1_samples1to5.vcf")
    generate_vcf(batch1_vcf, SAMPLE_IDS[:5])

    # 3. Incremental N+1 batch (samples 6-10) for incremental ingest benchmarking
    batch2_vcf = os.path.join(DATA_DIR, "cohort_batch2_samples6to10.vcf")
    generate_vcf(batch2_vcf, SAMPLE_IDS[5:])

    # 4. Synthetic OMOP CDM Tables
    generate_omop_tables(DATA_DIR, SAMPLE_IDS)
    print("=== Dataset Generation Complete ===")

if __name__ == "__main__":
    main()
