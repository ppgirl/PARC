__author__ = 'Zhang Shaojun'

import struct
import cfg
import msg_proto

# uplink message base class
class MsgUpBase(object):

    def __init__(self, cc_agent):
        super(MsgUpBase, self).__init__()
        self.cc_agent = cc_agent
        self.version = None
        self.msg_type = None
        self.msg_len = None
        self.xid = None
        self.buf = None

    def set_xid(self, xid):
        self.xid = xid

    def _serialize_pre(self):
        self.version = cfg.TFLC_VERSION_1
        self.buf = bytearray(msg_proto.TFLCP_HEADER_SIZE)

    def _serialize_header(self):
        self.msg_len = len(self.buf)
        if self.xid is None:
            self.xid = 0
        struct.pack_into(msg_proto.TFLCP_HEADER_PACK_STR, self.buf, 0,
                         self.version, self.msg_type, self.msg_len, self.xid)

    def _serialize_body(self):
        pass

    def serialize(self):
        self._serialize_pre()
        self._serialize_body()
        self._serialize_header()

# downlink message base class
class MsgDownBase(object):

    def __init__(self, cc_agent, version = None, msg_type = None, msg_len = None, xid = None, buf = None):
        super(MsgDownBase, self).__init__()
        self.cc_agent = cc_agent
        self.version = version
        self.msg_type = msg_type
        self.msg_len = msg_len
        self.xid = xid
        self.buf = buf

# pack function
def msg_pack_into(fmt, buf, offset, *args):
    if len(buf) < offset:
        buf += bytearray(offset - len(buf))

    if len(buf) == offset:
        buf += struct.pack(fmt, *args)
        return

    needed_len = offset + struct.calcsize(fmt)
    if len(buf) < needed_len:
        buf += bytearray(needed_len - len(buf))

    struct.pack_into(fmt, buf, offset, *args)

# header parser
def header(buf):
    assert len(buf) >= msg_proto.TFLCP_HEADER_SIZE
    return struct.unpack_from(msg_proto.TFLCP_HEADER_PACK_STR, buffer(buf))

# the controller address for controller pool change
class TFLCPLocalCtrlAddr(object):
    def __init__(self, type, ip_addr, port):
        super(TFLCPLocalCtrlAddr, self).__init__()
        self.type = type            # string
        self.ip_addr = ip_addr      # string
        self.port = port            # number

