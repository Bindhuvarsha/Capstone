"""
MigrateIQ ABAP Scanner Rules
10 Verified rules based on SAP S/4HANA Simplification List and ATC checks.
"""

from typing import List, Dict, Any
import re

RULES: List[Dict[str, Any]] = [
    {
        "id": "R001",
        "name": "Financial Line Items (BSEG/Index tables)",
        "area": "Financial line items",
        "severity": "high",
        "source": "SAP Simplification Item S4H_SI_FIN_001",
        "message": "Direct access to BSEG or index tables (BSIS, BSAS, etc.); financial data in S/4HANA is centered on Universal Journal ACDOCA.",
        "regex": r"(?i)(?:\bSELECT\b.*?FROM|\bFROM)\s+(?:bseg|bsis|bsas|bsik|bsak|bsid|bsad)\b",
        "recommendation": "Refactor query to use ACDOCA or core CDS view I_JournalEntryItem."
    },
    {
        "id": "R002",
        "name": "Sales Document Status (VBUK / VBUP)",
        "area": "Sales document status",
        "severity": "high",
        "source": "SAP Simplification Item S4H_SI_SD_002",
        "message": "Status tables VBUK and VBUP are obsolete; status fields are relocated into VBAK/VBAP and delivery/billing tables.",
        "regex": r"(?i)(?:\bSELECT\b.*?FROM|\bFROM|\bTABLES|\bDATA:?.*?TYPE)\s+(?:vbuk|vbup)\b",
        "recommendation": "Query header statuses from VBAK/LIKP/VBRK and item statuses from VBAP/LIPS/VBRP."
    },
    {
        "id": "R003",
        "name": "Material Documents (MKPF / MSEG)",
        "area": "Material documents",
        "severity": "high",
        "source": "SAP Simplification Item S4H_SI_MM_003",
        "message": "Material document tables MKPF and MSEG are replaced by MATDOC in S/4HANA.",
        "regex": r"(?i)(?:\bSELECT\b.*?FROM|\bFROM)\s+(?:mkpf|mseg)\b",
        "recommendation": "Query material movements from MATDOC or use CDS view C_MaterialStockByKeyDate."
    },
    {
        "id": "R004",
        "name": "Customer / Vendor Master (KNA1 / LFA1 Direct Maintenance)",
        "area": "Customer and vendor master",
        "severity": "medium",
        "source": "SAP Simplification Item S4H_SI_BP_001",
        "message": "Direct modification or master data bypass on KNA1/LFA1; Business Partner (CVI) is the leading object in S/4HANA.",
        "regex": r"(?i)\b(?:INSERT\s+INTO|UPDATE|MODIFY|DELETE\s+FROM)\s+(?:kna1|lfa1)\b",
        "recommendation": "Use Business Partner synchronization (CVI) or BAPIs (BAPI_BUPA_*)."
    },
    {
        "id": "R005",
        "name": "Hardcoded Material Number Length (MATNR 18)",
        "area": "Material number length",
        "severity": "medium",
        "source": "SAP Simplification Item S4H_SI_MM_004",
        "message": "Hardcoded MATNR length (18 characters) detected; MATNR field length is extended to 40 characters in S/4HANA.",
        "regex": r"(?i)(?:matnr[^\n\r;]*?(?:LENGTH\s+18|\(18\))|matnr\+0\(18\)|matnr\(18\))",
        "recommendation": "Declare material numbers using TYPE matnr or data element MATNR_DISPLAY (40 chars)."
    },
    {
        "id": "R006",
        "name": "Pricing Condition Table (KONV)",
        "area": "Pricing cluster table",
        "severity": "high",
        "source": "SAP Simplification Item S4H_SI_SD_003",
        "message": "Table KONV is obsolete; pricing condition records in S/4HANA are stored in transparent table PRCD_ELEMENTS.",
        "regex": r"(?i)(?:\bSELECT\b.*?FROM|\bFROM|\bTABLES)\s+konv\b",
        "recommendation": "Replace queries to KONV with PRCD_ELEMENTS or standard pricing APIs."
    },
    {
        "id": "R007",
        "name": "Obsolete Function Modules",
        "area": "Obsolete interfaces",
        "severity": "medium",
        "source": "SAP Simplification Item S4H_SI_BASIS_005",
        "message": "Call to obsolete function module detected; replaced or altered in S/4HANA.",
        "regex": r"(?i)\bCALL\s+FUNCTION\s+['\"](?:WS_DELIVERY_UPDATE|BAPI_CUSTOMER_CREATE|BAPI_CUSTOMER_CHANGEFROMDATA|CONVERT_TO_LOCAL_CURRENCY|SO_NEW_DOCUMENT_SEND_API1)['\"]",
        "recommendation": "Migrate to modern S/4HANA replacement BAPIs or RAP business object actions."
    },
    {
        "id": "R008",
        "name": "Native SQL Statements (EXEC SQL)",
        "area": "Database portability",
        "severity": "high",
        "source": "SAP Custom Code Migration Guide: Native SQL",
        "message": "Native SQL (EXEC SQL) detected; bypasses SAP HANA database optimizations, CDS views, and authorization checks.",
        "regex": r"(?i)\bEXEC\s+SQL\b",
        "recommendation": "Rewrite using Open SQL (modern ABAP SQL) or AMDP (ABAP Managed Database Procedures)."
    },
    {
        "id": "R009",
        "name": "Direct Modification of Standard SAP Tables",
        "area": "Application integrity",
        "severity": "high",
        "source": "SAP S/4HANA Readiness Check: Custom Code",
        "message": "Direct DB modification (INSERT/UPDATE/MODIFY/DELETE) on standard SAP table violates S/4HANA data integrity.",
        "regex": r"(?i)\b(?:INSERT\s+INTO|UPDATE|MODIFY|DELETE\s+FROM)\s+(?:mara|vbak|vbap|ekko|ekpo|bseg|bkpf)\b",
        "recommendation": "Use SAP standard APIs, BAPIs, or RAP business objects instead of direct table updates."
    },
    {
        "id": "R010",
        "name": "Obsolete Open SQL Clauses and DB Hints",
        "area": "Open SQL modernization",
        "severity": "low",
        "source": "SAP HANA Programming Guide: Database Hints",
        "message": "CLIENT SPECIFIED clause or DB-specific hints (%_HINTS) detected; obsolete or ignored on SAP HANA DB.",
        "regex": r"(?i)(?:\bCLIENT\s+SPECIFIED\b|%_HINTS\b)",
        "recommendation": "Use USING CLIENT syntax in modern Open SQL and remove obsolete DBMS-specific hints."
    }
]

def get_rule_by_id(rule_id: str) -> Dict[str, Any]:
    for r in RULES:
        if r["id"] == rule_id:
            return r
    return {}
