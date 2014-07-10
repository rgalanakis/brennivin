.. include:: _copied_readme.rst

.. image:: _static/logo.png
    :alt: logo
    :align: right

.. _a-mods:

Brennivin's modules
===================

Brennivin includes a number of useful utility modules
that augment the Python libraries with similar names.
Others are just plain handy.
Here's a rundown of what's included:

- :mod:`brennivin.dochelpers` provides functions for creating prettier documentation,
- :mod:`brennivin.ioutils` provides retry and timeout decorators,
- :mod:`brennivin.itertoolsext` provides functions for working with iterables,
  like ``first``, ``last``, and all sorts of other useful things
  (it's probably the most useful module in here).
- :mod:`brennivin.logutils` has helpful formatters,
  and functions for working with and cleaning up timestamped log files,
- :mod:`brennivin.nicenum` provides pretty number and memory formatting,
- :mod:`brennivin.osutils` has functions that should be on ``os`` and ``os.path`` in the first place,
  such as a recursive file lister, and context manager to change the cwd,
  and more.
- :mod:`brennivin.platformutils` has a few functions to tell you about the process and OS/hardware,
- :mod:`brennivin.preferences` provides an object that will serialize preferences,
- :mod:`brennivin.pyobjcomparer` allows the comparison of complex Python objects,
  such as when you need to compare floats with a tolerance,
  but those floats are in deeply nested data structures,
- :mod:`brennivin.testhelpers` has gobs of useful assertion methods
  (numbers, sequences, folders, files), and other nice helpers,
- :mod:`brennivin.threadutils` has a not-crap Thread class that can raise
  exceptions instead of swalling them,
  a restartable timer,
  and mechanisms for communication such as tokens and signals.
- :mod:`brennivin.traceback2` is like the ``traceback`` module but will
  include locals, and has more controls for formatting,
- :mod:`brennivin.yamlext` contains some helpers for simplifying yaml reading/writing,
- and :mod:`brennivin.zipfileutils` has useful functions for creating zip files
  that you wish were on the ``zipfile`` module.

There's a lot more useful functionality in each of these modules
than what's listed above, so check them out!

And in a neater form:

.. toctree::
   :maxdepth: 1

   brennivin.dochelpers
   brennivin.ioutils
   brennivin.itertoolsext
   brennivin.logutils
   brennivin.nicenum
   brennivin.osutils
   brennivin.platformutils
   brennivin.preferences
   brennivin.pyobjcomparer
   brennivin.testhelpers
   brennivin.threadutils
   brennivin.traceback2
   brennivin.yamlext
   brennivin.zipfileutils

About the name
==============

You can learn about the Icelandic schnapps called "brennivin"
on Wikipedia. It literally translates to "burnt wine."

The reason for this library's name is that CCP developed an
Open Source framework named `sake`_ while working on Dust514
(the game was primarily developed in China).
As EVE was developed in Iceland
(remember brennivin is mostly utilities harvested from EVE),
I thought "brennivin" was a fitting name for this library.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _sake: https://code.google.com/p/sake/
