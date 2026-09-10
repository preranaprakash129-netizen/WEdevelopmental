"""Hand-authored (question, label) pairs for the local chatbot's intent router.

Label format: "{SCHEME_KEY}::{intent}" for a scheme-specific question, or
"GENERAL::{intent}" for something that isn't about one specific scheme.
Intents: eligibility, amount, documents, apply_process.

This is a real (if small, hand-authored) supervised text-classification
dataset -- honest about being hand-written, not scraped or crowd-sourced.
Small hand-written sets are a legitimate, common way to bootstrap an intent
classifier before real usage logs exist; say so plainly if asked, rather than
implying a larger provenance than this has.
"""

from __future__ import annotations

EXAMPLES = [
    # --- PMEGP ---
    ("Am I eligible for PMEGP", "PMEGP::eligibility"),
    ("who can apply for pmegp", "PMEGP::eligibility"),
    ("what is the minimum qualification for PMEGP", "PMEGP::eligibility"),
    ("can an existing business apply for PMEGP", "PMEGP::eligibility"),
    ("is PMEGP only for new businesses", "PMEGP::eligibility"),
    ("what age do I need to be for PMEGP", "PMEGP::eligibility"),
    ("PMEGP eligibility criteria", "PMEGP::eligibility"),
    ("do I qualify for the PMEGP scheme", "PMEGP::eligibility"),
    ("how much subsidy does PMEGP give", "PMEGP::amount"),
    ("what is the maximum project cost under PMEGP", "PMEGP::amount"),
    ("how much loan can I get from PMEGP", "PMEGP::amount"),
    ("PMEGP subsidy percentage rural vs urban", "PMEGP::amount"),
    ("what is my own contribution for PMEGP", "PMEGP::amount"),
    ("PMEGP margin money amount", "PMEGP::amount"),
    ("what documents do I need for PMEGP", "PMEGP::documents"),
    ("PMEGP required papers", "PMEGP::documents"),
    ("what certificates are needed for PMEGP application", "PMEGP::documents"),
    ("how do I apply for PMEGP", "PMEGP::apply_process"),
    ("PMEGP application process", "PMEGP::apply_process"),
    ("where do I submit my PMEGP form", "PMEGP::apply_process"),
    ("khadi board loan how to apply", "PMEGP::apply_process"),
    ("kvic loan application steps", "PMEGP::apply_process"),

    # --- MUDRA ---
    ("what is mudra loan", "MUDRA::eligibility"),
    ("who is eligible for mudra loan", "MUDRA::eligibility"),
    ("can I get a mudra loan for my shop", "MUDRA::eligibility"),
    ("is mudra loan only for new business", "MUDRA::eligibility"),
    ("mudra loan eligibility criteria", "MUDRA::eligibility"),
    ("what is shishu kishore tarun", "MUDRA::amount"),
    ("how much loan under mudra shishu", "MUDRA::amount"),
    ("mudra loan maximum amount", "MUDRA::amount"),
    ("mudra loan interest rate", "MUDRA::amount"),
    ("what is the mudra loan limit", "MUDRA::amount"),
    ("documents needed for mudra loan", "MUDRA::documents"),
    ("what papers do I need for pradhan mantri mudra yojana", "MUDRA::documents"),
    ("bank statement required for mudra loan", "MUDRA::documents"),
    ("how do I apply for mudra loan", "MUDRA::apply_process"),
    ("where can I get a mudra loan", "MUDRA::apply_process"),
    ("pmmy application process", "MUDRA::apply_process"),
    ("which bank gives mudra loans", "MUDRA::apply_process"),

    # --- Stand-Up India ---
    ("what is stand up india scheme", "Stand-Up India::eligibility"),
    ("am I eligible for stand up india", "Stand-Up India::eligibility"),
    ("is stand up india only for women", "Stand-Up India::eligibility"),
    ("can a general category person apply for stand up india", "Stand-Up India::eligibility"),
    ("does stand up india need sc st certificate", "Stand-Up India::eligibility"),
    ("stand up india loan amount range", "Stand-Up India::amount"),
    ("how much can I borrow under stand up india", "Stand-Up India::amount"),
    ("maximum loan under stand up india scheme", "Stand-Up India::amount"),
    ("what documents for stand up india loan", "Stand-Up India::documents"),
    ("papers required for stand up india application", "Stand-Up India::documents"),
    ("do I need an sc st certificate for stand up india", "Stand-Up India::documents"),
    ("how to apply for stand up india", "Stand-Up India::apply_process"),
    ("standupmitra portal application steps", "Stand-Up India::apply_process"),
    ("where do I submit stand up india application", "Stand-Up India::apply_process"),

    # --- CGTMSE ---
    ("what is cgtmse", "CGTMSE::eligibility"),
    ("who can use cgtmse guarantee", "CGTMSE::eligibility"),
    ("is cgtmse a loan or a guarantee", "CGTMSE::eligibility"),
    ("do I need collateral if I use cgtmse", "CGTMSE::eligibility"),
    ("cgtmse coverage percentage", "CGTMSE::amount"),
    ("how much guarantee cover does cgtmse give", "CGTMSE::amount"),
    ("cgtmse maximum guarantee amount", "CGTMSE::amount"),
    ("cgtmse guarantee fee", "CGTMSE::amount"),
    ("what documents for cgtmse", "CGTMSE::documents"),
    ("do I need udyam registration for cgtmse", "CGTMSE::documents"),
    ("papers my bank needs for cgtmse guarantee", "CGTMSE::documents"),
    ("how do I apply for cgtmse cover", "CGTMSE::apply_process"),
    ("can I apply to cgtmse directly", "CGTMSE::apply_process"),
    ("does my bank apply for cgtmse or do I", "CGTMSE::apply_process"),

    # --- PMFME ---
    ("what is pmfme scheme", "PMFME::eligibility"),
    ("who can apply for pmfme", "PMFME::eligibility"),
    ("is pmfme only for food business", "PMFME::eligibility"),
    ("can a pickle business apply for pmfme", "PMFME::eligibility"),
    ("pmfme subsidy percentage", "PMFME::amount"),
    ("how much subsidy for food processing unit", "PMFME::amount"),
    ("pmfme maximum subsidy amount", "PMFME::amount"),
    ("shg seed capital under pmfme", "PMFME::amount"),
    ("what documents for pmfme", "PMFME::documents"),
    ("do I need a project report for pmfme", "PMFME::documents"),
    ("shg membership proof needed for pmfme", "PMFME::documents"),
    ("how to apply for pmfme scheme", "PMFME::apply_process"),
    ("pmfme application process for food processing", "PMFME::apply_process"),
    ("where do I submit pmfme application", "PMFME::apply_process"),

    # --- Karnataka Udyogini ---
    ("what is udyogini scheme", "Karnataka Udyogini::eligibility"),
    ("am I eligible for udyogini loan", "Karnataka Udyogini::eligibility"),
    ("is udyogini scheme only for women", "Karnataka Udyogini::eligibility"),
    ("what is the income limit for udyogini scheme", "Karnataka Udyogini::eligibility"),
    ("age limit for udyogini scheme karnataka", "Karnataka Udyogini::eligibility"),
    ("udyogini scheme subsidy percentage", "Karnataka Udyogini::amount"),
    ("how much loan under udyogini scheme", "Karnataka Udyogini::amount"),
    ("udyogini maximum loan amount", "Karnataka Udyogini::amount"),
    ("what documents for udyogini scheme", "Karnataka Udyogini::documents"),
    ("do I need a caste certificate for udyogini", "Karnataka Udyogini::documents"),
    ("income certificate needed for udyogini scheme", "Karnataka Udyogini::documents"),
    ("how to apply for udyogini scheme karnataka", "Karnataka Udyogini::apply_process"),
    ("kswdc application process", "Karnataka Udyogini::apply_process"),
    ("where do I get the udyogini application form", "Karnataka Udyogini::apply_process"),

    # --- General / cross-scheme ---
    ("which scheme is best for me", "GENERAL::which_scheme"),
    ("what loan should I apply for", "GENERAL::which_scheme"),
    ("recommend a scheme for my business", "GENERAL::which_scheme"),
    ("I don't know which government scheme to choose", "GENERAL::which_scheme"),
    ("help me pick the right scheme", "GENERAL::which_scheme"),
    ("what is the best government scheme for a new dairy business", "GENERAL::which_scheme"),
    ("hello", "GENERAL::greeting"),
    ("hi", "GENERAL::greeting"),
    ("hey there", "GENERAL::greeting"),
    ("good morning", "GENERAL::greeting"),
    ("thank you", "GENERAL::greeting"),
    ("thanks for the help", "GENERAL::greeting"),

    # --- Out-of-domain negatives ---
    # Without explicit "this is NOT about a scheme" examples, a closed-set
    # classifier always picks its closest class for anything, including
    # nonsense -- it has no way to say "none of the above" on its own. These
    # teach that class explicitly, rather than relying on a confidence
    # threshold alone (which, with this little data, is poorly calibrated).
    ("what is the airspeed velocity of an unladen swallow", "GENERAL::unclear"),
    ("what's the weather like today", "GENERAL::unclear"),
    ("who won the cricket match yesterday", "GENERAL::unclear"),
    ("tell me a joke", "GENERAL::unclear"),
    ("what is the capital of France", "GENERAL::unclear"),
    ("how do I cook biryani", "GENERAL::unclear"),
    ("what's your favorite movie", "GENERAL::unclear"),
    ("can you write me a poem", "GENERAL::unclear"),
    ("what time is it", "GENERAL::unclear"),
    ("how old are you", "GENERAL::unclear"),
    ("what is 2 plus 2", "GENERAL::unclear"),
    ("tell me about the stock market", "GENERAL::unclear"),
]
