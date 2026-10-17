Installation Guide
==================

Requirements
------------

* Python 3.10 or higher
* ``pip`` package manager

Environment Setup
-----------------

1. **Clone or navigate to the project directory**:

   .. code-block:: powershell

      cd Humanitarian-Data-Schema-Analyser-

2. **Create a Python virtual environment**:

   .. code-block:: powershell

      python -m venv humanitarian_env

3. **Activate the virtual environment**:

   * On Windows (PowerShell):

     .. code-block:: powershell

        .\humanitarian_env\Scripts\Activate.ps1

   * On Linux / macOS:

     .. code-block:: bash

        source humanitarian_env/bin/activate

4. **Install project dependencies**:

   .. code-block:: powershell

      python -m pip install -r requirements.txt

The root requirements file includes runtime, development, and documentation
dependencies. To install only the package and documentation tools instead, use
the ``docs`` extra:

.. code-block:: powershell

   python -m pip install -e ".[docs]"

Building the Documentation
--------------------------

.. code-block:: powershell

   python -m sphinx -b html docs docs/_build/html

Open ``docs/_build/html/index.html`` to browse the generated documentation.
