from uuid import uuid4

from fastapi import FastAPI

from app.calculator import calculate, working_capital_for
from app.schemas import CalculatorRequest, CalculatorResponse, EmiRow, Moratorium, SchemeSelected


app = FastAPI(title="SIH26091 Calculator", version="0.1.0")


@app.post("/calculator", response_model=CalculatorResponse)
def calculator(request: CalculatorRequest) -> CalculatorResponse:
    project_cost, terms, loan_amount, schedule = calculate(
        request.margin_capital,
        request.requested_loan_amount,
    )
    return CalculatorResponse(
        request_id=str(uuid4()),
        project_cost=project_cost,
        scheme_selected=SchemeSelected(
            name=terms.name,
            subsidy_percent=float(terms.subsidy_percent),
        ),
        loan_amount=loan_amount,
        emi_schedule=[EmiRow(**row) for row in schedule],
        moratorium=Moratorium(
            months=terms.moratorium_months,
            reason=(
                f"{terms.name} standard moratorium; interest accrues and is "
                f"capitalized into the principal before repayment begins"
            ),
        ),
        working_capital=working_capital_for(project_cost),
    )