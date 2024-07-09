import feedparser
import email, email.utils, email.mime.text
import smtplib
import html2text
import pickle
import config

class BufferedUnicode(object):
    """
    Simple pseudo unicode string. StringIO wasn't worth importing.
    >>> buf = BufferedUnicode()
    >>> buf += 'hello'
    >>> buf += ' world!'
    >>> buf.as_unicode()
    'hello world!'
    """
    def __init__(self):
        self._buf = []

    def __iadd__(self, other):
        try:
            self._buf.append(str(other))
            return self
        except UnicodeDecodeError:
            raise TypeError('Expected unicode')

    def as_unicode(self):
        return ''.join(self._buf)

def news_content_form(news):
    content = BufferedUnicode()
    # news link
    try:
        content += ('<font size="4"><b><a href="%s">' % news.link)
    except:
        content += ('<font size="4"><a href="%s">' % news.id)
    # news title
    content += news.title + '</a></b></font><br/>'
    # news author
    try:
        content += ('Author: %s...<br/>' % news.author[:40].replace('\n',' '))
    except:
        pass
    # news time
    for time_news in ('updated', 'published', 'created'):
        try:
            content += ('%s time: %s<br/>' % (time_news,news[time_news]))
            break
        except KeyError:
            pass
    # news summary
    try:
        content += ('<b>%s</b><br/>' % html2text.html2text(news.summary))
    except:
        pass
    # content break
    content += '<br><font size="3"> </font><br/>'
    return content.as_unicode()

def mail_content_form(entry):
    body = BufferedUnicode()
    for news in entry:
        body += news_content_form(news)
    return body.as_unicode()

def mail_form(entry,mail_title):
    mail_body = mail_content_form(entry)
    mail = email.mime.text.MIMEText(
        mail_body.encode('utf-8'),
        'html',
        'utf-8'
        )
    mail['To'] = config.RECIPIENT_MAIL
    mail['Subject'] = mail_title
    mail['From'] = config.SENDER_MAIL
    mail['Date'] = email.utils.formatdate(localtime=True)
    return mail.as_string()

def data_compare(feed_content,mail_title):
    try:
        with open('./data/%s' % mail_title,'rb') as file:
            pre_data = pickle.load(file)
    except:
        with open('./data/%s' % mail_title,'wb') as file:
            pickle.dump(feed_content,file)
        return feed_content
    if sorted(pre_data[0]) == sorted(feed_content[0]):
        print('[Warning] No update. Would not send new email.')
        return None
    else:
        with open('./data/%s' % mail_title,'wb') as file:
            pickle.dump(feed_content,file)
        return feed_content

def main():
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
    for feed in config.FEEDS:
        feed_url, mail_title = feed
        print('[Info] Fetching %s: %s' % (mail_title,feed_url))
        feed_content = feedparser.parse(feed_url).entries
        feed_content = data_compare(feed_content,mail_title)
        if feed_content:
            mail_content = mail_form(feed_content,mail_title)
            try:
                print('[Info] Email to %s from %s' % (config.RECIPIENT_MAIL,config.SENDER_MAIL))
                smtp_server.sendmail(
                    config.SENDER_MAIL,
                    config.RECIPIENT_MAIL,
                    mail_content,
                )
            except:
                import traceback
                traceback.print_exc()
    print('[Info] Finish')

if __name__ == '__main__':
    main()