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

# Simulated genomic loci across Chr21 and Chr22 (GRCh38 coordinates)
SYNTHETIC_LOCI = [
    # chr, start, end, ref, alt, gene_symbol, simulated_pathogenicity, target_phenotype_concept
    ("chr21", 25891796, 25891796, "A", "G", "APP", "PATHOGENIC", 43530807), # 43530807: Early onset Alzheimer disease
    ("chr21", 25891820, 25891820, "C", "T", "APP", "BENIGN", None),
    ("chr21", 33039603, 33039603, "G", "A", "SOD1", "PATHOGENIC", 374919),   # 374919: Amyotrophic lateral sclerosis
    ("chr21", 33039650, 33039650, "T", "C", "SOD1", "VUS", None),
    ("chr21", 41480000, 41480000, "C", "A", "RUNX1", "BENIGN", None),
    ("chr22", 17071756, 17071756, "T", "C", "BCR", "BENIGN", None),
    ("chr22", 23223844, 23223844, "G", "T", "SMARCB1", "PATHOGENIC", 4180790), # 4180790: Malignant rhabdoid tumor
    ("chr22", 29697660, 29697660, "A", "C", "NF2", "PATHOGENIC", 4216183),   # 4216183: Neurofibromatosis type 2
    ("chr22", 29697700, 29697700, "G", "A", "NF2", "BENIGN", None),
    ("chr22", 37680000, 37680000, "C", "T", "LARGE1", "BENIGN", None),
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
