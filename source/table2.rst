Data Table
==========

Table for Fig. 2 in Loebner.


.. comment
   _ table_cat_fofi :


.. _table_loebner_fig2a:


Cells and connections in cat
----------------------------

The following table provides counts of cells and connections in the cat cerebellum.
The first two columns (*Source cell* and *Cell count*) are respectively a cell type
and the count (number) of cells of that type.  The values in the rest of the table
give the number of connections from the Source cell to Target cells.  These are
specified as a pair of numbers: FO,FI.  FO is fan-out (number of target cells each
source cell contacts) and FI is fan-in (number of source cells going to each target
cell).  Most of the data is from Figure 2 in :cite:`LoebnerEE-1989`, but new data will
be added.



.. tblrender:: table_loebner_fig2a
   :rows: "Source cell", "basket", "golgi", "granule", "purkinje", "stellate"
   :cols: "Target cell", "Cell count", "basket", "golgi", "granule", "purkinje", "stellate"
   :expanded_col_title: "Cell count or Target cell"
   :ct_offset: 2
   :description:
      Values are either a Cell count, or FO,FI where FO is *fan-out* (number of target cells
      each source cell contacts) and FI is *fan-in* (number of source cells going to each
      target cell).
   :gridLayout:
      +-------------+----------+------------------------------------------------------------------+
      |             |          |  Target cell                                                     |
      | Source      | Cell     +------------+------------+------------+-------------+-------------+
      | cell        | count    | basket     | golgi      | granule    | purkinje    | stellate    |
      +=============+==========+============+============+============+=============+=============+
      | basket      |          |      -     |            |            |             |             |
      +-------------+----------+------------+------------+------------+-------------+-------------+
      | golgi       |          |            |      -     |            |             |             |
      +-------------+----------+------------+------------+------------+-------------+-------------+
      | granule     |          |            |            |      -     |             |             |
      +-------------+----------+------------+------------+------------+-------------+-------------+
      | purkinje    |          |            |            |            |      -      |             |
      +-------------+----------+------------+------------+------------+-------------+-------------+
      | stellate    |          |            |            |            |             |      -      |
      +-------------+----------+------------+------------+------------+-------------+-------------+



..
   comment old text
   The following table has data and references for table :ref:`table_loebner_fig2a_`.
   Values are either a Cell count, or FO,FI where FO is fan-out (number of target cells
   each source cell contacts) and FI is fan-in (number of source cells going to each
   target cell).

   Each row in the following table lists source cells on the left and destination cells
   on the top. The first column with numeric values gives the number of source cells. 
   The other entries gives FO, FI. FO is fan-out (number of target cells each source
   contacts) and FI is fan-in (number source cells going to each target). Currently, 
   all values are for the cat.
   
   Number of cells and connections between cells as: *fan-out*, **fan-in**.  Fan-out is	
   number of target cells each source contacts; fan-in is number source cells going to each
   target. All values are for the cat.
