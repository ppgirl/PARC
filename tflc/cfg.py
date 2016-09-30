__author__ = 'Zhang Shaojun'

import logging
import sys

# log
LOG = logging.getLogger('tflc')
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler(sys.stderr))

# version of TransFormed Layered Controller
TFLC_VERSION_1 = 1

# listening address and port
CC_LISTEN_HOST = ''
CC_LISTEN_PORT = 9696

# WSGI REST service address
WSGI_API_HOST = ''
WSGI_API_PORT = 8080

# state of local controller
LC_STATE_HANDSHAKE = "handshake"
LC_STATE_CONFIG = "config"
LC_STATE_LIVE = "live"
LC_STATE_DEAD = "dead"

# max message id
MAX_XID = 0xffffffff

# max local controller id
MAX_LC_ID = 0xffffffff

# flow dispatch option
FLOW_DISPATCH_STEPBYSTEP = 1

# echo_request interval
ECHO_REQ_INTERVAL = 100

# master-slave-switching interval
MS_SWITCH_INTERVAL = 300