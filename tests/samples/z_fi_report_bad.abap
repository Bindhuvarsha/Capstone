*&---------------------------------------------------------------------*
*& Report Z_FI_REPORT_BAD
*& Legacy ECC 6.0 Financial Line Item Extraction Report
*& Contains direct reads of BSEG, BSIS, and native SQL
*&---------------------------------------------------------------------*
REPORT z_fi_report_bad.

TABLES: bseg, bkpf, bsis.

DATA: lt_bseg TYPE STANDARD TABLE OF bseg,
      ls_bseg TYPE bseg,
      lv_bukrs TYPE bukrs VALUE '1000',
      lv_gjahr TYPE gjahr VALUE '2024'.

* Direct query on BSEG line item cluster table (R001)
SELECT * FROM bseg INTO TABLE lt_bseg
  WHERE bukrs = lv_bukrs
    AND gjahr = lv_gjahr.

* Query on secondary index table BSIS (R001)
SELECT * FROM bsis INTO CORRESPONDING FIELDS OF TABLE lt_bseg
  WHERE bukrs = lv_bukrs.

* Obsolete Native SQL query (R008)
EXEC SQL.
  SELECT BELNR, BUKRS FROM BKPF WHERE BUKRS = :lv_bukrs
ENDEXEC.

* Database specific hint (R010)
SELECT * FROM bkpf INTO CORRESPONDING FIELDS OF TABLE lt_bseg
  %_HINTS ORACLE 'INDEX("BKPF" "BKPF~0")'.

* Direct modification of standard accounting table (R009)
UPDATE bkpf SET bktxt = 'Migrated' WHERE bukrs = lv_bukrs.

WRITE: / 'FI extraction completed successfully.'.
