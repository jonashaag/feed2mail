rss2email
---------
rss2email done simple.

Delivers news from feeds (RSS, Atom, ...) to your mail box.

Digested HTML format

**Required Env**
~~~~~~~~~~~~~~

   pip install html2text feedparser

How to use it?
~~~~~~~~~~~~~~
1. ``cp -r rss2email.py config.py /data``.
2. Edit ``config.py``.
3. run in python ``python rss2email.py``
4. Task:

   ``vim crontab``

   ``minute hour day_of_month month day_of_week user_name cd ./location && python rss2email.py``

RSS Link
~~~~~~~~~~~~~~
Science:
   https://www.science.org/action/showFeed?type=axatoc
Nature:
   https://www.science.org/action/showFeed?type=axatoc
   
License?
~~~~~~~~
ISC
