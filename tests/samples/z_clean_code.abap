*&---------------------------------------------------------------------*
*& Report Z_CLEAN_CODE
*& Clean S/4HANA Compliant ABAP Program
*& Uses ACDOCA, MATDOC, modern Open SQL, CDS views, and proper data types
*&---------------------------------------------------------------------*
REPORT z_clean_code.

DATA: lv_matnr TYPE matnr,
      lv_bukrs TYPE bukrs VALUE '1000',
      lv_gjahr TYPE gjahr VALUE '2026'.

* Clean S/4HANA Universal Journal query
SELECT rldnr, rbukrs, gjahr, belnr, docln, hsl
  FROM acdoca
  WHERE rldnr  = '0L'
    AND rbukrs = @lv_bukrs
    AND gjahr  = @lv_gjahr
  INTO TABLE @DATA(lt_journal_items)
  UP TO 100 ROWS.

* Clean S/4HANA Material Document query
SELECT mblnr, mjahr, zeile, bwart, matnr, menge, meins
  FROM matdoc
  WHERE mjahr = @lv_gjahr
  INTO TABLE @DATA(lt_material_docs)
  UP TO 50 ROWS.

* Read sales order header status directly from VBAK
SELECT vbeln, erdat, ernam, gbstk
  FROM vbak
  WHERE vbeln = '0000010000'
  INTO TABLE @DATA(lt_orders).

WRITE: / 'S/4HANA compliant processing successful.'.
