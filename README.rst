feed2mail
---------
rss2email done simple.

Delivers news from feeds (RSS, Atom, ...) to your mail box.

How to install
~~~~~~~~~~~~~~

Simply check out the Git repository or download the Python file.

**Docker**::

   docker build -t feed2mail .

**Alternatively, manual virtualenv**::

   pip install html2text feedparser

How to use it?
~~~~~~~~~~~~~~
1. ``cp example_config.py config.py``.
2. Edit ``config.py``.
3. Run feed2mail every *N* seconds/hours/decades. For Docker setup::

     docker run -v /path/to/your/seen/file:/seen feed2mail
    
   For manual virtualenv setup, simply run ``feed2mail.py``.

I've found a bug!
~~~~~~~~~~~~~~~~~
Great! `Please open a ticket`_.

.. _Please open a ticket: http://github.com/jonashaag/feed2mail/issues/

License?
~~~~~~~~
ISC
