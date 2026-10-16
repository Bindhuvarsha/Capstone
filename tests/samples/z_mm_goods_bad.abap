*&---------------------------------------------------------------------*
*& Report Z_MM_GOODS_BAD
*& Legacy Inventory Movement and Customer Update
*& Contains MKPF/MSEG, hardcoded MATNR(18), and KNA1 direct modification
*&---------------------------------------------------------------------*
REPORT z_mm_goods_bad.

TABLES: mkpf, mseg, kna1, mara.

* Hardcoded 18-character MATNR definition (R005)
DATA: lv_old_matnr TYPE c LENGTH 18,
      lv_target_matnr(18) TYPE c,
      lt_mseg TYPE STANDARD TABLE OF mseg.

* Direct query on MKPF material document header (R003)
SELECT * FROM mkpf INTO TABLE @DATA(lt_mkpf)
  WHERE mblnr = '5000000001'.

* Direct query on MSEG material document items (R003)
SELECT * FROM mseg INTO TABLE lt_mseg
  WHERE mblnr = '5000000001'.

* Direct modification of standard customer master KNA1 (R004)
UPDATE kna1 SET sortl = 'VIP' WHERE kunnr = '0000100000'.

* Direct modification of standard material master MARA (R009)
UPDATE mara SET mtart = 'FERT' WHERE matnr = 'MAT001'.

WRITE: / 'MM goods receipt verified.'.
