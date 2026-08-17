import os
import unittest

import pandas as pd


class TestLoaderDataIntegrity(unittest.TestCase):
    def test_raw_files_exist(self):
        files = [
            "data/raw/companies.xlsx",
            "data/raw/profitandloss.xlsx",
            "data/raw/balancesheet.xlsx",
            "data/raw/cashflow.xlsx",
            "data/raw/analysis.xlsx",
            "data/raw/documents.xlsx",
            "data/raw/prosandcons.xlsx",
            "data/supporting/sectors.xlsx",
            "data/supporting/stock_prices.xlsx",
            "data/supporting/market_cap.xlsx",
            "data/supporting/financial_ratios.xlsx",
            "data/supporting/peer_groups.xlsx",
        ]
        for f in files:
            self.assertTrue(os.path.exists(f), f"File {f} is missing")

    def test_companies_columns(self):
        df = pd.read_excel("data/raw/companies.xlsx", header=1)
        self.assertIn("id", df.columns)
        self.assertIn("company_name", df.columns)

    def test_sectors_columns(self):
        df = pd.read_excel("data/supporting/sectors.xlsx")
        self.assertIn("company_id", df.columns)
        self.assertIn("broad_sector", df.columns)

    def test_pl_columns(self):
        df = pd.read_excel("data/raw/profitandloss.xlsx", header=1)
        self.assertIn("company_id", df.columns)
        self.assertIn("sales", df.columns)

    def test_bs_columns(self):
        df = pd.read_excel("data/raw/balancesheet.xlsx", header=1)
        self.assertIn("company_id", df.columns)
        self.assertIn("total_assets", df.columns)

    def test_cf_columns(self):
        df = pd.read_excel("data/raw/cashflow.xlsx", header=1)
        self.assertIn("company_id", df.columns)
        self.assertIn("operating_activity", df.columns)

    def test_analysis_columns(self):
        df = pd.read_excel("data/raw/analysis.xlsx", header=1)
        self.assertIn("company_id", df.columns)

    def test_documents_columns(self):
        df = pd.read_excel("data/raw/documents.xlsx", header=1)
        self.assertIn("company_id", df.columns)

    def test_prosandcons_columns(self):
        df = pd.read_excel("data/raw/prosandcons.xlsx", header=1)
        self.assertIn("company_id", df.columns)

    def test_peer_groups_columns(self):
        df = pd.read_excel("data/supporting/peer_groups.xlsx")
        self.assertIn("peer_group_name", df.columns)
        self.assertIn("company_id", df.columns)
