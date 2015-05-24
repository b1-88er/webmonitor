import pytest
from twisted.internet import defer

from webmonitor.monitor import WebMonitor

def defer_with_content(content):
    '''
    return given content via deferred
    '''
    d = defer.Deferred()
    d.callback(content)
    return d

def defer_raises(exc_instance):
    '''
    raises exception inside a deferred chain, use this for checking your
    errbacks
    '''
    def _raise(ignored):
        raise exc_instance

    d = defer.Deferred()
    d.addCallback(_raise)
    d.callback(None)
    return d

@pytest.fixture(scope='function')
def monitor(request):
    monitor = WebMonitor('http://foo.com', 'lorem', 1)
    return monitor
