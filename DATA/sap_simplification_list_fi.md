# SAP S/4HANA Simplification Item: Financial Line Items (ACDOCA vs BSEG)

- **Source**: SAP Help Portal & S/4HANA Simplification Item S4H_SI_FIN_001
- **Topic**: Finance (FI/CO)
- **S/4HANA Release**: 1511 to 2023 / 2026

## 1. Overview and Architectural Change
In SAP ECC 6.0, financial accounting (FI) and controlling (CO) were separated across distinct database tables. Detail line items were recorded in `BSEG`, with secondary indexes stored in tables such as `BSIS`, `BSAS` (G/L accounts), `BSID`, `BSAD` (Customers), and `BSIK`, `BSAK` (Vendors). General ledger totals were maintained in `GLT0` or `FAGLFLEXT`.

In SAP S/4HANA, the Universal Journal table `ACDOCA` (Universal Journal Entry Line Items) replaces the separate line item tables and index tables. `ACDOCA` combines FI, CO, AA (Asset Accounting), ML (Material Ledger), and Profitability Analysis into a single line-item table containing over 350 columns.

## 2. Impact on Custom ABAP Code
- **Direct Queries on BSEG / BSIS / BSAS**:
  Direct `SELECT` queries on `BSEG`, `BSIS`, or `BSAS` in custom reports will either trigger severe performance degradation or fail to retrieve newly posted entries because secondary index tables (`BSIS`, `BSAS`, `BSIK`, etc.) are now implemented as compatibility views rather than physical transparent tables.
- **Compatibility Views**:
  SAP provides DDL compatibility views for `BSIS`, `BSAS`, `BSID`, `BSAD`, `BSIK`, and `BSAK`. However, reading from these compatibility views performs an on-the-fly calculation and union against `ACDOCA`, which can be computationally expensive if queries are not filtered on indexed fields.
- **Cluster/Pool Behavior**:
  Legacy operations treating `BSEG` as a cluster table or using database hints `%_HINTS` are obsolete.

## 3. Recommended Remediation
1. Refactor Open SQL queries to select from the Universal Journal `ACDOCA` or use modern Core Data Services (CDS) views (such as `I_JournalEntryItem`).
2. Use SAP-delivered standard APIs and BAPIs (`BAPI_ACC_DOCUMENT_POST`) for financial postings rather than manual table modifications.
3. For custom reports requiring line items, specify mandatory filters on `RCLNT` (Client), `RLDNR` (Ledger), `RBUKRS` (Company Code), and `GJAHR` (Fiscal Year) to leverage the primary partition of `ACDOCA`.
