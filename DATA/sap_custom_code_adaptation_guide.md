# SAP Custom Code Adaptation Guide for S/4HANA & ABAP Test Cockpit (ATC)

- **Source**: SAP Community & Custom Code Migration Guide for S/4HANA
- **Topic**: Custom Code (ABAP / Basis)
- **S/4HANA Release**: 1809 to 2023 / 2026

## 1. Custom Code Migration Methodology
The custom code migration process for SAP S/4HANA follows three distinct phases:
1. **Scoping**: Identify custom code that is actually executed in production (using Usage and Procedure Logging - UPL, or ABAP Call Monitor - SCMON via CCLM). Unused code should be retired/deleted rather than migrated.
2. **Analysis**: Execute the ABAP Test Cockpit (ATC) with the check variant `S4HANA_READINESS` (or remote ATC from an S/4HANA system).
3. **Adaptation**: Remediate critical syntax errors, functional incompatibilities, and database-specific dependencies.

## 2. Key Code Patterns Requiring Remediation
- **Native SQL (`EXEC SQL ... ENDEXEC`)**:
  Native SQL bypasses the SAP database interface and Open SQL optimizations. In S/4HANA on SAP HANA DB, native SQL written for Oracle/DB2/SQL Server will fail or bypass columnar indexing and security.
  *Remediation*: Rewrite using Open SQL (modern ABAP SQL) or AMDP (ABAP Managed Database Procedures).
- **Direct Database Modifications on Standard SAP Tables**:
  ABAP statements modifying standard tables directly (`INSERT INTO MARA`, `UPDATE VBAK`, `MODIFY BSEG`) bypass application logic, data dictionaries, and document numbering invariants.
  *Remediation*: Use standard BAPIs or RAP (ABAP RESTful Application Programming Model) business objects.
- **Obsolete Statements and Database Hints**:
  - `CLIENT SPECIFIED` clause is obsolete in modern Open SQL (use `USING CLIENT`).
  - Database-specific hints (`%_HINTS ORACLE ...`) have no effect or cause syntax warnings in SAP HANA.
  - Assumptions on implicit sorting: In ECC, `SELECT` without an `ORDER BY` often returned records sorted by primary key due to database engine behavior. In SAP HANA (column store), record order without `ORDER BY` is non-deterministic.
- **Obsolete Function Modules**:
  Function modules such as `WS_DELIVERY_UPDATE`, `BAPI_CUSTOMER_CREATE`, and old FI posting routines are replaced by streamlined S/4HANA interfaces and RAP business objects.
