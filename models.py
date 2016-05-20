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
from flask.ext.sqlalchemy import SQLAlchemy

from psychodrama import app

db = SQLAlchemy(app)


def create_db():
    db.create_all()


class ResultTbl(db.Model):
    __tablename__ = 'ResultTbl'
    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.BLOB)
    pub_date = db.Column(db.DateTime)
    status = db.Column(db.String(80))
    duration = db.Column(db.FLOAT)

    @property
    def fduration(self):
        return '{:0.1f}'.format(self.duration)

# ============= EOF =============================================
