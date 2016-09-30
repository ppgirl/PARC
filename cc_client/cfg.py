__author__ = 'Zhang Shaojun'

# listening address and port
CC_HOST = '192.168.124.1'
CC_PORT = 9696

# max message id
MAX_XID = 0xffffffff

# version of TransFormed Layered Controller
TFLC_VERSION_1 = 1

# packet_out timeout event
PACKET_OUT_TIMEOUT = 65536

# load_report interval
LOAD_REPORT_INTERVAL = 10

# the window datapath and corresponding out port
DPID_2_IS_WIN = {1: False, 2: False, 3: True, 4: True, 5: False, 6: False}
DPID_2_OUT_PORT = {3: 4, 4: 3}

