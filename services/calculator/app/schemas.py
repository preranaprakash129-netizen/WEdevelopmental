from pydantic import BaseModel, Field


class CalculatorRequest(BaseModel):
    margin_capital: int = Field(ge=0)
    category: str = Field(min_length=1)
    location: str | None = None
    requested_loan_amount: int | None = Field(default=None, ge=0)


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