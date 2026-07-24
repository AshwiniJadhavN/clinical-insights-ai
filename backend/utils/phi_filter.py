"""
PHI (Protected Health Information) safeguards for logging and error handling.

HIPAA Rule 45 CFR §164.312(b): Audit controls must log who accessed PHI and when.
HIPAA Rule 45 CFR §164.514: PHI must be de-identified before appearing in logs.

Provides: PHISafeFilter, scrub(), safe_error_response(), PHI_FIELD_NAMES.
"""

import logging
import re

PHI_FIELD_NAMES: frozenset[str] = frozenset({
    "patient_name", "first_name", "last_name", "full_name",
    "date_of_birth", "dob", "birthdate",
    "ssn", "social_security_number", "national_id",
    "mrn", "medical_record_number", "patient_id",
    "address", "street", "zip_code", "postal_code",
    "phone", "phone_number", "fax",
    "email", "email_address",
    "insurance_id", "policy_number",
    "diagnosis", "icd_code",
    "medication", "drug_name", "prescription",
    "lab_result", "test_result",
})

_PHI_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),           "[SSN-REDACTED]"),
    (re.compile(r"\b[A-Z]{1,3}\d{6,10}\b"),           "[MRN-REDACTED]"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),           "[DATE-REDACTED]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b"), "[EMAIL-REDACTED]"),
    (re.compile(r"\b\d{3}[\s.\-]?\d{3}[\s.\-]?\d{4}\b"), "[PHONE-REDACTED]"),
]


def scrub(text: str) -> str:
    for pattern, replacement in _PHI_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class PHISafeFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = scrub(str(record.msg))
        if isinstance(record.args, tuple):
            record.args = tuple(scrub(str(a)) for a in record.args)
        return True


def safe_error_response(internal_detail: str, public_message: str) -> str:
    from backend.utils.logger import get_logger
    get_logger("phi_guard").error(scrub(internal_detail))
    return public_message
