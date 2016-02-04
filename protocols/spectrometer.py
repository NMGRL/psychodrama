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
from twisted.internet.protocol import Factory

from protocols.base import SimProtocol


class SpectrometerProtocol(SimProtocol):
    _dac = 0

    def _getdata(self, data):
        return '12341234'

    def _setdac(self, data):
        SimProtocol._dac = data
        return 'OK'

    def _getdac(self, data):
        return SimProtocol._dac


class SpectrometerFactory(Factory):
    def buildProtocol(self, addr):
        return SpectrometerProtocol()

# ============= EOF =============================================
