# SAP S/4HANA Simplification Item: Sales Document Status and Pricing Data Model

- **Source**: SAP Help Portal & S/4HANA Simplification Item S4H_SI_SD_002
- **Topic**: Sales and Distribution (SD)
- **S/4HANA Release**: 1610 to 2023 / 2026

## 1. Overview and Status Field Relocation
In SAP ECC 6.0, header-level and item-level processing statuses for sales and billing documents were stored centrally in tables `VBUK` (Header Status) and `VBUP` (Item Status). 

In SAP S/4HANA:
- Header status fields (e.g., `GBSTK`, `LFSTK`, `WBSTK`, `FKSTK`) have been moved directly into the corresponding document header tables:
  - Sales Orders: `VBAK`
  - Deliveries: `LIKP`
  - Billing Documents: `VBRK`
- Item status fields (e.g., `GBSTA`, `LFSTA`, `WBSTA`, `FKSTA`) have been moved directly into the document item tables:
  - Sales Order Items: `VBAP`
  - Delivery Items: `LIPS`
  - Billing Document Items: `VBRP`

Tables `VBUK` and `VBUP` are no longer updated as transparent application tables. They exist only as compatibility views for read access.

## 2. Pricing Conditions Data Model (KONV -> PRCD_ELEMENTS)
In SAP ECC 6.0, condition records for documents were stored in cluster table `KONV`.
In SAP S/4HANA:
- Table `KONV` is replaced by the transparent table `PRCD_ELEMENTS`.
- Direct queries or custom code reading or writing to `KONV` will fail or hit compatibility views with performance overhead.

## 3. Impact on Custom ABAP Code
- Code executing `SELECT ... FROM VBUK` or `SELECT ... FROM VBUP` joins will suffer significant performance degradation because compatibility views emulate the old structure with large outer joins.
- Code updating `VBUK` or `VBUP` directly (`UPDATE VBUK ...`) will fail with runtime database errors (`DBSQL_TABLE_UNKNOWN` or read-only view exceptions).
- Pricing routines reading `KONV` directly must be replaced with accesses to `PRCD_ELEMENTS` or standard pricing APIs (`PRICING_COMPLETE`, etc.).

## 4. Recommended Remediation
1. Adjust queries to select status attributes directly from `VBAK` (Header) and `VBAP` (Item) or their CDS view counterparts `I_SalesOrder` and `I_SalesOrderItem`.
2. Replace all references to `KONV` with `PRCD_ELEMENTS`. Ensure field types match the extended definitions.