# messages
# allign to 64 bit?
# HELLO_UP --> up
class TFLCPHelloUp(MsgUpBase):
    def __init__(self, cc_agent):
        super(TFLCPHelloUp, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_HELLO_UP

# HELLO_DOWN --> down
class TFLCPHelloDown(MsgDownBase):
    def __init__(self, cc_agent, lcid = None):
        super(TFLCPHelloDown, self).__init__(cc_agent)
        self.lcid = lcid


# DATAPATH_CONNECTED --> up
class TFLCPDPConnected(MsgUpBase):
    def __init__(self, cc_agent, dpid = None, is_window = False):
        super(TFLCPDPConnected, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_DATAPATH_CONNECTED
        self.dpid = dpid
        self.is_window = is_window

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_DATAPATH_CONNECTED_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.dpid, self.is_window)

# ROLE_ASSIGN --> down
class TFLCPRoleAssign(MsgDownBase):
    def __init__(self, cc_agent, dpid = None, lcid = None, role = None, gid = None):
        super(TFLCPRoleAssign, self).__init__(cc_agent)
        self.dpid = dpid
        self.lcid = lcid
        self.role = role
        self.gid = gid

# GID_REQUEST --> up
class TFLCPGidRequest(MsgUpBase):
    def __init__(self, cc_agent, dpid = None):
        super(TFLCPGidRequest, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_GID_REQUEST
        self.dpid = dpid

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_GID_REQUEST_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE, self.dpid)

# GID_REPLY --> down
class TFLCPGidReply(MsgDownBase):
    def __init__(self, cc_agent, dpid = None, gid = None):
        super(TFLCPGidReply, self).__init__(cc_agent)
        self.dpid = dpid
        self.gid = gid

# PACKET_IN --> up
"""
class TFLCPPackerIn(MsgUpBase):
    def __init__(self, cc_agent, in_dpid = None, total_len = None, reason = None, package = None):
        super(TFLCPPackerIn, self).__init__(cc_agent)
        self.in_dpid = in_dpid
        self.total_len = total_len
        self.reason = reason
        self.package = package
"""
# currently only the second layer is considered.
# so the Packet in msg only contains the in_dpid/src mac/dst mac
class TFLCPPacketIn(MsgUpBase):
    def __init__(self, cc_agent, in_dpid = None, src_mac = None, dst_mac = None):
        super(TFLCPPacketIn, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_PACKET_IN
        self.in_dpid = in_dpid
        self.src_mac = src_mac          # 17*8 bits
        self.dst_mac = dst_mac          # 17*8 bits

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_PACKET_IN_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.in_dpid, self.src_mac, self.dst_mac)

# FLOW_MOD --> down
# flow_mod = header/wildcards/match/flow_mod/action
# simplified flow_mod only considers the second layer
# so only src/dst mac and the out_dpid is included
class TFLCPFlowMod(MsgDownBase):
    def __init__(self, cc_agent, in_dpid = None, out_dpid = None, dst_mac = None, wildcards = None):
        super(TFLCPFlowMod, self).__init__(cc_agent)
        self.in_dpid = in_dpid
        self.out_dpid = out_dpid
        self.dst_mac = dst_mac
        self.wildcards = wildcards

# LOAD_REPORT --> up
class TFLCPLoadReport(MsgUpBase):
    def __init__(self, cc_agent, dpid = None, pkt_in_cnt = None):
        super(TFLCPLoadReport, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_LOAD_REPORT
        self.dpid = dpid
        self.pkt_in_cnt = pkt_in_cnt

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_LOAD_REPORT_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.dpid, self.pkt_in_cnt)

# DATAPATH_MIGRATION --> down
class TFLCPDpMigration(MsgDownBase):
    def __init__(self, cc_agent, src_lcid = None, dst_lcid = None, m_dpid = None):
        super(TFLCPDpMigration, self).__init__(cc_agent)
        self.src_lcid = src_lcid
        self.dst_lcid = dst_lcid
        self.m_dpid = m_dpid

# CONTRL_POOL_CHANGE --> down
class TFLCPCtrlPoolChange(MsgDownBase):
    def __init__(self, cc_agent, dpid = None, lc_cnt = None, lc_list = None):
        super(TFLCPCtrlPoolChange, self).__init__(cc_agent)
        self.dpid = dpid
        self.lc_cnt = lc_cnt
        self.lc_list = lc_list

# ROLE_NOTIFY --> up
class TFLCPRoleNotify(MsgUpBase):
    def __init__(self, cc_agent, dpid = None, lcid = None, role = None):
        super(TFLCPRoleNotify, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_ROLE_NOTIFY
        self.dpid = dpid
        self.lcid = lcid
        self.role = role

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_ROLE_NOTIFY_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.dpid, self.lcid, self.role)

# ECHO_REQUEST --> down
class TFLCPEchoRequest(MsgDownBase):
    def __init__(self, cc_agent, timestamp = None):
        super(TFLCPEchoRequest, self).__init__(cc_agent)
        self.timestamp = timestamp

# ECHO_REPLY --> up
class TFLCPEchoReply(MsgUpBase):
    def __init__(self, cc_agent, timestamp = None):
        super(TFLCPEchoReply, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_ECHO_REPLY
        self.timestamp = timestamp

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_ECHO_REPLY_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE, self.timestamp)

# ERROR --> up
class TFLCPError(MsgUpBase):
    def __init__(self, cc_agent, type = None, code = None, data = None):
        super(TFLCPError, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_ERROR
        self.type = type
        self.code = code
        self.data = data

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_ERROR_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.type, self.code)
        self.buf += self.data

# BARRIER_REQUEST --> down
class TFLCPBarrierRequest(MsgDownBase):
    def __init__(self, cc_agent):
        super(TFLCPBarrierRequest, self).__init__(cc_agent)

# BARRIER_REPLY --> up
class TFLCPBarrierReply(MsgUpBase):
    def __init__(self, cc_agent):
        super(TFLCPBarrierReply, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_BARRIER_REPLY

# HOST_CONNECTED --> up
class TFLCPHostConnected(MsgUpBase):
    def __init__(self, cc_agent, dpid = None, mac = None):
        super(TFLCPHostConnected, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_HOST_CONNECTED
        self.dpid = dpid
        self.mac = mac

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_HOST_CONNECTED_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.dpid, self.mac)

# DATAPATH_LEAVE --> up
class TFLCPDatapathLeave(MsgUpBase):
    def __init__(self, cc_agent, dpid = None):
        super(TFLCPDatapathLeave, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_DATAPATH_LEAVE
        self.dpid = dpid

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_DATAPATH_LEAVE_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE, self.dpid)

# HOST_LEAVE --> up
class TFLCPHostLeave(MsgUpBase):
    def __init__(self, cc_agent, dpid = None, mac = None):
        super(TFLCPHostLeave, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_HOST_LEAVE
        self.dpid = dpid
        self.mac = mac

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_HOST_LEAVE_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.dpid, self.mac)
