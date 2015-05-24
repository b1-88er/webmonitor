import functools
from fabric.api import *  # pylint: disable=W0401,W0614
from fabric.contrib.files import exists
from StringIO import StringIO
import os


def upload(local_path, remote_path, owner=None, mode='644'):
    """Extended upload functionality.

    Args:
        local_path (object): file path, file object or list of lines
        remote_path (str): target filesystem path
        user (str): target file owner (default: don't change)
        mode (str): target file mode
    """

    if isinstance(local_path, list):
        local_path = StringIO(''.join(['%s\n' % line for line in local_path]))

    basename = 'install_' + os.path.basename(remote_path)
    use_sudo = True if owner is not None else False

    put(local_path, basename, use_sudo=use_sudo)
    if use_sudo:
        sudo('install -m%s -o%s %s %s' % (mode, owner, basename, remote_path))
    else:
        run('install -m%s %s %s' % (mode, basename, remote_path))
    run('rm %s' % basename)


@task
def vagrant():
    # change from the default user to 'vagrant'
    env.user = 'vagrant'
    # connect to the port-forwarded ssh
    env.hosts = ['127.0.0.1:2222']
    # use vagrant ssh key
    result = local('vagrant ssh-config | grep IdentityFile', capture=True)
    env.key_filename = result.split()[1].replace('"', '')


@task
def webmonitor():
    user = functools.partial(sudo, user='webmonitor')

    if not exists('/opt/webmonitor'):
        sudo('useradd -d /opt/webmonitor -m -s /bin/bash webmonitor')

    sudo('touch /var/log/webmonitor.log')
    sudo('chown webmonitor:webmonitor /var/log/webmonitor.log')
    sudo('aptitude install git')

    if not exists('/opt/webmonitor/webmonitor'):
        with cd('/opt/webmonitor'):
            user('git clone https://github.com/eddwardo/webmonitor.git')
    else:
        with cd('/opt/webmonitor/webmonitor'):
            user('git pull origin master')

    sudo('aptitude install -yq python-virtualenv')

    if not exists('/opt/webmonitor/bin/activate'):
        user('virtualenv --system-site-packages /opt/webmonitor')

    with prefix('source /opt/webmonitor/bin/activate'):
        user('pip install --upgrade pip')
        user('pip install -r /opt/webmonitor/webmonitor/requirements.txt')

    sudo('aptitude install -yq supervisor')
    upload(['[program:webmonitor]',
            'user = webmonitor',
            'directory = /opt/webmonitor/webmonitor',
            'command = bash -c "source /opt/webmonitor/bin/activate && python /opt/webmonitor/webmonitor/monitor.py"'],
           '/etc/supervisor/conf.d/webmonitor.conf',
           owner='root')

    sudo('supervisorctl update')
