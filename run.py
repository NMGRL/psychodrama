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
import argparse


def pd(arg_space):
    from psychodrama import bootstrap
    bootstrap(host=arg_space.host,
              port=arg_space.port,
              debug=arg_space.debug)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run PsychoDrama')

    parser.add_argument('--host',
                        type=str,
                        default='127.0.0.1',
                        help='host for Flask')
    parser.add_argument('--port',
                        type=int,
                        default=4567,
                        help='port for Flask')
    parser.add_argument('--debug',
                        action='store_true',
                        default=False,
                        help='run in debug mode')

    pd(parser.parse_args())


# ============= EOF =============================================
