from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext


RUPEE = Decimal("1")


@dataclass(frozen=True)
class SchemeTerms:
    name: str
    subsidy_percent: Decimal
    max_project_cost: int | None
    min_project_cost: int | None
    loan_percent: Decimal
    max_loan_amount: int | None
    annual_interest_percent: Decimal
    repayment_months: int
    moratorium_months: int
    # True for schemes whose terms are placeholders rather than sourced from the
    # problem statement. Not exposed in the response (the contract is locked) but
    # asserted in tests and documented in the README so nobody quotes them as fact.
    provisional: bool = False


MICRO_FINANCE_SCHEME = SchemeTerms(
    name="Micro Finance Scheme",
    subsidy_percent=Decimal("0"),
    min_project_cost=None,
    max_project_cost=140_000,
    loan_percent=Decimal("0.90"),
    max_loan_amount=125_000,
    annual_interest_percent=Decimal("6.5"),
    repayment_months=36,
    moratorium_months=3,
)

TERM_LOAN_SCHEME = SchemeTerms(
    name="Term Loan Scheme",
    subsidy_percent=Decimal("0"),
    min_project_cost=140_000,
    max_project_cost=5_000_000,
    loan_percent=Decimal("0.90"),
    max_loan_amount=4_500_000,
    annual_interest_percent=Decimal("8"),
    repayment_months=84,
    moratorium_months=6,
)

# PLACEHOLDERS - NOT AUTHORITATIVE.
#
# The two schemes above are transcribed from the problem statement and are exact.
# The three below are national schemes whose real eligibility depends on applicant
# attributes the API contract does not carry (social group, gender, urban/rural,
# enterprise vintage): PMEGP subsidy is 15-35% by category/area/social group, MUDRA
# is tiered Shishu/Kishore/Tarun, and Stand-Up India is Rs 10L-1Cr restricted to
# SC/ST and women borrowers. Encoding those properly needs a contract change.
# Until then these exist only so project costs above Rs 50L route somewhere.
PMEGP = SchemeTerms("PMEGP", Decimal("25"), None, None, Decimal("0.90"), None, Decimal("11"), 84, 6, provisional=True)
MUDRA = SchemeTerms("MUDRA", Decimal("0"), None, None, Decimal("0.90"), 1_000_000, Decimal("10"), 60, 0, provisional=True)
STAND_UP_INDIA = SchemeTerms("Stand-Up India", Decimal("0"), None, None, Decimal("0.90"), 10_000_000, Decimal("10"), 84, 18, provisional=True)


def choose_scheme(project_cost: int) -> SchemeTerms:
    """Route purely on project cost.

    The PS bands overlap at exactly Rs 1.40L ("up to 1.40L" vs "1.40L-50L"); the
    tie goes to Micro Finance, which is cheaper for the borrower at 6.5% vs 8%.
    """
    if project_cost <= MICRO_FINANCE_SCHEME.max_project_cost:
        return MICRO_FINANCE_SCHEME
    if project_cost <= TERM_LOAN_SCHEME.max_project_cost:
        return TERM_LOAN_SCHEME
    return PMEGP


# Both PS schemes fund 90% of project cost, so the entrepreneur's margin is the
# remaining 10%. Inverting that gives the project cost a given margin can support.
MARGIN_SHARE_OF_PROJECT_COST = Decimal("0.10")

# Recommended working capital buffer, as a share of project cost.
WORKING_CAPITAL_SHARE = Decimal("0.25")


def recommended_project_cost(margin_capital: int, requested_loan_amount: int | None) -> int:
    if requested_loan_amount is not None:
        return margin_capital + requested_loan_amount
    return _round_rupees(Decimal(margin_capital) / MARGIN_SHARE_OF_PROJECT_COST)


def working_capital_for(project_cost: int) -> int:
    return _round_rupees(Decimal(project_cost) * WORKING_CAPITAL_SHARE)


def loan_amount_for(project_cost: int, margin_capital: int, requested_loan_amount: int | None, terms: SchemeTerms) -> int:
    requested = requested_loan_amount if requested_loan_amount is not None else project_cost - margin_capital
    scheme_limit = int(Decimal(project_cost) * terms.loan_percent)
    if terms.max_loan_amount is not None:
        scheme_limit = min(scheme_limit, terms.max_loan_amount)
    return min(requested, scheme_limit)


def _round_rupees(value: Decimal) -> int:
    return int(value.quantize(RUPEE, rounding=ROUND_HALF_UP))


def _monthly_emi(principal: Decimal, annual_interest_percent: Decimal, months: int) -> Decimal:
    monthly_rate = annual_interest_percent / Decimal("1200")
    if monthly_rate == 0:
        return principal / Decimal(months)
    return principal * monthly_rate / (Decimal(1) - (Decimal(1) + monthly_rate) ** -months)


def amortization_schedule(loan_amount: int, terms: SchemeTerms) -> list[dict[str, int]]:
    """Full month-by-month schedule, moratorium rows first.

    During the moratorium no EMI is paid and interest is *capitalized* - it is
    added to the outstanding balance each month, so the balance grows. The level
    EMI is then computed on that grown balance over the repayment tenure, and the
    final instalment is trued up to retire the balance exactly.

    All arithmetic is Decimal at 40 digits of precision, rounded to whole rupees
    only at the point of output, so the schedule closes to a zero balance rather
    than drifting. The contract requires integer rupees.
    """
    with localcontext() as context:
        context.prec = 40
        balance = Decimal(loan_amount)
        monthly_rate = terms.annual_interest_percent / Decimal("1200")
        rows: list[dict[str, int]] = []

        for month in range(1, terms.moratorium_months + 1):
            interest = balance * monthly_rate
            balance += interest
            rows.append({
                "month": month,
                "emi": 0,
                "principal_component": 0,
                "interest_component": _round_rupees(interest),
                "outstanding_balance": _round_rupees(balance),
            })

        repayment_emi = _monthly_emi(balance, terms.annual_interest_percent, terms.repayment_months)
        for repayment_month in range(1, terms.repayment_months + 1):
            month = terms.moratorium_months + repayment_month
            interest = balance * monthly_rate
            payment = repayment_emi
            if repayment_month == terms.repayment_months:
                payment = balance + interest
            principal = payment - interest
            balance -= principal
            rows.append({
                "month": month,
                "emi": _round_rupees(payment),
                "principal_component": _round_rupees(principal),
                "interest_component": _round_rupees(interest),
                "outstanding_balance": max(0, _round_rupees(balance)),
            })
        return rows


def calculate(margin_capital: int, requested_loan_amount: int | None) -> tuple[int, SchemeTerms, int, list[dict[str, int]]]:
    project_cost = recommended_project_cost(margin_capital, requested_loan_amount)
    terms = choose_scheme(project_cost)
    loan_amount = loan_amount_for(project_cost, margin_capital, requested_loan_amount, terms)
    return project_cost, terms, loan_amount, amortization_schedule(loan_amount, terms)