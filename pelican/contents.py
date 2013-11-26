# -*- coding: utf-8 -*-
from pelican.utils import slugify, truncate_html_words
from pelican.log import *
from pelican.settings import _DEFAULT_CONFIG
from os import getenv
from sys import platform, stdin

from datetime import datetime
from dateutil.parser import parse as dateparse

from hashlib import md5

class Page(object):
    """Represents a page
    Given a content, and metadata, create an adequate object.

    :param content: the string to parse, containing the original content.
    """
    mandatory_properties = ('title',)

    def __init__(self, content, metadata=None, settings=None, filename=None):
        # init parameters
        if not metadata:
            metadata = {}
        if not settings:
            settings = _DEFAULT_CONFIG

        self._content = content
        self.translations = []

        self.status = "published"  # default value

        local_metadata = dict(settings.get('DEFAULT_METADATA', ()))
        local_metadata.update(metadata)

        # set metadata as attributes
        for key, value in local_metadata.items():
            setattr(self, key.lower(), value)
        
        # default author to the one in settings if not defined
        if not hasattr(self, 'author'):
            if 'AUTHOR' in settings:
                self.author = settings['AUTHOR']
            else:
                self.author = getenv('USER', 'John Doe')
                warning("Author of `{0}' unknow, assuming that his name is `{1}'".format(filename or self.title, self.author).decode("utf-8"))

        # manage languages
        self.in_default_lang = True
        if 'DEFAULT_LANG' in settings:
            default_lang = settings['DEFAULT_LANG'].lower()
            if not hasattr(self, 'lang'):
                self.lang = default_lang

            self.in_default_lang = (self.lang == default_lang)

        # create the slug if not existing, fro mthe title
        if not hasattr(self, 'slug') and hasattr(self, 'title'):
            self.slug = slugify(self.title)

        # create save_as from the slug (+lang)
        if not hasattr(self, 'save_as') and hasattr(self, 'slug'):
            if self.in_default_lang:
                self.save_as = '%s.html' % self.slug
                clean_url = '%s/' % self.slug
            else:
                self.save_as = '%s-%s.html' % (self.slug, self.lang)
                clean_url = '%s-%s/' % (self.slug, self.lang)

        # change the save_as regarding the settings
        if settings.get('CLEAN_URLS', False):
            self.url = clean_url
        elif hasattr(self, 'save_as'):
            self.url = self.save_as

        if filename:
            self.filename = filename

        # manage the date format
        if not hasattr(self, 'date_format'):
            if hasattr(self, 'lang') and self.lang in settings['DATE_FORMATS']:
                self.date_format = settings['DATE_FORMATS'][self.lang]
            else:
                self.date_format = settings['DEFAULT_DATE_FORMAT']

        if hasattr(self, 'date'):
            if platform == 'win32':
                self.locale_date = self.date.strftime(self.date_format.encode('ascii','xmlcharrefreplace')).decode(stdin.encoding)
            else:
                self.locale_date = self.date.strftime(self.date_format.encode('ascii','xmlcharrefreplace')).decode('utf')
        
        # manage status
        if not hasattr(self, 'status'):
            self.status = settings['DEFAULT_STATUS']

        # set summary
        if not hasattr(self, 'summary'):
            self.summary = truncate_html_words(self.content, 50)

    def check_properties(self):
        """test that each mandatory property is set."""
        for prop in self.mandatory_properties:
            if not hasattr(self, prop):
                raise NameError(prop)

    @property
    def content(self):
        if hasattr(self, "_get_content"):
            content = self._get_content()
        else:
            content = self._content
        return content


class Article(Page):
    mandatory_properties = ('title', 'date', 'category')


class Quote(Page):
    base_properties = ('author', 'date')
    
class Comment(Page):
    mandatory_properties = ('author', 'date', 'slug', 'lang', )
    
    def __init__(self, content, metadata=None, settings=None, msg=None):
        # init parameters
        if not metadata:
            metadata = {}
        if not settings:
            settings = _DEFAULT_CONFIG

        self._content = content

        local_metadata = dict(settings.get('DEFAULT_METADATA', ()))
        local_metadata.update(metadata)

        # set metadata as attributes
        for key, value in local_metadata.items():
            setattr(self, key.lower(), value)

        if msg:
            self.msg = msg

        # manage the date format
        if hasattr(self, 'lang') and self.lang in settings['DATE_FORMATS']:
            self.date_format = settings['DATE_FORMATS'][self.lang]
        else:
            self.date_format = settings['DEFAULT_DATE_FORMAT']
            
        if not hasattr(self, 'id'):
            setattr(self, 'id', md5(self._content.encode('utf8')).hexdigest())
        
        if not hasattr(self, 'parent'):
            setattr(self, 'parent', 0)

        if not hasattr(self, 'date'):
            setattr(self, 'date', dateparse(msg['date']))
#            setattr(self, 'date', datetime.strptime(msg['date'], "%X %x"))

        if hasattr(self, 'website') and getattr(self, 'website').strip() == u"http://":
            setattr(self, 'website', u"")
      
        self.locale_date = self.date.strftime(self.date_format.encode('ascii','xmlcharrefreplace')).decode('utf')


def is_valid_content(content, f):
    try:
        content.check_properties()
        return True
    except NameError, e:
        error(u"Skipping %s: impossible to find informations about '%s'" % (f, e))
        return False
