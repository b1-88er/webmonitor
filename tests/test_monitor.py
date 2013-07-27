import pytest
from conftest import defer_with_content, defer_raises
from twisted.internet import reactor, task


@pytest.inlineCallbacks
def test_run_monitor(monitor):
    '''
    check if:
    1. after run monitor, delayed call is scheduled.
    2. Is only this one delayed call is scheduled.
    3. is this delayed call a LoopingCall instance with correct arguments
    '''

    # mock lookup_url function, otherwise reactor can behave differently
    # ex. getPage can lookup for DNS resolve, we don't want to test this
    fake_lookup = lambda: 1
    monitor._lookup_url = fake_lookup

    # invoke running monitor
    yield monitor.run_monitor()

    delayed_calls = reactor.getDelayedCalls()
    # is there only one delayed call ?
    assert len(delayed_calls) == 1
    # check if delayed call is a LoopingCall instance
    assert isinstance(delayed_calls[0].func, task.LoopingCall)
    # with good interval
    assert delayed_calls[0].func.interval == monitor.interval
    # and good function (the same as our mock)
    assert delayed_calls[0].func.f == fake_lookup


@pytest.mark.parametrize(('page_content', 'required', 'state', 'reason'), (
    ('lorem ipsum', 'lorem', 'ok', 'content matched'),
    ('lorem ipsum', 'ipsum', 'ok', 'content matched'),
    ('lorem ipsum', 'asdf', 'error', 'page do not contain configured string'),
))
@pytest.inlineCallbacks
def test_monitor_lookups(monitor, page_content, required, state, reason):
    '''
    test getting page content. checks statuses, reasons, and elapsed time
    '''
    # mock getPage, we dont want to connect with any page during test
    # tests schould run offline, and we don't want to test twisted mechanisms
    monitor._get_page = lambda: defer_with_content(page_content)
    monitor.content = required

    yield monitor._lookup_url()

    assert monitor.status.state == state
    assert monitor.status.reason == reason
    assert monitor.status.elapsed > 0


@pytest.mark.parametrize(('exception', 'exc_args', 'reason'), (
    (TypeError, ('hey!', 'i am exc'), 'hey!, i am exc'),
    (ValueError, ('value', 'error', 'ommited'), 'value, error'),
))
@pytest.inlineCallbacks
def test_monitor_errors(monitor, exception, exc_args, reason):
    '''
    test getting page errors. checks statuses, reasons, and elapsed time
    '''
    # mock for get page, we want to raise some exceptions (except LookupError)
    # and check if states of monitor are errors with good reasons
    monitor._get_page = lambda: defer_raises(exception(*exc_args))

    yield monitor._lookup_url()

    assert monitor.status.state == 'error'
    assert monitor.status.reason == reason
    assert monitor.status.elapsed > 0
