feed2mail
---------
rss2email done simple.

What is it?
~~~~~~~~~~~
It's a tool that delivers news from feeds (RSS, Atom, ...) to your mail box.

Why?
~~~~
rss2email had some unicode bug. I tried to fix it but I couldn't because I
vomited and fainted when I saw the code. 
So I wrote this clone with simplicity and beauty in mind.

How to install
~~~~~~~~~~~~~~
::

   pip install html2text feedparser

How to use it?
~~~~~~~~~~~~~~
1. ``cp example_config.py config.py``.
2. edit `config.py`.
3. run `feed2mail.py` every *N* seconds/hours/decades.

I've found a bug!
~~~~~~~~~~~~~~~~~
Great! `Please open a ticket`_.

.. _Please open a ticket: http://github.com/jonashaag/feed2mail/issues/

License?
~~~~~~~~
ISC
