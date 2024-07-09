SENDER_MAIL     = 'Sender Name <sender_email@email.com>'
RECIPIENT_MAIL  = 'recipient_email@email.com'
SMTP_SERVER     = 'smtp.mail.com'
SMTP_USE_TLS    = True
SMTP_PORT       = 587 # can be absent/set to None for the default value
SMTP_USERNAME   = 'smtp_username@email.com'
SMTP_PASSWORD   = 'smtp_password'
# A list of feeds to fetch.
# Items must be `(feed_url, group_name)` tuples.
# Entries of feeds that make a group won't be sent twice of they appear
# on multiple feeds (often seen on News Sites that offer topic feeds)
FEEDS = [
    ('https://www.science.org/action/showFeed?type=axatoc','Science'),
    ('http://feeds.nature.com/nature/rss/current','Nature'),
]