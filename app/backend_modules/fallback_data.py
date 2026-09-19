"""
Deterministic fallback synthetic data loader and local VCF parser.
"""

import os
import sys
import pandas as pd
from typing import Tuple


class FallbackDataLoader:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.vcf_path = os.path.join(project_root, "samples/data/cohort_10samples.vcf")
        self.person_path = os.path.join(project_root, "samples/data/person.csv")
        self.cond_path = os.path.join(project_root, "samples/data/condition_occurrence.csv")
        self.person_df = pd.DataFrame()
        self.cond_df = pd.DataFrame()
        self.variants_df = pd.DataFrame()
        self.load_all()

    def load_all(self):
        """Loads deterministic local synthetic datasets as baseline."""
        self.person_df = pd.read_csv(self.person_path) if os.path.exists(self.person_path) else pd.DataFrame()
        self.cond_df = pd.read_csv(self.cond_path) if os.path.exists(self.cond_path) else pd.DataFrame()

        if os.path.exists(self.vcf_path):
            try:
                if self.project_root not in sys.path:
                    sys.path.insert(0, self.project_root)
                from ingest.s3tables.load_variants import parse_vcf_records
                records = list(parse_vcf_records(self.vcf_path))
                self.variants_df = pd.DataFrame(records)
            except Exception:
                pass

    @staticmethod
    @staticmethod
    def get_fallback_dataframe(query_kind: str, gene: str = "APP") -> pd.DataFrame:
        """Returns deterministic baseline DataFrame for offline demo UI."""
        safe_gene = (gene or "APP").upper()
        if safe_gene not in ("APP", "SOD1", "BRCA1"):
            safe_gene = "APP"

        if query_kind == "carriers":
            gene_records = {
                "APP": [
                    {"sample_id": "NA12878", "reference_name": "chr21", "start": "25891796", "reference_bases": "A", "alternate_bases": "G", "genotype": "0/1", "dp": "48", "gq": "99", "allele_depth": "24,24", "gene_symbol": "APP", "clinical_significance": "PATHOGENIC"},
                    {"sample_id": "HG002", "reference_name": "chr21", "start": "25891796", "reference_bases": "A", "alternate_bases": "G", "genotype": "0/1", "dp": "52", "gq": "99", "allele_depth": "27,25", "gene_symbol": "APP", "clinical_significance": "PATHOGENIC"},
                    {"sample_id": "HG003", "reference_name": "chr21", "start": "25891796", "reference_bases": "A", "alternate_bases": "G", "genotype": "0/1", "dp": "45", "gq": "95", "allele_depth": "22,23", "gene_symbol": "APP", "clinical_significance": "PATHOGENIC"},
                    {"sample_id": "HG004", "reference_name": "chr21", "start": "25891796", "reference_bases": "A", "alternate_bases": "G", "genotype": "1/1", "dp": "60", "gq": "99", "allele_depth": "0,60", "gene_symbol": "APP", "clinical_significance": "PATHOGENIC"},
                ],
                "SOD1": [
                    {"sample_id": "NA12878", "reference_name": "chr21", "start": "31659787", "reference_bases": "C", "alternate_bases": "T", "genotype": "0/1", "dp": "42", "gq": "98", "allele_depth": "20,22", "gene_symbol": "SOD1", "clinical_significance": "PATHOGENIC"},
                    {"sample_id": "HG003", "reference_name": "chr21", "start": "31659787", "reference_bases": "C", "alternate_bases": "T", "genotype": "0/1", "dp": "50", "gq": "99", "allele_depth": "25,25", "gene_symbol": "SOD1", "clinical_significance": "PATHOGENIC"},
                    {"sample_id": "HG005", "reference_name": "chr21", "start": "31659787", "reference_bases": "C", "alternate_bases": "T", "genotype": "1/1", "dp": "55", "gq": "99", "allele_depth": "0,55", "gene_symbol": "SOD1", "clinical_significance": "PATHOGENIC"},
                ],
                "BRCA1": [
                    {"sample_id": "HG002", "reference_name": "chr17", "start": "43044295", "reference_bases": "C", "alternate_bases": "T", "genotype": "0/1", "dp": "64", "gq": "99", "allele_depth": "32,32", "gene_symbol": "BRCA1", "clinical_significance": "LIKELY_PATHOGENIC"},
                    {"sample_id": "HG004", "reference_name": "chr17", "start": "43044295", "reference_bases": "C", "alternate_bases": "T", "genotype": "0/1", "dp": "58", "gq": "96", "allele_depth": "28,30", "gene_symbol": "BRCA1", "clinical_significance": "LIKELY_PATHOGENIC"},
                ]
            }
            return pd.DataFrame(gene_records.get(safe_gene, gene_records["APP"]))

        elif query_kind == "burden":
            burden_records = {
                "APP": [
                    {"sample_id": "NA12878", "gene_symbol": "APP", "distinct_variant_sites": 2, "total_alt_allele_burden": 3},
                    {"sample_id": "HG002", "gene_symbol": "APP", "distinct_variant_sites": 1, "total_alt_allele_burden": 1},
                    {"sample_id": "HG003", "gene_symbol": "APP", "distinct_variant_sites": 2, "total_alt_allele_burden": 2},
                    {"sample_id": "HG004", "gene_symbol": "APP", "distinct_variant_sites": 3, "total_alt_allele_burden": 4},
                    {"sample_id": "HG005", "gene_symbol": "APP", "distinct_variant_sites": 1, "total_alt_allele_burden": 1},
                ],
                "SOD1": [
                    {"sample_id": "NA12878", "gene_symbol": "SOD1", "distinct_variant_sites": 1, "total_alt_allele_burden": 1},
                    {"sample_id": "HG003", "gene_symbol": "SOD1", "distinct_variant_sites": 2, "total_alt_allele_burden": 3},
                    {"sample_id": "HG005", "gene_symbol": "SOD1", "distinct_variant_sites": 1, "total_alt_allele_burden": 2},
                ],
                "BRCA1": [
                    {"sample_id": "HG002", "gene_symbol": "BRCA1", "distinct_variant_sites": 2, "total_alt_allele_burden": 2},
                    {"sample_id": "HG004", "gene_symbol": "BRCA1", "distinct_variant_sites": 1, "total_alt_allele_burden": 1},
                ]
            }
            return pd.DataFrame(burden_records.get(safe_gene, burden_records["APP"]))

        elif query_kind == "omop":
            return pd.DataFrame([
                {"person_id": "P001", "sample_id": "NA12878", "year_of_birth": "1982", "gene_symbol": "APP", "clinical_significance": "PATHOGENIC", "genotype": "0/1", "condition_concept_id": "378419", "condition_start_date": "2021-04-12"},
                {"person_id": "P002", "sample_id": "HG002", "year_of_birth": "1975", "gene_symbol": "APP", "clinical_significance": "PATHOGENIC", "genotype": "0/1", "condition_concept_id": "378419", "condition_start_date": "2020-08-19"},
                {"person_id": "P003", "sample_id": "HG003", "year_of_birth": "1968", "gene_symbol": "APP", "clinical_significance": "PATHOGENIC", "genotype": "0/1", "condition_concept_id": "378419", "condition_start_date": "2019-11-03"},
                {"person_id": "P004", "sample_id": "HG004", "year_of_birth": "1990", "gene_symbol": "APP", "clinical_significance": "PATHOGENIC", "genotype": "1/1", "condition_concept_id": "378419", "condition_start_date": "2022-01-15"},
            ])
        else:  # "af"
            return pd.DataFrame([
                {"engine": "mock_data", "reference_name": "chr21", "start": "25891796", "reference_bases": "A", "alternate_bases": "G", "total_cohort_samples": "10", "alt_carrier_count": "4", "carrier_frequency": "0.4000", "gene_symbol": "APP", "clinical_significance": "PATHOGENIC"},
                {"engine": "mock_data", "reference_name": "chr21", "start": "31659787", "reference_bases": "C", "alternate_bases": "T", "total_cohort_samples": "10", "alt_carrier_count": "4", "carrier_frequency": "0.4000", "gene_symbol": "SOD1", "clinical_significance": "PATHOGENIC"},
                {"engine": "mock_data", "reference_name": "chr1", "start": "100050", "reference_bases": "G", "alternate_bases": "T", "total_cohort_samples": "10", "alt_carrier_count": "3", "carrier_frequency": "0.3000", "gene_symbol": "BRCA1", "clinical_significance": "LIKELY_PATHOGENIC"},
                {"engine": "mock_data", "reference_name": "chr1", "start": "100120", "reference_bases": "T", "alternate_bases": "C", "total_cohort_samples": "10", "alt_carrier_count": "2", "carrier_frequency": "0.2000", "gene_symbol": "BRCA1", "clinical_significance": "BENIGN"},
            ])
