"""Structured ground truth for all 6 schemes this prototype covers.

This is the single source of truth for two things that must never disagree:
  1. The rule engine that labels synthetic training data for the scheme-match
     classifier (see train/generate_training_data.py) -- so the model is
     trained to approximate *these exact* real eligibility rules, not an
     arbitrary pattern.
  2. The local (no-API) chatbot's answer templates (see local_advisor.py) --
     so every number the chatbot states is pulled from here, never generated,
     which is what makes hallucination structurally impossible rather than
     merely "prompted against."

Figures were researched from official/authoritative sources on 2026-09-10 --
see corpus/manifest.json for the exact URLs. Scheme parameters change; treat
this as a snapshot worth re-verifying before presenting, not a live feed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SchemeFacts:
    key: str  # matches manifest.json "scheme" field
    display_name: str
    url: str

    # --- Eligibility gates used by both the rule-labeler and the chatbot ---
    requires_new_business: bool  # greenfield only (Stand-Up India, PMEGP)
    requires_sc_st_or_woman: bool  # Stand-Up India's bank-branch mandate
    allowed_categories: Optional[List[str]]  # None = any category eligible
    min_loan: int
    max_loan: int
    max_annual_family_income: Optional[int]  # Karnataka Udyogini income cap (general)
    max_annual_family_income_sc_st: Optional[int]  # higher cap for SC/ST
    women_only: bool  # Udyogini is women-only

    # --- Numbers the chatbot states verbatim, never generates ---
    subsidy_general_pct: Optional[float]
    subsidy_special_pct: Optional[float]  # SC/ST/women/etc, wherever the scheme has a higher tier
    own_contribution_pct_general: Optional[float]
    own_contribution_pct_special: Optional[float]
    guarantee_coverage_pct_general: Optional[float]  # CGTMSE-style
    guarantee_coverage_pct_special: Optional[float]
    tiers: Optional[Dict[str, str]] = None  # e.g. MUDRA's Shishu/Kishore/Tarun
    documents: List[str] = field(default_factory=list)
    apply_process: str = ""


SCHEMES: Dict[str, SchemeFacts] = {
    "PMEGP": SchemeFacts(
        key="PMEGP",
        display_name="Prime Minister's Employment Generation Programme (PMEGP)",
        url="https://kviconline.gov.in/pmegp",
        requires_new_business=True,
        requires_sc_st_or_woman=False,
        allowed_categories=None,
        min_loan=100000,
        max_loan=5000000,  # Rs.50 lakh manufacturing ceiling
        max_annual_family_income=None,
        max_annual_family_income_sc_st=None,
        women_only=False,
        subsidy_general_pct=15.0,  # urban general; 25% rural general (see notes)
        subsidy_special_pct=25.0,  # urban special; 35% rural special
        own_contribution_pct_general=10.0,
        own_contribution_pct_special=5.0,
        guarantee_coverage_pct_general=None,
        guarantee_coverage_pct_special=None,
        documents=["Aadhaar", "PAN", "project report", "education certificate", "category certificate (if applicable)"],
        apply_process=(
            "Apply online through the KVIC e-Portal. The application routes to your district's "
            "KVIC, KVIB or DIC office, then a District Task Force Committee interview, then the "
            "financing bank's own appraisal before disbursal."
        ),
    ),
    "MUDRA": SchemeFacts(
        key="MUDRA",
        display_name="Pradhan Mantri MUDRA Yojana (PMMY)",
        url="https://www.mudra.org.in/",
        requires_new_business=False,
        requires_sc_st_or_woman=False,
        allowed_categories=None,
        min_loan=0,
        max_loan=1000000,
        max_annual_family_income=None,
        max_annual_family_income_sc_st=None,
        women_only=False,
        subsidy_general_pct=None,  # MUDRA is a loan product, not a subsidy scheme
        subsidy_special_pct=None,
        own_contribution_pct_general=None,
        own_contribution_pct_special=None,
        guarantee_coverage_pct_general=None,
        guarantee_coverage_pct_special=None,
        tiers={"Shishu": "up to Rs.50,000", "Kishore": "Rs.50,000-5 lakh", "Tarun": "Rs.5-10 lakh"},
        documents=["identity proof", "address proof", "business address proof", "last 6 months bank statements"],
        apply_process="Apply at the branch of a bank, NBFC or MFI where you already hold an account, or via udyamimitra.in.",
    ),
    "Stand-Up India": SchemeFacts(
        key="Stand-Up India",
        display_name="Stand-Up India",
        url="https://www.standupmitra.in/",
        requires_new_business=True,
        requires_sc_st_or_woman=True,
        allowed_categories=None,
        min_loan=1000000,
        max_loan=10000000,
        max_annual_family_income=None,
        max_annual_family_income_sc_st=None,
        women_only=False,
        subsidy_general_pct=None,
        subsidy_special_pct=None,
        own_contribution_pct_general=None,
        own_contribution_pct_special=None,
        guarantee_coverage_pct_general=None,
        guarantee_coverage_pct_special=None,
        documents=["identity/address proof", "SC/ST certificate (if applicable)", "project report"],
        apply_process="Apply online via standupmitra.in, which also connects you to handholding agencies for the loan application.",
    ),
    "CGTMSE": SchemeFacts(
        key="CGTMSE",
        display_name="Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE)",
        url="https://www.cgtmse.in/",
        requires_new_business=False,
        requires_sc_st_or_woman=False,
        allowed_categories=None,
        min_loan=0,
        max_loan=100000000,  # Rs.10 crore
        max_annual_family_income=None,
        max_annual_family_income_sc_st=None,
        women_only=False,
        subsidy_general_pct=None,
        subsidy_special_pct=None,
        own_contribution_pct_general=None,
        own_contribution_pct_special=None,
        guarantee_coverage_pct_general=75.0,
        guarantee_coverage_pct_special=85.0,
        documents=["Udyam registration", "loan application via your bank/NBFC"],
        apply_process="Not applied for directly -- your bank or NBFC requests the guarantee cover as part of processing your loan.",
    ),
    "PMFME": SchemeFacts(
        key="PMFME",
        display_name="Pradhan Mantri Formalisation of Micro Food Processing Enterprises (PMFME)",
        url="https://pmfme.mofpi.gov.in/",
        requires_new_business=False,
        requires_sc_st_or_woman=False,
        allowed_categories=["food-processing", "dairy"],
        min_loan=0,
        max_loan=1000000,  # Rs.10 lakh per unit individual cap
        max_annual_family_income=None,
        max_annual_family_income_sc_st=None,
        women_only=False,
        subsidy_general_pct=35.0,
        subsidy_special_pct=35.0,
        own_contribution_pct_general=None,
        own_contribution_pct_special=None,
        guarantee_coverage_pct_general=None,
        guarantee_coverage_pct_special=None,
        documents=["business/unit details", "project report", "SHG/FPO membership (if applying as a group)"],
        apply_process="Apply through your State Nodal Agency / District Resource Person, or the PMFME portal.",
    ),
    "Karnataka Udyogini": SchemeFacts(
        key="Karnataka Udyogini",
        display_name="Udyogini Scheme (Karnataka)",
        url="https://kswdc.karnataka.gov.in/",
        requires_new_business=False,
        requires_sc_st_or_woman=False,  # gated separately via women_only below
        allowed_categories=None,
        min_loan=0,
        max_loan=300000,
        max_annual_family_income=150000,
        max_annual_family_income_sc_st=200000,
        women_only=True,
        subsidy_general_pct=30.0,
        subsidy_special_pct=50.0,  # SC/ST women
        own_contribution_pct_general=None,
        own_contribution_pct_special=None,
        guarantee_coverage_pct_general=None,
        guarantee_coverage_pct_special=None,
        documents=["identity/address proof", "project report", "income certificate", "caste certificate (if applicable)", "BPL card (if applicable)"],
        apply_process="Apply online via a participating bank/NBFC, or offline via kswdc.karnataka.gov.in forms through your district's Child Development Project Officer.",
    ),
}
