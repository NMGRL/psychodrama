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
import logging


# ============= standard library imports ========================
# ============= local library imports  ==========================
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint

root = logging.getLogger()
root.setLevel(logging.DEBUG)
shandler = logging.StreamHandler()

handlers = [shandler]
NAME_WIDTH = 40
gFORMAT = '%(name)-{}s: %(asctime)s %(levelname)-9s (%(threadName)-10s) %(message)s'.format(NAME_WIDTH)
for hi in handlers:
    hi.setLevel(logging.DEBUG)
    hi.setFormatter(logging.Formatter(gFORMAT))
    root.addHandler(hi)


class Simulator:
    def __init__(self):
        self.logger = logging.getLogger('Simulator')

    def bootstrap(self):
        # load configuration
        self._load_configuration()

        # start reactor
        self._start_reactor()

    # private
    def _load_configuration(self):

        for f, p in (('ValveFactory', 8000),
                     ('SpectrometerFactory', 8001),
                     ('LaserFactory', 8002)):
            mod = __import__('protocols', fromlist=[f])
            klass = getattr(mod, f)
            endpoint = TCP4ServerEndpoint(reactor, p)
            endpoint.listen(klass())

    def _start_reactor(self):
        reactor.run()

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.info(msg)

# ============= EOF =============================================
