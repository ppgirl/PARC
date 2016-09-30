__author__ = 'Zhang Shaojun'

import socket
import time
import random
from ryu.lib import hub
import cfg
import msg_proto
import msg_proto_parser
import msg_handler

def _deactivate(method):
    def deactivate(self):
        try:
            method(self)
        finally:
            self.is_live = False
    return deactivate

class CentralCtrlAgent(object):
    def __init__(self, logger):
        super(CentralCtrlAgent, self).__init__()
        self.logger = logger
        self.is_live = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.send_q = hub.Queue(16)
        self.xid = random.randint(0, cfg.MAX_XID)

    @_deactivate
    def _recv_loop(self):
        buf = bytearray()
        required_len = msg_proto.TFLCP_HEADER_SIZE
        count = 0
        while self.is_active:
            ret = self.sock.recv(required_len)
            if len(ret) == 0:
                self.logger.info("cc_agent: connection dropped")
                self.is_active = False
                break
            buf += ret
            while len(buf) >= required_len:
                (version, msg_type, msg_len, xid) = msg_proto_parser.header(buf)
                required_len = msg_len
                if len(buf) < required_len:
                    break

                msg_handler.msg_handler[msg_type](self, version, msg_type, msg_len, xid, buf)

                buf = buf[required_len:]
                required_len = msg_proto.TFLCP_HEADER_SIZE
                # methods to schedule other greenlets
                count += 1
                if count > 512:
                    count = 0
                    hub.sleep(0)

    @_deactivate
    def _send_loop(self):
        count = 0
        try:
            while self.is_live:
                buf = self.send_q.get()
                self.sock.sendall(buf)
        finally:
            q = self.send_q
            self.send_q = None
            try:
                while q.get(block=False):
                    pass
            except hub.QueueEmpty:
                pass

    def send(self, buf):
        if self.send_q:
            self.send_q.put(buf)

    def set_xid(self, msg):
        self.xid += 1
        self.xid &= cfg.MAX_XID
        msg.set_xid(self.xid)
        return self.xid

    def send_msg(self, msg):
        if msg.xid is None:
            self.set_xid(msg)
        msg.serialize()
        self.logger.debug("cc_agent: send message: %s", msg.__class__.__name__)
        self.send(msg.buf)

    def serve(self):
        while True:
            try:
                self.sock.connect((cfg.CC_HOST, cfg.CC_PORT))
                self.logger.info("cc_agent: connection to the central controller: success! ")
                self.is_live = True
                break
            except:
                self.logger.info("cc_agent: connection failed, maybe the central controller doesn't start, retry ...")
                time.sleep(5)

        send_thread = hub.spawn(self._send_loop)

        # send hello_up message immediately
        hello_up = msg_proto_parser.TFLCPHelloUp(self)
        self.send_msg(hello_up)

        try:
            self._recv_loop()
        finally:
            hub.kill(send_thread)
            hub.joinall([send_thread])

#    def start_cc_agent(self):
#        cc_agent_thread = hub.spawn(self.serve())

