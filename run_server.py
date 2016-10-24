"""
Run Bottle Server
"""

import bottle
from amoeba import app

bottle.run(app, host="0.0.0.0", port=8888)
