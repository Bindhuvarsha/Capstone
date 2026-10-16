*&---------------------------------------------------------------------*
*& Report Z_SD_ORDER_BAD
*& Legacy Sales Order Status & Pricing Report
*& Contains VBUK, VBUP, KONV, and obsolete delivery function module
*&---------------------------------------------------------------------*
REPORT z_sd_order_bad.

TABLES: vbak, vbap, vbuk, vbup, konv.

DATA: lt_vbuk TYPE STANDARD TABLE OF vbuk,
      lt_vbup TYPE STANDARD TABLE OF vbup,
      lt_konv TYPE STANDARD TABLE OF konv,
      lv_vbeln TYPE vbeln_va VALUE '0000012345'.

* Direct query on obsolete header status table VBUK (R002)
SELECT * FROM vbuk INTO TABLE lt_vbuk
  WHERE vbeln = lv_vbeln.

* Direct query on obsolete item status table VBUP (R002)
SELECT * FROM vbup INTO TABLE lt_vbup
  WHERE vbeln = lv_vbeln.

* Obsolete Open SQL clause CLIENT SPECIFIED (R010)
SELECT * FROM vbak CLIENT SPECIFIED
  WHERE mandt = sy-mandt AND vbeln = lv_vbeln.

* Direct read of obsolete pricing cluster table KONV (R006)
SELECT * FROM konv INTO TABLE lt_konv
  WHERE knumv = '0000000100'.

* Obsolete delivery update function module (R007)
CALL FUNCTION 'WS_DELIVERY_UPDATE'
  EXPORTING
    delivery = lv_vbeln.

WRITE: / 'SD Status processing finished.'.
