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
import chardet

from html2text import html2text
html2text = (lambda func: lambda html: func(html).replace('\n', ' '))(html2text)

import config

HTTP_NOT_FOUND = 404
HTTP_GONE = 410
HTTP_MOVED_PERMANENTLY = 301


def warn(feed_url, msg):
    print >> sys.stderr, \
        'WARNING: [%s] %s' % (feed_url, msg)

def log(msg):
    print msg

class BufferedUnicode(object):
    def __init__(self):
        self._buf = []

    def __iadd__(self, other):
        try:
            self._buf.append(unicode(other))
            return self
        except UnicodeDecodeError:
            raise TypeError('Expected Unicode')

    def as_unicode(self):
        return u''.join(self._buf)

def force_unicode(string):
    if not string or isinstance(string, unicode):
        return string
    # first, try a few common encodings
    for encoding in ('utf-8', 'iso-8859-15'):
        try:
            return string.decode(encoding)
        except UnicodeDecodeError:
            pass
    # then, use chardet to detect the encoding.
    result = chardet.detect(s)
    if result is not None:
        try:
            return string.decode(result['encoding'])
        except UnicodeDecodeError:
            pass

    # if *everything* fails, we can't do any more but
    # ignore unknown characters. :(
    return string.decode('utf-8', 'replace')

def force_plaintext(element):
    if 'html' in element.type:
        return html2text(element.value)
    return element.value

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
        if 'id' not in entry:
            entry.id = entry.link
        if entry.id in seen_entries:
            log('Already saw entry %r' % entry.id)
            continue
        log('Got new entry %r' % entry.id)
        seen_entries.add(entry.id)
        try: entry['feed_author'] = feed.feed['author']
        except KeyError: pass
        try: entry['feed_title'] = feed.feed['title_detail']
        except KeyError: pass
        yield entry

def select_plaintext_body(entry):
    bodies = entry.get('content', []) + [entry.get('summary_detail')]
    bodies = filter(None, bodies)
    if not bodies:
        return None
    for body in bodies:
        if body.type == 'text/plain':
            return body.value
    return html2text(bodies[0].value)

def select_plaintext_title(entry):
    try:
        return force_plaintext(entry['title_detail'])
    except KeyError:
        pass

def select_timestamp(entry):
    for attr in ('updated', 'published', 'created'):
        try:
            return entry['%s_parsed'] % attr
        except KeyError:
            pass
    return time.gmtime()

def generate_mail_for_entry(entry):
    # the entry's content:
    body = force_unicode(select_plaintext_body(entry))
    # the entry's title:
    title = force_unicode(select_plaintext_title(entry))
    # the date+time the entry was updated/published:
    timestamp = select_timestamp(entry)
    # the entry's feed's title:
    feed_title = force_unicode(force_plaintext(entry.get('feed_title')))
    # the entry's author:
    author = force_unicode(entry.get('author'))
    # the feed's author:
    feed_author = force_unicode(entry.get('feed_author'))
    # files attached to the entry:
    enclosures = entry.get('enclosures', [])

    subject, author, body = format_mail(
        entry.id, entry.link, title, timestamp, author,
        body, feed_title, feed_author, enclosures
    )

    subject, author, body = map(force_unicode, (subject, author, body))

    mail = email.mime.text.MIMEText(body, 'plain', 'ISO-8859-15')
    mail['To'] = config.RECIPIENT_MAIL
    mail['Subject'] = title
    mail['From'] = email.utils.formataddr((author, config.SENDER_MAIL))
    mail['Date'] = email.utils.formatdate(time.mktime(timestamp))
    mail['X-RSS-Entry-ID'] = entry.id
    return mail

def format_mail(id, link, title, timestamp, author, body,
                feed_title, feed_author, enclosures):
    if not title:
        if body:
            title = body[:70] + '...'
        else:
            title = link

    if not author:
        author = feed_author or ''

    if feed_title:
        title = feed_title + ': ' + title

    content = BufferedUnicode()
    content += title + '\n' + (link or id)
    if enclosures:
        content += '[%d enclosures]' % len(enclosures)

    if body:
        content += '\n\n'
        content += body
        content += '\n'

    if enclosures:
        content += '-' * 20
        for enclosure in enclosures:
            try:
                length = int(float(enclosure.length))
            except ValueError:
                length = -1
            content += 'Enclosure: %s (Type: %s, Size: %d)' \
                        % (enclosure.href, enclosure.type, length)

    return title, author, content.as_unicode()


format_mail = getattr(config, 'format_mail', format_mail)


def main():
    if os.path.exists('.seen'):
        with open('.seen', 'r') as fobj:
            seen = pickle.load(fobj)
    else:
        seen = {}

    mail_queue = []

    for feed in config.FEEDS:
        if isinstance(feed, (list, tuple)):
            feed, feed_id = feed
        else:
            feed_id = feed
        seen.setdefault(feed_id, set())
        for entry in fetch_entries(feed, seen[feed_id]):
            mail_queue.append(generate_mail_for_entry(entry))

    mails = len(mail_queue)
    sent = error = 0
    if mails:
        smtp_server = smtplib.SMTP(
            config.SMTP_SERVER,
            getattr(config, 'SMTP_PORT', None)
        )
        for mail in mail_queue:
            log('Sending mail for entry %r...' % mail['X-RSS-Entry-ID'])
            try:
                smtp_server.sendmail(SENDER_MAIL, RECIPIENT_MAIL, mail.as_string())
                sent += 1
            except:
                import traceback
                traceback.print_exc()
                error += 1

    log('-' * 20)
    log('Sent %d of %d mails (%d errors)' % (sent, mails, error))

    with open('.seen', 'w') as fobj:
        pickle.dump(seen, fobj)

if __name__ == '__main__':
    main()
