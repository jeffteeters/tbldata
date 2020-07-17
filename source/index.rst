.. pc_data_table documentation master file, created by
   sphinx-quickstart on Wed Nov 13 11:24:02 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pc_data_table's documentation!
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   table2
   basket2a
   golgi
   grannule2a
   purkinje
   stellate2a
   basket2
   grannule
   stellate
   data/basket
   references/references


Hello world.  Below is a data table.


.. _num_cells:

Number of cells in different species
------------------------------------


.. tblrender:: num_cells
   :rows: "Cell type", "basket", "grannule", "stellate"
   :cols: "Species", "cat", "human"
   :expanded_col_title: "Species"
   :description:  Number of cells by species.


Some text between the tables.


..
   comment
   _table_loebner_fig2:

.. tblrender:: loebner_fig2
   :rows: "From cell", "basket", "golgi", "granule", "purkinje", "stellate"
   :cols: "To cell", "# cells", "basket", "golgi", "granule", "purkinje", "stellate"
   :expanded_col_title: "To cell"
   :description: Number of cells and connections between cells as: fan-out, fan-in.  Fan-out is
      number of target cells each source contacts; fan-in is number source cells going to each
      target. All values are for the cat.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
