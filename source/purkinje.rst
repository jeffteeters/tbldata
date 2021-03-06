Purkinje Cell
=============

Some text about Purkinje cells...



.. tbldata:: table_loebner_fig2a
   :valrefs: ["Source cell:purkinje", "Cell count", "1.3x10^6", "LoebnerEE-1989"],
             ["Source cell:purkinje", "Target cell:purkinje", "-", "-"]
   :id_prefix: p

   Source cell| Target cell | Value    | Reference
   purkinje   | Cell count  | 1.3x10^6 | LoebnerEE-1989, AlbusJS-1981


And some text after basket cell text.


Test grid table.

Test grid table.

+------------------------+----------------------------------+
|                        |               To Cell            |
+------------------------+------------+----------+----------+
| Header row, column 1   | Header 2   | Header 3 | Header 4 |
| (header rows optional) |            |          |          |
+========================+============+==========+==========+
| body row 1, column 1   | column 2   | column 3 | column 4 |
+------------------------+------------+----------+----------+
| body row 2             | ...        | ...      |          |
+------------------------+------------+----------+----------+



Loebner grid table


Previous version:


+-------------+------------+----------------------------------------------------------------+
|             |            |  Target cell                                                   |
|             |            +------------+------------+------------+------------+------------+
| Source cell | Cell count | basket     | golgi      | granule    | purkinje   | stellate   |
+=============+============+============+============+============+============+============+
| basket      |            |     -      |            |            |            |            |
+-------------+------------+------------+------------+------------+------------+------------+
| golgi       |            |            |      -     |            |            |            |
+-------------+------------+------------+------------+------------+------------+------------+
| granule     |            |            |            |      -     |            |            |
+-------------+------------+------------+------------+------------+------------+------------+
| purkinje    |            |            |            |            |      -     |            |
+-------------+------------+------------+------------+------------+------------+------------+
| stellate    |            |            |            |            |            |     -      |
+-------------+------------+------------+------------+------------+------------+------------+


New version:

+----------+----------+---------------------------------------------------------------------+
|          |          |  Target cell                                                        |
| Source   | Cell     +-------------+-------------+-------------+-------------+-------------+
| cell     | count    | basket      | golgi       | granule     | purkinje    | stellate    |
+==========+==========+=============+=============+=============+=============+=============+
| basket   |          |      -      |             |             |             |             |
+----------+----------+-------------+-------------+-------------+-------------+-------------+
| golgi    |          |             |      -      |             |             |             |
+----------+----------+-------------+-------------+-------------+-------------+-------------+
| granule  |          |             |             |       -     |             |             |
+----------+----------+-------------+-------------+-------------+-------------+-------------+
| purkinje |          |             |             |             |      -      |             |
+----------+----------+-------------+-------------+-------------+-------------+-------------+
| stellate |          |             |             |             |             |      -      |
+----------+----------+-------------+-------------+-------------+-------------+-------------+



Data for Loebner grid table

+---------------+---------------+---------------+--------------------+
|               | Cell count or |               |                    |
| Source cell   | Target cell   | Value         | Reference          |
+===============+===============+===============+====================+
| basket        | Cell count    | 2348          | Loebner-1989       |
+---------------+---------------+---------------+--------------------+
| basket        | golgi         | 276,37878     | Smith-2017         |
+---------------+---------------+---------------+--------------------+



.. comment Notes about :cite:`LoebnerEE-1989` :footcite:`LoebnerEE-1989` .

.. footbibliography::



