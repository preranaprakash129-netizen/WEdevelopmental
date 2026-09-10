from typing import Literal

from pydantic import BaseModel, Field


class CalculatorRequest(BaseModel):
    margin_capital: int = Field(ge=0)
    category: str = Field(min_length=1)
    location: str | None = None
    requested_loan_amount: int | None = Field(default=None, ge=0)

    # Applicant attributes for scheme eligibility beyond cost-based routing (see
    # choose_scheme in app/calculator.py). All optional so existing callers are
    # unaffected. is_rural and enterprise_vintage_months are accepted here for
    # forward-compatibility (e.g. a future PMEGP rural/urban subsidy split) but
    # aren't consumed by routing yet - that expansion is out of scope for now.
    social_category: Literal["general", "obc", "sc", "st"] | None = None
    gender: Literal["male", "female", "other"] | None = None
    is_rural: bool | None = None
    enterprise_vintage_months: int | None = Field(default=None, ge=0)

    # Bypasses cost-based routing to request a specific scheme directly. "MUDRA"
    # is otherwise entirely unreachable (its real range sits inside the Micro
    # Finance / Term Loan cost bands); "Stand-Up India" is only automatically
    # reachable for Rs 50L-1Cr, so this also unlocks its Rs 10L-50L portion for
    # eligible (SC/ST or woman-owned) applicants. See choose_scheme's docstring.
    requested_scheme: Literal["MUDRA", "Stand-Up India"] | None = None


class SchemeSelected(BaseModel):
    name: str
    subsidy_percent: float = Field(ge=0, le=100)


class EmiRow(BaseModel):
    month: int
    emi: int
    principal_component: int
    interest_component: int
    outstanding_balance: int


class Moratorium(BaseModel):
    months: int
    reason: str | None = None


class CalculatorResponse(BaseModel):
    request_id: str
    project_cost: int
    scheme_selected: SchemeSelected
    loan_amount: int
    emi_schedule: list[EmiRow]
    moratorium: Moratorium
    working_capital: int