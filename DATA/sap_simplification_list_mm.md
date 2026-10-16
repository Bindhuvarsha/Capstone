# SAP S/4HANA Simplification Item: Material Management (MATDOC, MATNR, Business Partner)

- **Source**: SAP Help Portal & S/4HANA Simplification Items S4H_SI_MM_003 / S4H_SI_BP_001
- **Topic**: Materials Management (MM) & Business Partner (BP)
- **S/4HANA Release**: 1511 to 2023 / 2026

## 1. Material Documents: MKPF and MSEG replaced by MATDOC
In SAP ECC 6.0, inventory movements were recorded across two primary tables: `MKPF` (Material Document Header) and `MSEG` (Material Document Segment / Line Items). Valuation tables included `MBEW`, `MARD`, etc.

In SAP S/4HANA:
- All inventory movements and stock ledger entries are unified into a single transparent table: `MATDOC` (Material Document Line Items).
- Tables `MKPF` and `MSEG` are replaced by compatibility views. Physical writes to `MKPF` and `MSEG` are strictly prohibited.
- Aggregated inventory tables (like `MARD`, `MSLB`, `MCHB`) are calculated on-the-fly from `MATDOC` records, eliminating database lock contention during high-volume goods receipts.

## 2. Material Number Field Extension (MATNR: 18 to 40 characters)
In SAP ECC 6.0, the `MATNR` domain had a length of 18 characters (`CHAR18`).
In SAP S/4HANA:
- The `MATNR` field length is extended to 40 characters (`CHAR40`).
- Custom code with hardcoded length definitions, concatenation offsets (`DATA lv_matnr(18) TYPE c`), or substring operations (`lv_matnr+0(18)`) will cause data truncation, silent corruption, or syntax errors.
- External formats and interfaces (BAPIs, IDOCs, EDI, RFC) must be reviewed for length compatibility.

## 3. Customer and Vendor Master Integration (Business Partner Approach)
In SAP ECC 6.0, customer master records resided in `KNA1`, `KNB1`, `KNVV`, and vendor master records resided in `LFA1`, `LFB1`, `LFM1`.

In SAP S/4HANA:
- The SAP Business Partner (`BUT000`, `BUT020`, `BUT100`) is the mandatory single point of entry for managing master data for business partners, customers, and vendors (CVI - Customer Vendor Integration).
- Direct maintenance of `KNA1` and `LFA1` transactions (e.g. `FD01`, `FK01`, `XD01`, `XK01`) is obsolete and redirects to transaction `BP`.
- While read compatibility exists for `KNA1`/`LFA1` for basic reporting, write operations and synchronization must be handled through CVI services and Business Partner APIs.

## 4. Recommended Remediation
1. Refactor inventory queries to select from `MATDOC` or standard CDS views (`C_MaterialStockByKeyDate`).
2. Replace hardcoded `CHAR18` definitions with `TYPE matnr` or the data element `MATNR_DISPLAY`.
3. Migrate customer/vendor master maintenance logic to CVI and Business Partner BAPIs (`BAPI_BUPA_*`).
