SENDER_MAIL     = 'send@er.tld'
RECIPIENT_MAIL  = 'rec@ipient.tld'
SMTP_SERVER     = 'ser.ver.tld'
SMTP_PORT       = None # can be absent/set to None for the default value

# A list of feeds to fetch.
# Items might be `(feed_url, group_name)` tuples.
# Entries of feeds that make a group won't be sent twice of they appear
# on multiple feeds (often seen on News Sites that offer topic feeds)
FEEDS = [
    'http://foobar.org/feed.rss',
    'http://blah.com/feed.atom',
    ('http://www.reddit.com/r/python/.rss', 'reddit'),
    ('http://www.reddit.com/r/programming/.rss', 'reddit')
]
