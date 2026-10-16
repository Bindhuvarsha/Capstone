"""
MigrateIQ Guardrails Module
Enforces strict scope constraints: SAP ECC to S/4HANA Migration, ABAP, and Custom Code Adaptation.
Blocks out-of-scope queries and prompt injections.
"""

import re
from typing import Tuple, Dict, Any

# Whitelisted core domain keywords
SAP_KEYWORDS = [
    "sap", "ecc", "s/4hana", "s4hana", "s4", "abap", "hana", "migration", "acdoca",
    "bseg", "mseg", "matdoc", "mkpf", "vbuk", "vbup", "kna1", "lfa1", "konv",
    "prcd_elements", "matnr", "atc", "simplification", "cvi", "business partner",
    "fiori", "cds", "amdp", "btp", "open sql", "native sql", "scmon", "upl",
    "code conversion", "readiness check", "sum", "maintenance", "custom code",
    "bapi", "idoc", "badi", "enhancement", "spau", "spdd", "sap gui"
]

# Blacklisted prompt-injection or jailbreak patterns
INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"disregard\s+(?:all\s+)?prior\s+prompts",
    r"system\s*:\s*you\s+are\s+now",
    r"jailbreak",
    r"dan\s+mode",
    r"forget\s+your\s+role",
    r"bypass\s+rules",
    r"give\s+me\s+your\s+system\s+prompt"
]

# Obvious out-of-scope domains
OUT_OF_SCOPE_PATTERNS = [
    r"\b(?:recipe|cooking|bake|cake|pasta|ingredients)\b",
    r"\b(?:movie|actor|film|hollywood|bollywood|box office)\b",
    r"\b(?:sports|football|cricket|nba|world cup|fifa)\b",
    r"\b(?:weather\s+in|forecast\s+for)\b",
    r"\b(?:write\s+a\s+poem|compose\s+a\s+song|joke\s+about)\b",
    r"\b(?:quantum\s+physics|gardening|astrology|horoscope)\b"
]

class GuardrailsEngine:
    def __init__(self):
        self.injection_regexes = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
        self.out_of_scope_regexes = [re.compile(p, re.IGNORECASE) for p in OUT_OF_SCOPE_PATTERNS]

    def validate_query(self, query: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates if an incoming query is within the SAP S/4HANA migration scope.
        Returns: (is_allowed, reason_or_message, metadata)
        """
        clean_text = query.strip()
        lower_text = clean_text.lower()

        if len(clean_text) < 3:
            return False, "Query is too short. Please ask a detailed SAP migration question.", {"code": "TOO_SHORT"}

        # 1. Prompt Injection Check
        for reg in self.injection_regexes:
            if reg.search(lower_text):
                return False, "Security violation: Potential prompt injection or system override detected. Request rejected.", {
                    "code": "PROMPT_INJECTION",
                    "flagged_pattern": reg.pattern
                }

        # 2. Obvious Out-of-Scope Check
        for reg in self.out_of_scope_regexes:
            if reg.search(lower_text):
                return False, "Out of scope: MigrateIQ is dedicated solely to SAP ECC to S/4HANA migration and ABAP adaptation.", {
                    "code": "OUT_OF_SCOPE_DOMAIN",
                    "flagged_pattern": reg.pattern
                }

        # 3. Domain Keyword Presence Check
        has_sap_keyword = any(kw in lower_text for kw in SAP_KEYWORDS)
        if not has_sap_keyword:
            # Let general technical questions through only if related to database/migration/sql
            tech_keywords = ["database", "table", "sql", "index", "column", "query", "upgrade", "conversion"]
            if not any(tk in lower_text for tk in tech_keywords):
                return False, "Out of scope: Query does not appear related to SAP ECC or S/4HANA migration. Please ask questions concerning SAP simplification, ABAP code adaptation, or migration strategy.", {
                    "code": "NO_DOMAIN_MATCH"
                }

        return True, "Query allowed within SAP S/4HANA migration scope.", {
            "code": "ALLOWED",
            "scope": "SAP_MIGRATION"
        }

guardrails = GuardrailsEngine()
