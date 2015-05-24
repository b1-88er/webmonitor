import sys
from time import time

import tenjin
from tenjin.helpers import to_str, escape
from tenjin.escaped import as_escaped
# omit pyflake unused error
tenjin_template_tags = [to_str, escape, as_escaped]
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.python import log
from twisted.web.client import getPage, HTTPClientFactory
from twisted.web.server import Site
from twisted.web.resource import Resource

import config

class Status(object):
    def __init__(self):
        self.state = ''
        self.reason = ''
        self.elapsed = 0


class WebMonitor(object):

    '''
    Monitors web availability with given frequency.
    '''
    def __init__(self, url, required_content, interval):
        '''
        :param url: (str) url to monitor
        :param required_content: (str)what string should be on the site on each
        request
        :param interval: (float) delay between requests for site
        '''
        self.url = url
        self.content = required_content
        self.interval = interval
        self.status = Status()

    def run_monitor(self):
        '''
        runs self._lookup_url method periodically with self.interval interval.
        Monitoring will be start as soon as possible (immediately)
        '''
        loop = LoopingCall(self._lookup_url)
        loop.start(self.interval, now=True)

    def _get_page(self):
        '''
        Get content of page on self.url. It must be a valid url (starts with
        http:// prefix).

        :returns: (str) fires deferred and returns page content
        '''
        return getPage(self.url)

    def _lookup_url(self):
        '''
        tries to get a page content defined in self.url
        sets statuses in self.status


        if page contains required content:
        self.status.state = 'ok'
        self.status.reason = 'content matched'

        if page got retrieved correctly but doesn't contains required string:
        self.status.state = 'error'
        self.status.reason = 'page do not contain configured string'

        if some other error occurs (DNS lookup error, Connection Error, 401..)
        self.status.state = 'error'
        self.status.reason = first two arguments from Exception instance

        Every request is measured and defined in self.state.elapsed in seconds.
        '''
        def validate(content):
            '''
            Checks if page content has a self.content string.
            If not raises LookupError, else sets "ok" status.
            '''
            if self.content not in content:
                raise LookupError()

            self.status.state = 'ok'
            self.status.reason = 'content matched'
            log.msg('[OK] %s' % self.url)

        def invalid_response(failure):
            '''
            Handles every errors while validating page content.

            This failure passes quietly, be careful.
            '''
            self.status.state = 'error'

            if failure.check(LookupError):
                self.status.reason = 'page do not contain configured string'
            else:
                self.status.reason = ", ".join(failure.value.args[:2])

            log.msg('[FAIL] %s' % self.status.reason)

        def update_time(_, request_time):
            '''
            update status witch time which passed for given url request
            '''
            elapsed = time() - request_time
            self.status.elapsed = elapsed
            log.msg('Request time processing %s sec.' % elapsed)

        log.msg('Request for: %s' % self.url)

        # mark page in pending status
        self.status.state = 'pending'
        self.status.reason = ''
        self.status.elapsed = 0
        d = self._get_page()
        d.addCallback(validate)
        d.addErrback(invalid_response)
        d.addBoth(update_time, time())
        return d

class Monitors(Resource):
    '''
    renders statuses of every monitor
    '''
    isLeaf = True

    def __init__(self, monitors):
        self.monitors = monitors
        self.render_engine = tenjin.Engine(**config.tenjin)

    @property
    def statuses(self):
        return [(m.url, m.status) for m in monitors]

    def render_GET(self, request):
        ctx = {'statuses': self.statuses}
        html = self.render_engine.render('main.html', ctx)
        return html


if __name__ == "__main__":
    log.startLogging(open(config.log_file, 'w+'))
    HTTPClientFactory.noisy = False

    monitors = [WebMonitor(*args) for args in config.monitors]
    [m.run_monitor() for m in monitors]
    reactor.listenTCP(
        config.frontend_port,
        Site(Monitors(monitors)),
        interface=config.frontend_host
    )
    reactor.run()
