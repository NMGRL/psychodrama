# ===============================================================================
# Copyright 2016 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
import logging
import os
import socket
import subprocess
import time
import sqlite3
import yaml
import json
from datetime import datetime
from git import Repo
from threading import Thread
# ============= local library imports  ==========================
logger = logging.getLogger('psychodrama_runner')


class SupportException(BaseException):
    def __str__(self):
        return 'SupportException'


class PreRunException(BaseException):
    def __str__(self):
        return 'PreRunException'


class RunException(BaseException):
    def __str__(self):
        return 'RunException'


class PostRunException(BaseException):
    def __str__(self):
        return 'PostRunException'


class NoEndpointException(BaseException):
    def __str__(self):
        return 'NoEndpointException'


class SupportCTX(object):
    def __init__(self, root):
        self._root = root

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class PsychoDramaRunner:
    """
    example config

    endpoint: pychron/psycho.sock

    support:
      - root: pychron
      - path: pychron/setupfiles/initialization.xml
        text: "<root>...</root>"
      - path: .enthought/pychron.application.root/preferences.ini
        text: "[pychron.dvc]..."

    environment:
      name: pychron_pd
      dependencies:
        - traits
        - traitsui
        - envisage
        - qt
        - pyside

    pre_run:
      - start_sim:PychronSimulator
      - start_app:PyExperiment

    run:
      - move_laser
      - fire_laser
      - execute_experiment:experiment1

    post_run:
      - stop_sim
      - report_results

    """

    _support_root = None

    def info(self, msg):
        logger.info(msg)

    def debug(self, msg):
        logger.debug(msg)

    def critical(self, msg):
        logger.critical(msg)

    def warning(self, msg):
        logger.warning(msg)

    def bootstrap(self, data):
        self.info('******************* Bootstrap')
        t = Thread(target=self._bootstrap, args=(data,))
        t.setDaemon(1)
        t.start()

    def shutdown(self):
        self.info('******************* Shutdown')
        for k, v in self.processes.iteritems():
            self.debug('kill process {} ({})'.format(k, v))
            subprocess.call(['kill', str(v)])

    # private
    def _bootstrap(self, data):
        """
        example data
        {
  "object_kind": "push",
  "before": "95790bf891e76fee5e1747ab589903a6a1f80f22",
  "after": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
  "ref": "refs/heads/master",
  "checkout_sha": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
  "user_id": 4,
  "user_name": "John Smith",
  "user_email": "john@example.com",
  "user_avatar": "https://s.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?s=8://s.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?s=80",
  "project_id": 15,
  "project":{
    "name":"Diaspora",
    "description":"",
    "web_url":"http://example.com/mike/diaspora",
    "avatar_url":null,
    "git_ssh_url":"git@example.com:mike/diaspora.git",
    "git_http_url":"http://example.com/mike/diaspora.git",
    "namespace":"Mike",
    "visibility_level":0,
    "path_with_namespace":"mike/diaspora",
    "default_branch":"master",
    "homepage":"http://example.com/mike/diaspora",
    "url":"git@example.com:mike/diaspora.git",
    "ssh_url":"git@example.com:mike/diaspora.git",
    "http_url":"http://example.com/mike/diaspora.git"
  },
  "repository":{
    "name": "Diaspora",
    "url": "git@example.com:mike/diaspora.git",
    "description": "",
    "homepage": "http://example.com/mike/diaspora",
    "git_http_url":"http://example.com/mike/diaspora.git",
    "git_ssh_url":"git@example.com:mike/diaspora.git",
    "visibility_level":0
  },
  "commits": [
    {
      "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
      "message": "Update Catalan translation to e38cb41.",
      "timestamp": "2011-12-12T14:27:31+02:00",
      "url": "http://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
      "author": {
        "name": "Jordi Mallach",
        "email": "jordi@softcatala.org"
      },
      "added": ["CHANGELOG"],
      "modified": ["app/controller/application.rb"],
      "removed": []
    },
    {
      "id": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
      "message": "fixed readme",
      "timestamp": "2012-01-03T23:36:29+02:00",
      "url": "http://example.com/mike/diaspora/commit/da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
      "author": {
        "name": "GitLab dev user",
        "email": "gitlabdev@dv6700.(none)"
      },
      "added": ["CHANGELOG"],
      "modified": ["app/controller/application.rb"],
      "removed": []
    }
  ],
  "total_commits_count": 4
}

        :param data:
        :return:
        """
        st = time.time()
        self.info('bootstrap')

        self.processes = {}

        root = '/anaconda'
        if not os.path.isdir(root):
            root = os.path.join(os.path.expanduser('~'), 'anaconda')
            if not os.path.isdir(root):
                root = os.path.join(os.path.expanduser('~'), 'miniconda2')

        if not os.path.isdir(root):
            self.warning('No conda available')
            return

        self._conda_root = root

        ref = data['ref']
        branch = '/'.join(ref.split('/')[2:])

        repo = data['repository']
        url = repo['url']
        name = repo['name']

        self._make_repo(name, url, branch)
        try:
            # pull updates
            self._pull(branch)
        except BaseException, e:
            self._report('failed to pull {}. exception={}'.format(branch, e), data, st)
            return
        # run .psycho.yaml
        try:
            config = self._get_config()
            if config is None:
                self._report('no .psycho.yaml file present', data, st)
                return
        except BaseException, e:
            self._report('failed to get config from branch {}. exception={}'.format(branch, e), data, st)
            return

        try:
            self._exec(config)
        except BaseException, e:
            import traceback
            traceback.print_exc()
            self._report('failed to run branch {}. exception={}'.format(branch, e), data, st)

        self._report('run succeeded', data, st)
        self.shutdown()

    def _make_repo(self, name, url, branch, depth=10):
        self.debug('make repo {}, {}, {}'.format(name, url, branch))

        root = os.path.join(os.path.expanduser('~'), '.psychodrama')
        if not os.path.isdir(root):
            os.mkdir(root)

        root = os.path.join(root, 'repos')
        if not os.path.isdir(root):
            os.mkdir(root)

        self._root = os.path.join(root, name)
        if not os.path.isdir(self._root):
            self._repo = Repo.clone_from(url, self._root, depth=depth, branch=branch)
        else:
            self._repo = Repo(self._root)
            if branch not in self._repo.heads:
                self._repo.create_head(branch)

            head = getattr(self._repo.heads, branch)
            head.checkout()

    def _pull(self, branch):
        self.debug('_pull')
        origin = self._repo.remotes['origin']
        origin.pull(branch)

    def _get_config(self):
        self.debug('get config')
        p = os.path.join(self._root, '.psycho.yaml')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                config = yaml.load(rfile)
            return config

    def _exec(self, config):
        self.debug('_exec')
        self._endpoint = config.get('endpoint')
        if self._endpoint is None:
            raise NoEndpointException()

        # setup conda environment
        self._setup_env(config)

        # setup database
        self._setup_db(config)

        # setup support files
        if not self._support(config):
            raise SupportException()

        with SupportCTX(self._support_root):
            if not self._pre_run(config):
                raise PreRunException()

            if not self._run(config):
                raise RunException()

            if not self._post_run(config):
                raise PostRunException()

    def _setup_env(self, config):
        self.debug('setup env')
        env = config['environment']
        conda = os.path.join(self._conda_root, 'bin', 'conda')

        self.debug('env name={}'.format(env['name']))
        self.debug('conda {}'.format(conda))
        try:
            subprocess.check_call(
                [conda, 'create', '--yes', '-n', env['name'], 'python'])
        except subprocess.CalledProcessError:
            pass

        self._env_path = os.path.join(self._conda_root, 'envs', env['name'])

        ins = [conda, 'install', '-n', env['name'], '--yes']
        ins.extend(env['dependencies'])
        subprocess.check_call(ins)

        pip = os.path.join(self._env_path, 'bin', 'pip')
        for pp in env['pip']:
            subprocess.check_call([pip, 'install', pp])

    def _setup_db(self, config):
        d = config.get('database')
        if d:
            self.debug('setup db')
            path = d['path']
            if os.path.isfile(path):
                os.remove(path)

            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            for sql in d['sql']:
                if ';' in sql:
                    for si in sql.split(';'):
                        cursor.execute(si)
                else:
                    cursor.execute(sql)
            conn.commit()
            conn.close()

    def _support(self, config):
        self.debug('setup support')
        home = os.path.expanduser('~')

        def r_mkdir(p):
            if p and not os.path.isdir(p):
                try:
                    os.mkdir(p)
                except OSError:
                    r_mkdir(os.path.dirname(p))
                    os.mkdir(p)

        def make_path(s):
            path = os.path.join(home, s['path'])
            r_mkdir(os.path.dirname(path))
            return path

        c = config.get('support', [])
        for sd in c:
            if 'text' in sd:
                # this is a file
                path = make_path(sd)
                with open(path, 'w') as wfile:
                    wfile.write(sd['text'])
            elif 'root' in sd:
                self._support_root = os.path.join(home, sd['root'])
            else:
                # this is a directory
                os.mkdir(make_path(sd))

        return True

    def _pre_run(self, config):
        self.info('------------- Pre Run -------------')
        c = config.get('pre_run', [])
        return self._do_steps(c)

    def _run(self, config):
        self.info('------------- Run -------------')
        c = config.get('run', [])
        return self._do_steps(c)

    def _post_run(self, config):
        self.info('------------- Post Run -------------')
        c = config.get('post_run', [])
        return self._do_steps(c)

    def _do_steps(self, steps):
        for step in steps:
            if ':' in step:
                cmd, data = step.split(':')
            else:
                cmd, data = step, None

            getattr(self, '_{}'.format(cmd))(data)

        return True

    def _report(self, msg, data, st):
        self.info("Result message={}".format(msg))
        duration = time.time() - st
        conn = sqlite3.connect('/tmp/results.sqlite3')
        cur = conn.cursor()

        sql = '''select id from resulttbl ORDER by id desc'''
        cur.execute(sql)
        try:
            fid = cur.fetchone()[0]
        except TypeError:
            fid = 1

        sql = '''insert into resulttbl (id, msg, pub_date, duration)
        values ({},'{}', '{}', '{}')'''.format(fid + 1, msg, datetime.now(), duration)

        cur.execute(sql)
        conn.commit()

    # actions
    def _start_app(self, data):
        name = data
        path = os.path.join(self._root, name)
        
        def func():
            os.environ['PYTHONPATH'] = self._root
            process = subprocess.Popen([os.path.join(self._env_path, 'bin', 'python'),
                                        path],
                                       env=os.environ)
            self.processes[name] = process.pid

        t = Thread(target=func)
        t.setDaemon(True)
        t.start()
        # wait until psychodrama plugin launches
        # timeout after 1 min
        st = time.time()
        while time.time() - st < 60:
            self.info('Get Status')
            resp = self._send_action('status')
            if resp == 'READY':
                break
            time.sleep(1)

    def _start_sim(self, data):
        name = '{}_simulator.py'.format(data)
        path = os.path.join(os.path.dirname(__file__), name)
        process = subprocess.Popen(['python', path])
        self.processes[name] = process.pid
        time.sleep(2)

    def _stop_sim(self, data):
        pass

    def _report_results(self, data):
        pass

    def _test_simulator(self, data):
        """
        data should be string in form of <SimulatorKlass>, <port>
        e.g.
           Valve, 8000
        :param data:
        :return:
        """
        self.info('test simulator. data={}'.format(data))
        klass, port = map(str.strip, data.split(','))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', int(port)))
        cmd = {'Valve': ('Open A', 'OK'),
               'Laser': ('Enable', 'OK')}.get(klass)
        if cmd:
            cmd, resp = cmd
            s.send(cmd)
            data = s.recv(4096)
            self.info('{} ==> {}, expected={}'.format(cmd, data, resp))
            s.close()

            assert (data.strip() == resp)

    def _move_to_position(self, data):
        resp = self._send_action('MoveToPosition {}'.format(data))
        assert (resp == 'OK')

    def _enable(self, data):
        resp = self._send_action('Enable')
        assert (resp == 'OK')

    def _disable(self, data):
        resp = self._send_action('Disable')
        assert (resp == 'OK')

    def _execute_experiment(self, data):
        resp = self._send_action('ExecuteExperiment {}'.format(data))
        assert (resp == 'OK')

    def _send_action(self, command, **kw):
        kw['command'] = command
        action = json.dumps(kw)

        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.debug('connect to {}'.format(self._endpoint))
            s.connect(self._endpoint)
        except BaseException, e:
            self.critical(e)
            self.warning('asdfsdfsadf')
            return

        s.settimeout(0.5)

        cmd = '{:02X}{}'.format(len(action), action)
        s.send(cmd)
        resp = s.recv(1024)
        s.close()

        self.debug('Send Action {}==>{}'.format(cmd, resp))
        return resp

# ============= EOF =============================================
