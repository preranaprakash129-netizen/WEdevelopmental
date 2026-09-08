# services/calculator

Owner: person 3

Project cost, scheme selection, EMI + moratorium schedule, working capital estimate.
Implements `POST /calculator` — see [`docs/api-contract.md`](../../docs/api-contract.md).

## Local dev

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
pytest                     # run from this directory
```

## Scheme terms

The two schemes named in the problem statement are transcribed exactly and are the
authoritative path. Everything a judge is likely to hand-check falls here.

| | Micro Finance Scheme | Term Loan Scheme |
|---|---|---|
| Project cost band | up to ₹1.40L | ₹1.40L – ₹50L |
| Loan | 90%, max ₹1.25L | 90%, max ₹45L |
| Interest | 6.5% p.a. | 8% p.a. |
| Repayment | 3 years (36 mo) | 7 years (84 mo) |
| Moratorium | 3 months | 6 months |

**PMEGP, MUDRA and Stand-Up India are placeholders and are not authoritative.** Their
real eligibility depends on applicant attributes the API contract does not carry
(social group, gender, urban/rural, enterprise vintage). They exist only so project
costs above ₹50L route somewhere. They are marked `provisional=True` in code and a
test enforces that flag. Do not quote their numbers in the demo.

## Modelling assumptions

These are deliberate decisions, not defaults. Each one moves the output numbers.

1. **Moratorium interest is capitalized.** Interest accrues monthly during the
   moratorium and is added to the outstanding balance; no EMI is paid. The level EMI
   is then computed on that grown balance. (The alternatives — servicing interest
   monthly, or simple non-compounded accrual — produce lower totals.)
2. **Project cost inverts the 90/10 split.** When the caller supplies only
   `margin_capital`, project cost is `margin ÷ 0.10`, since both schemes fund 90% and
   the entrepreneur's margin is the other 10%. If `requested_loan_amount` is given it
   takes precedence and project cost is `margin + requested`.
3. **The ₹1.40L tie goes to Micro Finance.** The PS bands overlap at exactly ₹1.40L;
   the cheaper scheme for the borrower wins (6.5% vs 8%).
4. **Working capital is 25% of project cost.** A flat rule of thumb, not category-aware.
5. **Rounding.** All arithmetic is `Decimal` at 40 digits; values are rounded to whole
   rupees (`ROUND_HALF_UP`) only on output, as the contract requires integer INR. The
   final instalment is trued up so the schedule closes at exactly zero rather than
   drifting by a few rupees.

### Worked example (hand-checkable)

₹1.25L at 6.5% with a 3-month moratorium, the maximum Micro Finance loan:

```
M1  interest   677   balance 125,677
M2  interest   681   balance 126,358
M3  interest   684   balance 127,042
M4–M39  EMI  3,894   closing balance 0
```

₹45L at 8% with a 6-month moratorium, the maximum Term Loan:

```
M1  interest 30,000   balance 4,530,000
M6                    balance 4,683,027
M7–M90  EMI  72,991   closing balance 0
```

## Known gaps

- `subsidy_percent` is 0 for both PS schemes — neither PS scheme defines a capital
  subsidy. If the team wants PMEGP-style subsidy in the demo, that needs real rules.
- The contract's `scheme_selected` carries only `name` and `subsidy_percent`, so the
  interest rate and tenure are not visible in the response even though they drive
  every EMI. Worth raising with the team as a contract amendment.
- Open question #2 in the contract (does calculator call feasibility for project cost,
  or does the gateway orchestrate?) is unresolved; assumption 2 above is the interim.
