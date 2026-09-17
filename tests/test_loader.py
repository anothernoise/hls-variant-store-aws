"""
Unit tests for VCF Ingestion Loader into Amazon S3 Tables schema.
"""

import os
import unittest
from ingest.s3tables.load_variants import parse_vcf_records, ICEBERG_COLUMNS

class TestVcfLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.dirname(os.path.abspath(__file__))
        cls.vcf_path = os.path.join(cls.test_dir, "test_sample.vcf")
        content = (
            "##fileformat=VCFv4.2\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample_001\tsample_002\n"
            "chr21\t25891796\trs123\tA\tG\t99.0\tPASS\tGENE=APP;CLNSIG=PATHOGENIC\tGT:DP:GQ:AD\t0/1:30:99:15,15\t0/0:32:90:32,0\n"
        )
        with open(cls.vcf_path, "w", encoding="utf-8") as f:
            f.write(content)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.vcf_path):
            os.remove(cls.vcf_path)

    def test_parse_vcf_records_count(self):
        records = list(parse_vcf_records(self.vcf_path, cohort_id="test_cohort"))
        self.assertEqual(len(records), 2)

    def test_schema_conformance(self):
        records = list(parse_vcf_records(self.vcf_path, cohort_id="test_cohort"))
        for rec in records:
            for col in ICEBERG_COLUMNS:
                self.assertIn(col, rec, f"Missing required column {col} in record")

    def test_record_values(self):
        records = list(parse_vcf_records(self.vcf_path, cohort_id="test_cohort"))
        rec_s1 = [r for r in records if r["sample_id"] == "sample_001"][0]
        self.assertEqual(rec_s1["reference_name"], "chr21")
        self.assertEqual(rec_s1["start"], 25891796)
        self.assertEqual(rec_s1["end"], 25891796)
        self.assertEqual(rec_s1["reference_bases"], "A")
        self.assertEqual(rec_s1["alternate_bases"], "G")
        self.assertEqual(rec_s1["genotype"], "0/1")
        self.assertEqual(rec_s1["dp"], 30)
        self.assertEqual(rec_s1["gq"], 99)
        self.assertEqual(rec_s1["allele_depth"], "15,15")
        self.assertIn('"gene": "APP"', rec_s1["attributes"])

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            list(parse_vcf_records("non_existent.vcf"))

if __name__ == "__main__":
    unittest.main()
