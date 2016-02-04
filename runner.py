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
# ============= local library imports  ==========================


class PreRunException(BaseException):
    pass


class RunException(BaseException):
    pass


class PostRunException(BaseException):
    pass


class PsychoDramaRunner:
    def run(self, config):
        if not self._pre_run(config):
            raise PreRunException()

        if not self._run(config):
            raise RunException()

        if not self._post_run(config):
            raise PostRunException()

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


# ============= EOF =============================================



