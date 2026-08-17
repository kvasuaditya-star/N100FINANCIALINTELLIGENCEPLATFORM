import unittest

import pandas as pd

from src.etl.validator import DataValidator


class TestDataQualityRules(unittest.TestCase):
    def setUp(self):
        self.validator = DataValidator()

    def test_dq_01_companies_pk(self):
        # Create duplicate company ID
        df = pd.DataFrame(
            [
                {"id": "TCS", "company_name": "Tata Consultancy Services"},
                {"id": "TCS", "company_name": "Duplicate TCS"},
            ]
        )
        res = self.validator.validate_dq_01_companies_pk(df)
        self.assertFalse(res)
        self.assertTrue(any(f["rule_id"] == "DQ-01" for f in self.validator.failures))

    def test_dq_02_annual_pk(self):
        df = pd.DataFrame(
            [
                {"company_id": "TCS", "year": "2024-03", "sales": 100},
                {"company_id": "TCS", "year": "2024-03", "sales": 200},
            ]
        )
        res_df = self.validator.validate_dq_02_annual_pk("profitandloss", df)
        self.assertEqual(len(res_df), 1)
        self.assertTrue(any(f["rule_id"] == "DQ-02" for f in self.validator.failures))

    def test_dq_03_fk_integrity(self):
        valid_ids = {"TCS", "INFY"}
        df = pd.DataFrame([{"company_id": "INVALID"}])
        res_df = self.validator.validate_dq_03_fk_integrity("sectors", df, valid_ids)
        self.assertEqual(len(res_df), 0)
        self.assertTrue(any(f["rule_id"] == "DQ-03" for f in self.validator.failures))

    def test_dq_04_bs_balance(self):
        df = pd.DataFrame(
            [
                {
                    "company_id": "TCS",
                    "year": "2024-03",
                    "total_assets": 100,
                    "total_liabilities": 110,
                }
            ]
        )
        self.validator.validate_dq_04_bs_balance(df)
        self.assertTrue(any(f["rule_id"] == "DQ-04" for f in self.validator.failures))

    def test_dq_05_opm_crosscheck(self):
        df = pd.DataFrame(
            [
                {
                    "company_id": "TCS",
                    "year": "2024-03",
                    "sales": 100,
                    "operating_profit": 20,
                    "opm_percentage": 25.0,
                }
            ]
        )
        self.validator.validate_dq_05_opm_crosscheck(df)
        self.assertTrue(any(f["rule_id"] == "DQ-05" for f in self.validator.failures))

    def test_dq_06_positive_sales(self):
        df_pl = pd.DataFrame([{"company_id": "TCS", "year": "2024-03", "sales": 0}])
        df_sec = pd.DataFrame(
            [{"company_id": "TCS", "broad_sector": "Technology", "sub_sector": "IT"}]
        )
        self.validator.validate_dq_06_positive_sales(df_pl, df_sec)
        self.assertTrue(any(f["rule_id"] == "DQ-06" for f in self.validator.failures))

    def test_dq_07_year_format(self):
        df = pd.DataFrame([{"company_id": "TCS", "year": "2024"}])
        res_df = self.validator.validate_dq_07_year_format("profitandloss", df)
        self.assertEqual(len(res_df), 0)
        self.assertTrue(any(f["rule_id"] == "DQ-07" for f in self.validator.failures))

    def test_dq_08_ticker_format(self):
        df = pd.DataFrame([{"company_id": "T"}])
        res_df = self.validator.validate_dq_08_ticker_format("profitandloss", df)
        self.assertEqual(len(res_df), 0)
        self.assertTrue(any(f["rule_id"] == "DQ-08" for f in self.validator.failures))

    def test_dq_09_net_cash(self):
        df = pd.DataFrame(
            [
                {
                    "company_id": "TCS",
                    "year": "2024-03",
                    "operating_activity": 100,
                    "investing_activity": -20,
                    "financing_activity": -10,
                    "net_cash_flow": 150,
                }
            ]
        )
        self.validator.validate_dq_09_net_cash(df)
        self.assertTrue(any(f["rule_id"] == "DQ-09" for f in self.validator.failures))

    def test_dq_10_fixed_assets(self):
        df = pd.DataFrame(
            [{"company_id": "TCS", "year": "2024-03", "fixed_assets": -50}]
        )
        res_df = self.validator.validate_dq_10_fixed_assets(df)
        self.assertEqual(res_df.iloc[0]["fixed_assets"], 0.0)
        self.assertTrue(any(f["rule_id"] == "DQ-10" for f in self.validator.failures))

    def test_dq_11_tax_rate(self):
        df = pd.DataFrame(
            [{"company_id": "TCS", "year": "2024-03", "tax_percentage": 75}]
        )
        self.validator.validate_dq_11_tax_rate(df)
        self.assertTrue(any(f["rule_id"] == "DQ-11" for f in self.validator.failures))

    def test_dq_12_dividend_cap(self):
        df = pd.DataFrame(
            [{"company_id": "TCS", "year": "2024-03", "dividend_payout": 250}]
        )
        self.validator.validate_dq_12_dividend_cap(df)
        self.assertTrue(any(f["rule_id"] == "DQ-12" for f in self.validator.failures))

    def test_dq_13_urls(self):
        # We check invalid URL
        df = pd.DataFrame(
            [
                {
                    "company_id": "TCS",
                    "Year": 2024,
                    "Annual_Report": "http://invalid-url-that-does-not-exist.org/report.pdf",
                }
            ]
        )
        self.validator.validate_dq_13_urls(df)
        self.assertTrue(any(f["rule_id"] == "DQ-13" for f in self.validator.failures))

    def test_dq_14_eps_sign(self):
        df = pd.DataFrame(
            [{"company_id": "TCS", "year": "2024-03", "net_profit": 100, "eps": -2}]
        )
        self.validator.validate_dq_14_eps_sign(df)
        self.assertTrue(any(f["rule_id"] == "DQ-14" for f in self.validator.failures))
