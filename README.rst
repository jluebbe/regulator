Welcome to regulator
====================

|build-status| |coverage-status|

Purpose
-------

Regulator is a text-based tool to decode and annotate register dumps.
The main focus is on minimal user interaction and an expressive layout
definition.

From this hex dump (as produced by memedit)::

   ->map 0x2600000 0x200000
   mapping offset 0x02600000 (size 0x200000)
   ->md 0x0 0x100
   00000000: 00000761 00000000 00000000 00000000 a...............

And this layout definition:

.. code-block:: yaml

   clusters:
     IPU_Base:
       size: 0xe8
       word_size: 4
       types:
         r32 IPUx_CONF:
           fields:
             u1 00: CSI0_EN
             u1 01: CSI1_EN
             u1 02: IC_EN
             u1 03: IRT_EN
             u1 05: DP_EN
             u1 06: DI0_EN
             u1 07: DI1_EN
             u1 08: SMFC_EN
             u1 09: DC_EN
             u1 10: DMFC_EN
             u1 28:
               name: CSI0_DATA_SOURCE
               enum:
                 0: Parallel interface is connected to CSI0
                 1: MCT (MIPI) is connected to CSI0
         r32 IPUx_SISG_CTRL0:
           fields:
             u1 00: VSYNC_RST_CNT
             u3 01…03: NO_VSYNC_2_STRT_CNT
       registers:
         r32 0x00: IPUx_CONF
         r32 0x04: IPUx_SISG_CTRL0
   instances:
     IPU_Base 0x2600000: IPU1_Base

Regulator produces this output::

   parser base set to 0x2600000
   02600000: 00000761 -------- -------- -------- # IPUx_CONF
   02600000: 00       = ...0_...._...._...._...._...._...._.... # CSI0_DATA_SOURCE: 0 = Parallel interface is connected to CSI0 
   02600000:     07   = ...._...._...._...._...._.1.._...._.... # DMFC_EN: 1
   02600000:     07   = ...._...._...._...._...._..1._...._.... # DC_EN: 1
   02600000:     07   = ...._...._...._...._...._...1_...._.... # SMFC_EN: 1
   02600000:       61 = ...._...._...._...._...._...._0..._.... # DI1_EN: 0
   02600000:       61 = ...._...._...._...._...._...._.1.._.... # DI0_EN: 1
   02600000:       61 = ...._...._...._...._...._...._..1._.... # DP_EN: 1
   02600000:       61 = ...._...._...._...._...._...._...._0... # IRT_EN: 0
   02600000:       61 = ...._...._...._...._...._...._...._.0.. # IC_EN: 0
   02600000:       61 = ...._...._...._...._...._...._...._..0. # CSI1_EN: 0
   02600000:       61 = ...._...._...._...._...._...._...._...1 # CSI0_EN: 1
   02600000: -------- 00000000 -------- -------- # IPUx_SISG_CTRL0
   02600004:       00 = ...._...._...._...._...._...._...._000. # NO_VSYNC_2_STRT_CNT: 0
   02600004:       00 = ...._...._...._...._...._...._...._...0 # VSYNC_RST_CNT: 0

Documentation
-------------

Currently none, except for this README.

Contributing
------------

Send a pull request.

Quickstart
----------

Install the dependencies:

.. code-block:: bash

   $ sudo apt install libgirepository1.0-dev

Clone the git repository:

.. code-block:: bash

   $ git clone https://github.com/jluebbe/regulator

Create and activate a virtualenv for regulator:

.. code-block:: bash

   $ virtualenv -p python3 venv
   $ source venv/bin/activate

Install regulator into the virtualenv:

.. code-block:: bash

   $ pip install pygobject
   $ pip install -e .

Then there are several ways to start regulator:

1. Pass the hexdump on stdin:

   .. code-block:: bash

     $ regulator input your-layoutfile.yaml < your-hexdump

2. Decode the content of a file every time it changes on disk:

   .. code-block:: bash

     $ regulator log your-layoutfile.yaml the-file-to-watch

3. Decode the contents of the primary clipboard selection buffer every time it changes:

   .. code-block:: bash

     $ regulator selection your-layoutfile.yaml

Example layout files can be found in the ``layouts/`` folder.

Tests can be run via:

.. code-block:: bash

   $ tox

.. |build-status| image:: https://api.travis-ci.com/jluebbe/regulator.svg?branch=master
    :alt: build status
    :target: https://travis-ci.com/jluebbe/regulator

.. |coverage-status| image:: https://codecov.io/gh/jluebbe/regulator/branch/master/graph/badge.svg
    :alt: coverage status
    :target: https://codecov.io/gh/jluebbe/regulator
