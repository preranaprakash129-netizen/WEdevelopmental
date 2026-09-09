"""Boundary tests for the two schemes named in the problem statement.

The scheme *terms* asserted here come straight from the PS and are fixed facts.

The *derived* amortization figures additionally depend on one modelling choice:
interest accrued during the moratorium is capitalized (added to principal) rather
than paid as it accrues. If the team switches to simple/serviced moratorium
interest, the term-sheet assertions stay valid but every derived figure below
moves — see `amortization_schedule` in app/calculator.py.
"""

from decimal import Decimal

from app.calculator import (
    MICRO_FINANCE_SCHEME,
    MUDRA,
    PMEGP,
    STAND_UP_INDIA,
    TERM_LOAN_SCHEME,
    amortization_schedule,
    choose_scheme,
    loan_amount_for,
    recommended_project_cost,
    working_capital_for,
)


# --- Term sheets, straight from the problem statement -----------------------


def test_micro_finance_term_sheet_matches_ps():
    # Micro Finance Scheme: project cost up to Rs 1.40L, 90% / max Rs 1.25L,
    # 6.5% p.a., 3 years, 3 month moratorium.
    assert MICRO_FINANCE_SCHEME.max_project_cost == 140_000
    assert MICRO_FINANCE_SCHEME.loan_percent == Decimal("0.90")
    assert MICRO_FINANCE_SCHEME.max_loan_amount == 125_000
    assert MICRO_FINANCE_SCHEME.annual_interest_percent == Decimal("6.5")
    assert MICRO_FINANCE_SCHEME.repayment_months == 36
    assert MICRO_FINANCE_SCHEME.moratorium_months == 3


def test_term_loan_term_sheet_matches_ps():
    # Term Loan Scheme: project cost Rs 1.40L-Rs 50L, 90% / max Rs 45L,
    # 8% p.a., 7 years, 6 month moratorium.
    assert TERM_LOAN_SCHEME.min_project_cost == 140_000
    assert TERM_LOAN_SCHEME.max_project_cost == 5_000_000
    assert TERM_LOAN_SCHEME.loan_percent == Decimal("0.90")
    assert TERM_LOAN_SCHEME.max_loan_amount == 4_500_000
    assert TERM_LOAN_SCHEME.annual_interest_percent == Decimal("8")
    assert TERM_LOAN_SCHEME.repayment_months == 84
    assert TERM_LOAN_SCHEME.moratorium_months == 6


# --- Routing at the Rs 1.40L seam ------------------------------------------


def test_micro_finance_wins_at_exactly_140000():
    # The PS ranges overlap at Rs 1.40L ("up to 1.40L" vs "1.40L-50L").
    # We resolve the tie in favour of the cheaper scheme for the borrower.
    assert choose_scheme(140_000) is MICRO_FINANCE_SCHEME
    assert choose_scheme(139_999) is MICRO_FINANCE_SCHEME


def test_term_loan_covers_just_above_140000_up_to_50_lakh():
    assert choose_scheme(140_001) is TERM_LOAN_SCHEME
    assert choose_scheme(5_000_000) is TERM_LOAN_SCHEME


# --- The 90% / absolute-cap interaction ------------------------------------


def test_micro_finance_cap_binds_before_90_percent_at_top_of_band():
    # 90% of 1.40L = 1.26L, but the absolute cap is 1.25L, so the cap binds.
    assert loan_amount_for(140_000, 14_000, None, MICRO_FINANCE_SCHEME) == 125_000


def test_term_loan_90_percent_and_cap_coincide_at_50_lakh():
    # 90% of 50L = 45L, exactly the absolute cap.
    assert loan_amount_for(5_000_000, 500_000, None, TERM_LOAN_SCHEME) == 4_500_000


# --- Amortization at the maximum sanctionable loan under each scheme --------


def test_micro_finance_max_loan_schedule():
    schedule = amortization_schedule(125_000, MICRO_FINANCE_SCHEME)

    assert len(schedule) == 39  # 3 moratorium + 36 repayment

    # Moratorium months carry interest only, no EMI, no principal repaid.
    for row in schedule[:3]:
        assert row["emi"] == 0
        assert row["principal_component"] == 0
    assert schedule[0]["interest_component"] == 677  # 125000 * 6.5% / 12
    assert schedule[2]["outstanding_balance"] == 127_042

    # Level EMI over the 36 repayment months on the capitalized balance.
    assert schedule[3]["emi"] == 3_894
    assert schedule[-1]["outstanding_balance"] == 0


def test_term_loan_max_loan_schedule():
    schedule = amortization_schedule(4_500_000, TERM_LOAN_SCHEME)

    assert len(schedule) == 90  # 6 moratorium + 84 repayment

    for row in schedule[:6]:
        assert row["emi"] == 0
        assert row["principal_component"] == 0
    assert schedule[0]["interest_component"] == 30_000  # 4500000 * 8% / 12
    assert schedule[5]["outstanding_balance"] == 4_683_027

    assert schedule[6]["emi"] == 72_991
    assert schedule[-1]["outstanding_balance"] == 0


# --- Project cost and working capital derivation ----------------------------


def test_project_cost_inverts_the_90_10_split():
    # Schemes fund 90%, so a margin of X supports a project cost of X / 0.10.
    assert recommended_project_cost(14_000, None) == 140_000
    assert recommended_project_cost(500_000, None) == 5_000_000
    assert recommended_project_cost(50_000, None) == 500_000


def test_explicit_requested_loan_overrides_the_derivation():
    assert recommended_project_cost(50_000, 90_000) == 140_000


def test_derived_project_cost_makes_the_90_percent_rule_bind():
    # End to end at the top of the Micro Finance band: Rs 14,000 margin supports a
    # Rs 1.40L project, where the Rs 1.25L absolute cap bites before the 90% rule.
    project_cost = recommended_project_cost(14_000, None)
    terms = choose_scheme(project_cost)
    assert terms is MICRO_FINANCE_SCHEME
    assert loan_amount_for(project_cost, 14_000, None, terms) == 125_000


def test_working_capital_is_25_percent_of_project_cost():
    assert working_capital_for(140_000) == 35_000
    assert working_capital_for(5_000_000) == 1_250_000


# --- Provisional schemes must stay flagged ----------------------------------


def test_ps_schemes_are_authoritative_and_the_rest_are_flagged():
    assert MICRO_FINANCE_SCHEME.provisional is False
    assert TERM_LOAN_SCHEME.provisional is False
    for scheme in (PMEGP, MUDRA, STAND_UP_INDIA):
        assert scheme.provisional is True, f"{scheme.name} must stay flagged provisional"


def test_above_50_lakh_falls_through_to_a_provisional_scheme():
    assert choose_scheme(5_000_001).provisional is True


# --- Schedule invariants that must hold for any scheme ----------------------


def test_schedule_rows_are_internally_consistent():
    for loan, terms in ((125_000, MICRO_FINANCE_SCHEME), (4_500_000, TERM_LOAN_SCHEME)):
        schedule = amortization_schedule(loan, terms)

        assert [row["month"] for row in schedule] == list(range(1, len(schedule) + 1))

        for row in schedule[terms.moratorium_months:]:
            # Rounding to whole rupees can shift the split by at most Rs 1.
            split = row["principal_component"] + row["interest_component"]
            assert abs(split - row["emi"]) <= 1

        # Balance is non-increasing once repayment starts, and fully retired.
        repayment = schedule[terms.moratorium_months:]
        balances = [row["outstanding_balance"] for row in repayment]
        assert balances == sorted(balances, reverse=True)
        assert balances[-1] == 0
