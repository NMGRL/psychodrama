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
                    runner = PsychoDramaRunner()
                    runner.bootstrap(data)
                    break
        else:
            runner = PsychoDramaRunner()
            runner.bootstrap(data)

        return ''

    return bp


def results_blueprint():
    bp = Blueprint('results', __name__, template_folder='templates')

    @bp.route('/results')
    def results():
        return render_template('results.html', results=[])

    return bp


def bootstrap(**app_kwargs):
    # start the flask web app
    app = PsychoDramaApp('PsychoDrama')

    @app.route('/')
    def index():
        return render_template('index.html')

    # setup blueprints
    app.register_blueprint(webhook_blueprint(branches=['develop', 'release-*']))
    app.register_blueprint(results_blueprint())

    # setup database

    # run application
    app.run(**app_kwargs)

# ============= EOF =============================================
