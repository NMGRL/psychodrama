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
import socket
import subprocess
# ============= local library imports  ==========================


class SupportException(BaseException):
    pass


class PreRunException(BaseException):
    pass


class RunException(BaseException):
    pass


class PostRunException(BaseException):
    pass


class NoEndpointException(BaseException):
    pass


class SupportCTX(object):
    def __init__(self, root):
        self._root = root

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.rmdir(self._root)


class RepoCTX(object):
    def __init__(self, name, url, branch, depth=10):
        self._url = url
        self._branch = branch
        self._depth = depth

        root = os.path.join(os.path.expanduser('~'), '.psychodrama')
        if not os.path.isdir(root):
            os.mkdir(root)

        root = os.path.join(root, 'repos')
        if not os.path.isdir(root):
            os.mkdir(root)

        self._root = os.path.join(root, name)

    def __enter__(self):
        # clone the repo
        subprocess.check_call('git', 'clone', self._url,
                              '--depth', self._depth,
                              '--branch', self._branch, self._root)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.rmdir(self._root)


def report(msg, data):
    # added report to database
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

    def bootstrap(self, data):
        ref = data['ref']
        branch = ref.split('/')[-1]

        repo = data['repository']
        url = repo['clone_url']
        name = repo['name']

        with RepoCTX(name, url, branch):

            try:
                # pull updates
                self._pull(branch)
            except BaseException, e:
                report('failed to pull {}. exception={}'.format(branch, e), data)
                return
            # run .psycho.yaml
            try:
                config = self._get_config()
            except BaseException, e:
                report('failed to get config from branch {}. exception={}'.format(branch, e), data)
                return

            try:
                self._exec(config)
            except BaseException, e:
                report('failed to run branch {}. exception={}'.format(branch, e), data)
                return

    def _pull(self, branch):
        subprocess.check_call('git', 'checkout', branch)
        subprocess.check_call('git', 'pull')

    def _get_config(self):
        config = {}
        return config

    def _exec(self, config):
        self._endpoint = config.get('endpoint')
        if self._endpoint is None:
            raise NoEndpointException()

        if not self._support(config):
            if self._support_root:
                os.rmdir(self._support_root)
            raise SupportException()

        with SupportCTX(self._support_root):
            if not self._pre_run(config):
                raise PreRunException()

            if not self._run(config):
                raise RunException()

            if not self._post_run(config):
                raise PostRunException()

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

    def _pre_run(self, config):
        c = config.get('pre_run', [])
        for step in c:
            pass

    def _run(self, config):
        c = config.get('run', [])
        for step in c:
            pass

    def _post_run(self, config):
        c = config.get('post_run', [])
        for step in c:
            pass

    # actions
    def _start_app(self):
        pass

    def _start_sim(self):
        pass

    def _stop_sim(self):
        pass

    def _report_results(self):
        pass

    def _send_action(self, action):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._endpoint)
        s.write(action)
        resp = s.read(1024)
        s.close()
        return resp

# ============= EOF =============================================



