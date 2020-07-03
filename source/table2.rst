Data Table
==========

Table for Fig. 2 in Loebner.

.. 
  comment
   _table_loebner_fig2a:

Each row in the following table lists source cells on the left and destination cells on the top. The first column with numeric values gives the number of source cells. The other entries gives FO, FI. FO is fan-out (number of target cells each source contacts) and FI is fan-in (number source cells going to each target). Currently, all values are for the cat.

.. tblrender:: loebner_fig2a
   :rows: "Source cell", "basket", "golgi", "granule", "purkinje", "stellate"
   :cols: "Target cell", "Cell count", "basket", "golgi", "granule", "purkinje", "stellate"
   :expanded_col_title: "Cell count or Target cell" 
   :description: Number of cells and connections between cells as: *fan-out*, **fan-in**.  Fan-out is	
      number of target cells each source contacts; fan-in is number source cells going to each
      target. All values are for the cat.
   :gridLayout:
      +-------------+----------+------------------------------------------------------------------+
      |             |          |  Target cell                                                     |
      | Source      | Cell     +------------+------------+------------+-------------+-------------+
      | cell        | count    | basket     | golgi      | granule    | purkinje    | stellate    |
      +=============+==========+============+============+============+=============+=============+
      | basket      | 7.5x10^6 |      -     |            |            |9, 7.5x10^6  |             |
      +-------------+----------+------------+------------+------------+-------------+-------------+
      | golgi       |          |            |      -     |5.2x10^3, ? |             |             |
      +-------------+----------+------------+------------+------------+-------------+-------------+
      | granule     |          |?, 3.7x10^3 |?, 5.2x10^3 |      -     |             |?, 3.6x10^3  |
      +-------------+----------+------------+------------+------------+-------------+-------------+
      | purkinje    |          |            |            |            |      -      |             |
      +-------------+----------+------------+------------+------------+-------------+-------------+
      | stellate    |          |            |            |            |             |      -      |
      +-------------+----------+------------+------------+------------+-------------+-------------+

