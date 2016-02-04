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
import logging

from twisted.internet.protocol import Protocol


class SimProtocol(Protocol):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def dataReceived(self, data):
        self._handle_data(data)

    def _handle_data(self, data):
        resp = self._generate_response(data)
        self.debug('{} response ==> {}'.format(data, resp))
        self.transport.write(resp)

    def _generate_response(self, data):
        args = data.split(' ')
        cmd, data = args[0], ' '.join(args[1:])

        func = '_{}'.format(cmd.lower())
        if hasattr(self, func):
            func = getattr(self, func)
            return func(data)
        else:
            return 'Invalid Command "{}"'.format(cmd)

# ============= EOF =============================================
