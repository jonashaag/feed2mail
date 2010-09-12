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

How to use it?
~~~~~~~~~~~~~~
1. ``cp example_config.py config.py``.
2. edit `config.py`.
3. run `feed2mail.py` every *N* seconds/hours/decades.

Dependencies?
~~~~~~~~~~~~~
Only Mark Pilgrim's `Universal Feed Parser`_ and `Universal Encoding Detector`_,
for parsing the feeds.

.. _Universal Feed Parser: http://feedparser.org
.. _Universal Encoding Detector: http://chardet.feedparser.org

I've found a bug!
~~~~~~~~~~~~~~~~~
Great! `Please open a ticket`_.

.. _Please open a ticket: http://github.com/jonashaag/feed2mail/issues/

License?
~~~~~~~~
GPL, Version 2 or greater
