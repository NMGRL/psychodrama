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
import re
import subprocess

from flask import Flask, Blueprint, request, render_template
# ============= local library imports  ==========================

from runner import PsychoDramaRunner


class PsychoDramaApp(Flask):
    pass


def webhook_blueprint(branches=None):
    """
     if <branches> is None trigger handle webhooks for all branches
     else only for <branches>

    :param branches:
    :return:
    """

    bp = Blueprint('webhook', __name__)

    @bp.route('/payload', methods=['POST'])
    def payload():
        data = request.get_json()
        ref = data.get('ref', '')

        if branches:
            for b in branches:
                bb = 'refs/heads/{}'.format(b)
                if re.match(bb, ref):
                    start_new_run(data)
                    break
        else:
            start_new_run(data)
        return ''

    return bp


def results_blueprint():
    bp = Blueprint('results', __name__, template_folder='templates')

    @bp.route('/results')
    def results():
        return render_template('results.html', results=[])

    return bp


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


def start_new_run(data):
    ref = data['ref']
    branch = ref.split('/')[-1]

    repo = data['repository']
    url = repo['clone_url']
    name = repo['name']

    with RepoCTX(name, url, branch):

        try:
            # pull updates
            pull(branch)
        except BaseException, e:
            report('failed to pull {}. exception={}'.format(branch, e), data)
            return
        # run .psycho.yaml
        try:
            config = get_config()
        except BaseException, e:
            report('failed to get config from branch {}. exception={}'.format(branch, e), data)
            return

        try:
            run(config)
        except BaseException, e:
            report('failed to run branch {}. exception={}'.format(branch, e), data)
            return


def pull(branch):
    subprocess.check_call('git', 'checkout', branch)
    subprocess.check_call('git', 'pull')


def get_config():
    config = {}
    return config


def run(config):
    r = PsychoDramaRunner()
    r.run(config)


def report(msg, data):
    # added report to database
    pass


class PsychoDrama:
    def bootstrap(self):
        # start the flask web app
        app = PsychoDramaApp('PsychoDrama')

        @app.route('/')
        def index():
            return render_template('index.html')

        # setup blueprints
        app.register_blueprint(webhook_blueprint(branches=['develop', 'release-*']))
        app.register_blueprint(results_blueprint())

        # setup database

        app.run(port=4567, debug=True)

# ============= EOF =============================================
