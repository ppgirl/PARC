__author__ = 'Zhang Shaojun'
"""
modified from ryu~
thanks
"""

import contextlib
import hub
from hub import StreamServer
import random
import socket
import cfg
import msg_proto
import msg_proto_parser
import msg_handler
from cfg import LOG

class CentralController(object):
    def __init__(self):
        super(CentralController, self).__init__()
        self.server_loop()

    # def __call__(self):
    #     self.server_loop()

    def server_loop(self):
        server = StreamServer((cfg.CC_LISTEN_HOST, cfg.CC_LISTEN_PORT), local_ctrl_connection_factory)
        LOG.info("controller: central controller started")
        server.serve_forever()

def _deactivate(method):
    def deactivate(self):
        try:
            method(self)
        finally:
            self.is_active = False
    return deactivate

class LocalController(object):
    def __init__(self, sock, address):
        super(LocalController, self).__init__()

        self.sock = sock
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.address = address
        self.id = None
        self.is_active = True
        self.state = cfg.LC_STATE_HANDSHAKE
        self.send_q = hub.Queue(16)
        self.xid = random.randint(0, cfg.MAX_XID)

        self.dpid_to_role = {}
        self.dpid_to_load = {}
        self.dp_win = {}            # {dpid:lcid}, the lcid that the window dpid connected to
        self.orig_id = self.id

    def close(self):
        self.set_state(cfg.LC_STATE_DEAD)

    def set_id(self, lcid):
        self.id = lcid

    def set_state(self, state):
        self.state = state

    @_deactivate
    def _recv_loop(self):
        buf = bytearray()
        required_len = msg_proto.TFLCP_HEADER_SIZE
        count = 0
        while self.is_active:
            ret = self.sock.recv(required_len)
            if len(ret) == 0:
                LOG.info("controller: connection from %s dropped", self.address)
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
                if count > 1024:
                    count = 0
                    hub.sleep(0)

    @_deactivate
    def _send_loop(self):
        try:
            while self.is_active:
                buf = self.send_q.get()
                self.sock.sendall(buf)
        finally:
            q = self.send_q
            # first, clear self.send_q to prevent new references.
            self.send_q = None
            # there might be threads currently blocking in send_q.put().
            # unblock them by draining the queue.
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
        LOG.debug("controller: send message: %s", msg.__class__.__name__)
        self.send(msg.buf)

    def serve(self):
        send_thread = hub.spawn(self._send_loop)
        try:
            self._recv_loop()
        finally:
            hub.kill(send_thread)
            hub.joinall([send_thread])

class Datapath(object):
    def __init__(self, dpid):
        self.id = dpid
        self._generation_id = 1
        self.mac = []
        self.lc_home = None
        self.lc_connected = []
        self.load = 0

    def get_generation_id(self):
        self._generation_id += 1
        return self._generation_id-1

    def add_lc(self, lc):
        if lc not in self.lc_connected:
            self.lc_connected.append(lc)

    def del_lc(self, lc):
        self.lc_connected.remove(lc)

    def set_home_lc(self, lc):
        self.lc_home = lc

    def add_mac(self, mac):
        if mac not in self.mac:
            self.mac.append(mac)

    def del_mac(self, mac):
        self.mac.remove(mac)

    def set_load(self, load):
        self.load = load

def local_ctrl_connection_factory(sock, address):
    LOG.info("controller: local controller connected, address: %s", address)
    with contextlib.closing(LocalController(sock, address)) as local_ctrl:
        try:
            local_ctrl.serve()
        except:
            lcid_str = "%d" % local_ctrl.id
            LOG.error("controller: Error in the local controller %s from %s", lcid_str, address)
            raise
