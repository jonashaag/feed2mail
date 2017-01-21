""" Copyright 2010-2013 Jonas Haag <jonas@lophus.org>. ISC-licensed.  """
import os
import sys
import time
import smtplib
import email, email.utils, email.mime.text
import pickle

import feedparser
import html2text

import config


def warn(feed_url, status, msg):
    print >> sys.stderr, \
        'WARNING: %s HTTP %d: %s' % (feed_url, status, msg)

def log(msg):
    print msg


class BufferedUnicode(object):
    """
    Simple pseudo unicode string. StringIO wasn't worth importing.
    >>> buf = BufferedUnicode()
    >>> buf += 'hello'
    >>> buf += u' world!'
    >>> buf.as_unicode()
    'hello world!'
    """
    def __init__(self):
        self._buf = []

    def __iadd__(self, other):
        try:
            self._buf.append(unicode(other))
            return self
        except UnicodeDecodeError:
            raise TypeError('Expected unicode')

    def as_unicode(self):
        return u''.join(self._buf)


def my_html2text(s):
    return html2text.html2text(s.replace('\n', ' '))


def force_plaintext(element):
    if 'html' in element.type:
        return my_html2text(element.value)
    return element.value


def fetch_entries(feed_url, seen_entries):
    log('Fetching %r...' % feed_url)
    feed = feedparser.parse(feed_url)

    if feed.bozo:
        status = feed.get('status', 404)
        if status != 200:
            warn(feed_url, status, feed.bozo_exception)
        if 400 <= status < 600:
            return

    for entry in feed.entries:
        if 'id' not in entry:
            assert entry.link
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
    """
    Returns the first plaintext body that can be found in `entry`,
    or the first HTML body converted to plaintext using ``html2text``
    of none was found.

    Returns ``None`` if no bodies are found at all.
    """
    bodies = entry.get('content', []) + [entry.get('summary_detail')]
    bodies = filter(None, bodies)
    if not bodies:
        return None
    for body in bodies:
        if body.type == 'text/plain':
            return body.value
    return my_html2text(bodies[0].value)


def select_plaintext_title(entry):
    """
    Returns the entry's title, converted to plaintext if needed,
    or ``None`` if no title is found.
    """
    try:
        return force_plaintext(entry['title_detail'])
    except KeyError:
        pass


def select_timestamp(entry):
    """
    Returns the date and time `entry` was updated, published or created
    (respectively) as a time-tuple.
    """
    for attr in ('updated', 'published', 'created'):
        try:
            return entry['%s_parsed'] % attr
        except KeyError:
            pass
    return time.gmtime()


def generate_mail_for_entry(entry):
    # the entry's title:
    title = select_plaintext_title(entry)
    # the entry's content:
    body = select_plaintext_body(entry)
    # the entry's permalink
    link = entry.get('link', entry.id)
    # the date+time the entry was updated/published:
    timestamp = select_timestamp(entry)
    # the entry's feed's title:
    feed_title = force_plaintext(entry.get('feed_title'))
    # the entry's author:
    author = entry.get('author')
    # the feed's author:
    feed_author = entry.get('feed_author')
    # files attached to the entry:
    enclosures = entry.get('enclosures', [])

    subject, author, body = format_mail(
        entry.id,
        link,
        title,
        timestamp,
        author,
        body,
        feed_title,
        feed_author,
        enclosures,
    )

    mail = email.mime.text.MIMEText(
        body.encode('utf-8'),
        'plain',
        'utf-8'
    )
    mail['To'] = config.RECIPIENT_MAIL
    mail['Subject'] = subject
    mail['From'] = email.utils.formataddr((author, config.SENDER_MAIL))
    mail['Date'] = email.utils.formatdate(time.mktime(timestamp))
    mail['X-RSS-Entry-ID'] = entry.id
    return mail


def format_mail(id, link, title, timestamp, author, body,
                feed_title, feed_author, enclosures):
    """
    Returns a `(subject, author, body)` tuple, forming the mail's
    Subject and From headers and the mail's body, respectively.

    All arguments passed expect for `id` and `timestamp` can be ``None``.

    The returned tuple's items *must* be strings (they can be empty, though).
    """
    if not title:
        if body:
            title = body[:70] + '...'
        else:
            title = link

    if feed_title:
        author = feed_title
    else:
        if not author:
            author = feed_author or ''

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
            except (ValueError, AttributeError):
                length = -1
            content += '\nEnclosure: %s (%s, %d bytes)' \
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
        if getattr(config, 'SMTP_USE_TLS', False):
            smtp_server.starttls()
        if hasattr(config, 'SMTP_USERNAME') or hasattr(config, 'SMTP_PASSWORD'):
            smtp_server.login(
                getattr(config, 'SMTP_USERNAME', None),
                getattr(config, 'SMTP_PASSWORD', None)
            )
        for mail in mail_queue:
            log('Sending mail for entry %r...' % mail['X-RSS-Entry-ID'])
            try:
                smtp_server.sendmail(
                    config.SENDER_MAIL,
                    config.RECIPIENT_MAIL,
                    mail.as_string()
                )
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
