.. pc_data_table documentation master file, created by
   sphinx-quickstart on Wed Nov 13 11:24:02 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pc_data_table's documentation!
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   basket2
   grannule
   stellate
   data/basket
   references/references


Hello world.  Below is a data table.


.. _table_num_cells:

.. tblrender:: num_cells
   :rows: "Cell type", "basket", "grannule", "stellate"
   :cols: "Species", "cat", "human"


Some text between the tables.


.. _table_loebner_fig2:

.. tblrender:: loebner_fig2
   :rows: "From cell", "basket", "golgi", "granule", "purkinje", "stellate"
   :cols: "To cell", "# cells", "basket", "golgi", "granule", "purkinje", "stellate" 


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
