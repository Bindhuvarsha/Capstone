"""
MigrateIQ ABAP Scanner Engine
Parses ABAP code, evaluates simplification rules, and returns structured findings.
"""

from typing import List, Dict, Any, Optional
import re
from app.scanner.rules import RULES

class ABAPScanner:
    def __init__(self, custom_rules: Optional[List[Dict[str, Any]]] = None):
        self.rules = custom_rules or RULES
        self._compiled_rules = [
            {
                **rule,
                "compiled": re.compile(rule["regex"], re.IGNORECASE | re.DOTALL)
            }
            for rule in self.rules
        ]

    def scan_code(self, code: str, filename: str = "custom_program.abap") -> Dict[str, Any]:
        """
        Scans ABAP source code and returns structured findings, LOC, and metadata.
        """
        lines = code.splitlines()
        loc = len(lines)
        findings: List[Dict[str, Any]] = []

        # Multi-line statement buffer support
        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            
            # Skip empty lines or pure comment lines (* at line start)
            if not stripped or stripped.startswith("*"):
                continue

            # Strip inline comments (everything after ")
            code_part = stripped.split('"')[0].strip()
            if not code_part:
                continue

            # Evaluate each rule against the active code line
            for rule in self._compiled_rules:
                if rule["compiled"].search(code_part):
                    findings.append({
                        "file": filename,
                        "line": line_idx,
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "area": rule.get("area", "General"),
                        "severity": rule["severity"],
                        "snippet": stripped[:120] + ("..." if len(stripped) > 120 else ""),
                        "message": rule["message"],
                        "recommendation": rule.get("recommendation", ""),
                        "source": rule["source"]
                    })

        return {
            "filename": filename,
            "lines_of_code": loc,
            "total_findings": len(findings),
            "findings": findings
        }

    def scan_files(self, file_map: Dict[str, str]) -> Dict[str, Any]:
        """
        Scans multiple files: file_map = {filename: file_content}
        """
        file_results = []
        total_loc = 0
        all_findings = []

        for filename, content in file_map.items():
            result = self.scan_code(content, filename)
            file_results.append(result)
            total_loc += result["lines_of_code"]
            all_findings.extend(result["findings"])

        return {
            "total_files": len(file_map),
            "total_lines_of_code": total_loc,
            "total_findings": len(all_findings),
            "files": file_results,
            "all_findings": all_findings
        }
