import os
import sys
import time
import hashlib
import smtplib
import email, email.utils, email.mime.text
try:
    import cPickle as pickle
except ImportError:
    import pickle

import feedparser
from html2text import html2text

HTTP_NOT_FOUND = 404
HTTP_GONE = 410
HTTP_MOVED_PERMANENTLY = 301
ENCODING = 'ISO-8859-15'

from config import *


def warn(feed_url, msg):
    print >> sys.stderr, \
        'WARNING: [%s] %s' % (feed_url, msg)

def log(msg):
    print msg

def fetch_entries(feed_url, seen_entries):
    log('Fetching %r...' % feed_url)
    feed = feedparser.parse(feed_url)

    if feed.status == HTTP_NOT_FOUND:
        warn(feed_url, 'not found')
        return

    if feed.status == HTTP_GONE:
        warn(feed_url, 'is gone')
        return

    if str(feed.status)[0] in ('4', '5'):
        warn(feed_url, 'unknown HTTP status code %d' % feed.status)

    if feed.status == HTTP_MOVED_PERMANENTLY:
        warn(feed_url, 'has permanently moved to %r' % feed.href)

    for entry in feed.entries:
        if entry.id in seen_entries:
            log('Already saw entry %r' % entry.id)
            continue
        log('Got new entry %r' % entry.id)
        seen_entries.add(entry.id)
        entry['feed_author'] = feed.feed.get('author')
        entry['feed_title'] = feed.feed.get('title_detail')
        yield entry

def select_plaintext_body(entry):
    bodies = entry.get('content', []) + [entry.get('summary_detail')]
    bodies = filter(None, bodies)
    if not bodies:
        return '(no body)'
    for body in bodies:
        if body.type == 'text/plain':
            return body.value
    return html2text(bodies[0].value)

def select_plaintext_title(entry):
    try:
        title = entry.title_detail.value
    except KeyError:
        return
    else:
        if 'html' in entry.title_detail.type:
            title = html2text(title).replace('\n', ' ')
        return title

def select_timestamp(entry):
    for attr in ('updated', 'published', 'created'):
        try:
            return entry['%s_parsed'] % attr
        except KeyError:
            pass
    return time.gmtime()

def generate_mail_for_entry(entry):
    body = select_plaintext_body(entry)
    title = select_plaintext_title(entry) or body[50:] + '...'
    timestamp = select_timestamp(entry)
    feed_title = entry['feed_title'] or ''
    if feed_title:
        if 'html' in feed_title.type:
            feed_title = html2text(feed_title.value).replace('\n', ' ')
        else:
            feed_title = feed_title.value
    author = entry.get('author') or entry['feed_author'] or feed_title

    enclosures = entry.get('enclosures', [])
    if enclosures:
        body += '\n\nEnclosures:\n'
        for enclosure in enclosures:
            body += '%s (%s, %s bytes)' % (
                enclosure.href, enclosure.type, enclosure.type)

    body = '%s\n\n%s' % (entry.link, body)

    mail = email.mime.text.MIMEText(body.encode(ENCODING), 'plain', ENCODING)
    mail['To'] = RECIPIENT_MAIL
    mail['Subject'] = title
    mail['From'] = email.utils.formataddr((author, SENDER_MAIL))
    mail['Date'] = email.utils.formatdate(time.mktime(timestamp))
    mail['X-RSS-Entry-ID'] = entry.id
    return mail

def main():
    if os.path.exists('.seen'):
        with open('.seen', 'r') as fobj:
            seen = pickle.load(fobj)
    else:
        seen = {}
    mail_queue = []

    for feed in FEEDS:
        seen.setdefault(feed, set())
        for entry in fetch_entries(feed, seen[feed]):
            mail_queue.append(generate_mail_for_entry(entry))

    if mail_queue:
        smtp_server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        for mail in mail_queue:
            log('Sending mail for entry %r...' % mail['X-RSS-Entry-ID'])
            try:
                smtp_server.sendmail(SENDER_MAIL, RECIPIENT_MAIL, mail.as_string())
            except:
                import traceback
                traceback.print_exc()

    with open('.seen', 'w') as fobj:
        pickle.dump(seen, fobj)

if __name__ == '__main__':
    main()
