import os

project_dir = os.path.abspath(os.path.split(__file__)[0])
tenjin = {'path': [os.path.join(project_dir, 'templates')], }

frontend_port = 7766
frontend_host = '0.0.0.0'

log_file = '/var/log/monitor.log'

monitors = [
    # (url_to_monitor, required string in page content, interval for connections)
    ('http://google.com', 'google', 1),
    ('http://kanary.dev.clearcode.cc', '???', 1.5),
    ('http://cnn.com', 'Police', 4),
]

try:
    from local_settings import *
except ImportError:
    pass
