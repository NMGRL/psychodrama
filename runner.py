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
import os
import shutil
import socket
import subprocess

# ============= local library imports  ==========================
import yaml
from git import Repo


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


def report(msg, data):
    # added report to database
    print msg
    with open('.results.txt', 'a') as afile:
        afile.write(msg)


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

    def bootstrap(self, data):
        self._conda_root = '/anaconda'

        ref = data['ref']
        branch = '/'.join(ref.split('/')[2:])

        repo = data['repository']
        url = repo['clone_url']
        name = repo['name']

        self._make_repo(name, url, branch)

        try:
            # pull updates
            self._pull(branch)
        except BaseException, e:
            report('failed to pull {}. exception={}'.format(branch, e), data)
            return
        # run .psycho.yaml
        try:
            config = self._get_config()
            if config is None:
                report('no .psycho.yaml file present', data)
                return
        except BaseException, e:
            report('failed to get config from branch {}. exception={}'.format(branch, e), data)
            return

        try:
            self._exec(config)
        except BaseException, e:
            import traceback
            traceback.print_exc()
            report('failed to run branch {}. exception={}'.format(branch, e), data)
            return

    def _make_repo(self, name, url, branch, depth=10):
        root = os.path.join(os.path.expanduser('~'), '.psychodrama')
        if not os.path.isdir(root):
            os.mkdir(root)

        root = os.path.join(root, 'repos')
        if not os.path.isdir(root):
            os.mkdir(root)

        self._root = os.path.join(root, name)
        if not os.path.isdir(self._root):
            self._repo = Repo.clone_from(url, self._root, depth=depth, branch=branch)
            # clone the repo
            # subprocess.check_call(['git', 'clone', url,
            #                        '--depth', str(depth),
            #                        '--branch', branch, self._root])
        else:
            self._repo = Repo(self._root)
            if branch not in self._repo.heads:
                self._repo.create_head(branch)

            head = getattr(self._repo.heads, branch)
            head.checkout()

    def _pull(self, branch):
        origin = self._repo.remotes['origin']
        origin.pull(branch)

        # print 'checkout', subprocess.check_output(['cd', self._root, ';', 'git', 'checkout', branch])
        # print 'pull', subprocess.check_output(['cd', self._root, ';', 'git', 'pull', 'origin', branch])

    def _get_config(self):
        p = os.path.join(self._root, '.psycho.yaml')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                config = yaml.load(rfile)
            return config

    def _exec(self, config):
        self._endpoint = config.get('endpoint')
        if self._endpoint is None:
            raise NoEndpointException()

        # setup conda environment
        self._setup_env(config)

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
        env = config['environment']
        try:
            subprocess.check_call(
                ['{}/bin/conda'.format(self._conda_root), 'create', '--yes', '-n', env['name'], 'python'])
        except subprocess.CalledProcessError:
            pass

        ins = ['{}/bin/conda'.format(self._conda_root), 'install', '-n', env['name'], '--yes']
        ins.extend(env['dependencies'])
        subprocess.check_call(ins)

    def _support(self, config):
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
        print '------------- Pre Run -------------'
        c = config.get('pre_run', [])
        return self._do_steps(c)

    def _run(self, config):
        print '------------- Run -------------'
        c = config.get('run', [])
        return self._do_steps(c)

    def _post_run(self, config):
        print '------------- Post Run -------------'
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

    # actions
    def _start_app(self, data):
        pass

    def _start_sim(self, data):
        pass

    def _stop_sim(self, data):
        pass

    def _report_results(self, data):
        pass

    def _send_action(self, action):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._endpoint)
        s.write(action)
        resp = s.read(1024)
        s.close()
        return resp

# ============= EOF =============================================
