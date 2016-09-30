__author__ = 'Zhang Shaojun'

import struct
import cfg
import msg_proto
from cfg import LOG

"""
# scapy form of message
# allign to 64 bits

class TFLCPHeader(Packet):
    name = "tflc header"
    fields_desc = [
        XByteField("version", cfg.TFLC_VERSION_1),
        ByteEnumField("type", msg_proto.TFLCT_HELLO_UP, msg_proto.tflcp_type),
        ShortField("length", msg_proto.TFLCP_HEADER_SIZE),
        IntField("xid", 1)
    ]

# HELLO_UP --> up
class TFLCPHelloUp(Packet):
    name = "tflc hello up"
    fields_desc = []
bind_layers(TFLCPHeader, TFLCPHelloUp, type=msg_proto.TFLCT_HELLO_UP)

# HELLO_DOWN --> down
class TFLCPHelloDown(Packet):
    name = "tflc hello down"
    fields_desc = [
        BitField('lcid', None, 32),
        IntField('pad', 0)
    ]
bind_layers(TFLCPHeader, TFLCPHelloDown, type=msg_proto.TFLCT_HELLO_DOWN)

# DATAPATH_CONNECTED --> up
class TFLCPDPConnected(Packet):
    name = "tflc datapath connected"
    fields_desc = [
        BitField('dpid', None, 64)
    ]
bind_layers(TFLCPHeader, TFLCPDPConnected, type=msg_proto.TFLCT_DATAPATH_CONNECTED)

# ROLE_ASSIGN --> down
class TFLCPRoleAssign(Packet):
    name = "tflc role assign"
    fields_desc = [
        BitField('dpid', None, 64),
        BitField('lcid', None, 32),
        IntEnumField('role', msg_proto.OFPCR_ROLE_EQUAL, msg_proto.ofp_controller_role),
        BitField('gid', 0, 64)
    ]
bind_layers(TFLCPHeader, TFLCPRoleAssign, type=msg_proto.TFLCT_ROLE_ASSIGN)

# GID_REQUEST --> up
class TFLCPGidRequest(Packet):
    name = "tflc gid request"
    fields_desc = [
        BitField('dpid', None, 64)
    ]
bind_layers(TFLCPHeader, TFLCPGidRequest, type=msg_proto.TFLCT_GID_REQUEST)

# GID_REPLY --> down
class TFLCPGidReply(Packet):
    name = "tflc gid reply"
    fields_desc = [
        BitField('dpid', None, 64),
        BitField('gid', 0, 64)
    ]
bind_layers(TFLCPHeader, TFLCPGidReply, type=msg_proto.TFLCT_GID_REPLY)

# PACKET_IN --> up
class TFLCPPackerIn(Packet):
    name = "tflc packet in"
    fields_desc = [
        BitField('in_dpid', None, 64),
        ShortField('total_len', 0),
        ShortEnumField('reason', msg_proto.TFLCR_PIN_NO_MATCH, msg_proto.tflc_packet_in_reason),
        IntField('pad', 0)
    ]
bind_layers(TFLCPHeader, TFLCPPackerIn, type=msg_proto.TFLCT_PACKET_IN)

# FLOW_MOD --> down
class TFLCPFlowMod(Packet):
    name = "tflc flow mod"
    fields_desc = []
bind_layers(TFLCPHeader, TFLCPFlowMod, type=msg_proto.TFLCT_FLOW_MOD)

# LOAD_REPORT --> up
class TFLCPLoadReport(Packet):
    name = "tflc load report"
    fields_desc = [
        BitField('dpid', None, 64),
        BitField('pkt_in_cnt', 0, 64)
    ]
bind_layers(TFLCPHeader, TFLCPLoadReport, type=msg_proto.TFLCT_LOAD_REPORT)

# DATAPATH_MIGRATION --> down
class TFLCPDpMigration(Packet):
    name = "tflc datapath migration"
    fields_desc = [
        BitField('src_lcid', None, 32),
        BitField('dst_lcid', None, 32),
        BitField('m_dpid', None, 64)
    ]
bind_layers(TFLCPHeader, TFLCPDpMigration, type=msg_proto.TFLCT_DATAPATH_MIGRATION)

# CONTRL_POOL_CHANGE --> down
class TFLCPCtrlPoolChange(Packet):
    name = "tflc controller pool change"
    fields_desc = []
bind_layers(TFLCPHeader, TFLCPCtrlPoolChange, type=msg_proto.TFLCT_CONTRL_POOL_CHANGE)

# ROLE_NOTIFY --> up
class TFLCPRoleNotify(Packet):
    name = "tflc role notify"
    fields_desc = [
        BitField('dpid', None, 64),
        BitField('lcid', None, 32),
        IntEnumField('role', msg_proto.OFPCR_ROLE_EQUAL, msg_proto.ofp_controller_role)
    ]
bind_layers(TFLCPHeader, TFLCPRoleNotify, type=msg_proto.TFLCT_ROLE_NOTIFY)

# ECHO_REQUEST --> down
class TFLCPEchoRequest(Packet):
    name = "tflc echo request"
    fields_desc = [
        BitField('time_stamp', 0, 64)
    ]
bind_layers(TFLCPHeader, TFLCPEchoRequest, type=msg_proto.TFLCT_ECHO_REQUEST)

# ECHO_REPLY --> down
class TFLCPEchoReply(Packet):
    name = "tflc echo reply"
    fields_desc = [
        BitField('time_stamp', 0, 64)
    ]
bind_layers(TFLCPHeader, TFLCPEchoReply, type=msg_proto.TFLCT_ECHO_REPLY)

# ERROR --> up
class TFLCPError(Packet):
    name = "tflc error"
    fields_desc = [
        IntEnumField('type', 0, msg_proto.tflc_error_type),
        IntField('code', 0)
    ]
"""
# downlink message base class
class MsgDownBase(object):

    def __init__(self, local_ctrl):
        super(MsgDownBase, self).__init__()
        self.local_ctrl = local_ctrl
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

#uplink message base class
class MsgUpBase(object):

    def __init__(self, local_ctrl, version = None, msg_type = None, msg_len = None, xid = None, buf = None):
        super(MsgUpBase, self).__init__()
        self.local_ctrl = local_ctrl
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
        self.type = type
        self.ip_addr = ip_addr
        self.port = port

# messages
# allign to 64 bit?
# HELLO_UP --> up
class TFLCPHelloUp(MsgUpBase):
    def __init__(self, local_ctrl):
        super(TFLCPHelloUp, self).__init__(local_ctrl)

# HELLO_DOWN --> down
class TFLCPHelloDown(MsgDownBase):
    def __init__(self, local_ctrl, lcid = None):
        super(TFLCPHelloDown, self).__init__(local_ctrl)
        self.msg_type = msg_proto.TFLCT_HELLO_DOWN
        self.lcid = lcid

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_HELLO_DOWN_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE, self.lcid)

# DATAPATH_CONNECTED --> up
class TFLCPDPConnected(MsgUpBase):
    def __init__(self, local_ctrl, dpid = None, is_window = False):
        super(TFLCPDPConnected, self).__init__(local_ctrl)
        self.dpid = dpid
        self.is_window = is_window

# ROLE_ASSIGN --> down
class TFLCPRoleAssign(MsgDownBase):
    def __init__(self, local_ctrl, dpid = None, lcid = None, role = None, gid = None):
        super(TFLCPRoleAssign, self).__init__(local_ctrl)
        self.msg_type = msg_proto.TFLCT_ROLE_ASSIGN
        self.dpid = dpid
        self.lcid = lcid
        self.role = role
        self.gid = gid

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_ROLE_ASSIGN_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.dpid, self.lcid, self.role, self.gid)

# GID_REQUEST --> up
class TFLCPGidRequest(MsgUpBase):
    def __init__(self, local_ctrl, dpid = None):
        super(TFLCPGidRequest, self).__init__(local_ctrl)
        self.dpid = dpid

# GID_REPLY --> down
class TFLCPGidReply(MsgDownBase):
    def __init__(self, local_ctrl, dpid = None, gid = None):
        super(TFLCPGidReply, self).__init__(local_ctrl)
        self.msg_type = msg_proto.TFLCT_GID_REPLY
        self.dpid = dpid
        self.gid = gid

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_GID_REPLY_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE, self.dpid, self.gid)

# PACKET_IN --> up
"""
class TFLCPPackerIn(MsgUpBase):
    def __init__(self, local_ctrl, in_dpid = None, total_len = None, reason = None, package = None):
        super(TFLCPPackerIn, self).__init__(local_ctrl)
        self.in_dpid = in_dpid
        self.total_len = total_len
        self.reason = reason
        self.package = package
"""
# currently only the second layer is considered.
# so the Packet in msg only contains the in_dpid/src mac/dst mac
class TFLCPPacketIn(MsgUpBase):
    def __init__(self, local_ctrl, in_dpid = None, src_mac = None, dst_mac = None):
        super(TFLCPPacketIn, self).__init__(local_ctrl)
        self.in_dpid = in_dpid
        self.src_mac = src_mac          # 48 bits
        self.dst_mac = dst_mac          # 48 bits

# FLOW_MOD --> down
# flow_mod = header/wildcards/match/flow_mod/action
# simplified flow_mod only considers the second layer
# so only src/dst mac and the out_dpid is included
class TFLCPFlowMod(MsgDownBase):
    def __init__(self, local_ctrl, in_dpid = None, out_dpid = None, dst_mac = None, wildcards = None):
        super(TFLCPFlowMod, self).__init__(local_ctrl)
        self.msg_type = msg_proto.TFLCT_FLOW_MOD
        self.in_dpid = in_dpid
        self.out_dpid = out_dpid
        self.dst_mac = dst_mac
        self.wildcards = wildcards


    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_FLOW_MOD_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.in_dpid, self.out_dpid, self.dst_mac, self.wildcards)

# LOAD_REPORT --> up
class TFLCPLoadReport(MsgUpBase):
    def __init__(self, local_ctrl, dpid = None, pkt_in_cnt = None):
        super(TFLCPLoadReport, self).__init__(local_ctrl)
        self.dpid = dpid
        self.pkt_in_cnt = pkt_in_cnt

# DATAPATH_MIGRATION --> down
class TFLCPDpMigration(MsgDownBase):
    def __init__(self, local_ctrl, src_lcid = None, dst_lcid = None, m_dpid = None):
        super(TFLCPDpMigration, self).__init__(local_ctrl)
        self.msg_type = msg_proto.TFLCT_DATAPATH_MIGRATION
        self.src_lcid = src_lcid
        self.dst_lcid = dst_lcid
        self.m_dpid = m_dpid

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_DATAPATH_CONNECTED_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.src_lcid, self.dst_lcid, self.m_dpid)

# CONTRL_POOL_CHANGE --> down
class TFLCPCtrlPoolChange(MsgDownBase):
    def __init__(self, local_ctrl, dpid = None, lc_cnt = None, lc_list = None):
        super(TFLCPCtrlPoolChange, self).__init__(local_ctrl)
        self.msg_type = msg_proto.TFLCT_CONTRL_POOL_CHANGE
        self.dpid = dpid
        self.lc_cnt = lc_cnt
        self.lc_list = lc_list

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_CONTRL_POOL_CHANGE_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE,
                      self.dpid, self.lc_cnt)
        for lc in self.lc_list:
            self.buf += struct.pack(msg_proto.TFLCP_LOCAL_CTRL_ADDRESS_PACK_STR, lc)


# ROLE_NOTIFY --> up
class TFLCPRoleNotify(MsgUpBase):
    def __init__(self, local_ctrl, dpid = None, lcid = None, role = None):
        super(TFLCPRoleNotify, self).__init__(local_ctrl)
        self.dpid = dpid
        self.lcid = lcid
        self.role = role

# ECHO_REQUEST --> down
class TFLCPEchoRequest(MsgDownBase):
    def __init__(self, local_ctrl, timestamp = None):
        super(TFLCPEchoRequest, self).__init__(local_ctrl)
        self.msg_type = msg_proto.TFLCT_ECHO_REQUEST
        self.timestamp = timestamp

    def _serialize_body(self):
        msg_pack_into(msg_proto.TFLCP_ECHO_REQUEST_PACK_STR, self.buf, msg_proto.TFLCP_HEADER_SIZE, self.timestamp)

# ECHO_REPLY --> up
class TFLCPEchoReply(MsgUpBase):
    def __init__(self, local_ctrl, timestamp = None):
        super(TFLCPEchoReply, self).__init__(local_ctrl)
        self.timestamp = timestamp

# ERROR --> up
class TFLCPError(MsgUpBase):
    def __init__(self, local_ctrl, type = None, code = None, data = None):
        super(TFLCPError, self).__init__(local_ctrl)
        self.type = type
        self.code = code
        self.data = data

# BARRIER_REQUEST --> down
class TFLCPBarrierRequest(MsgDownBase):
    def __init__(self, local_ctrl):
        super(TFLCPBarrierRequest, self).__init__(local_ctrl)
        self.msg_type = msg_proto.TFLCT_BARRIER_REQUEST

# BARRIER_REPLY --> up
class TFLCPBarrierReply(MsgUpBase):
    def __init__(self, local_ctrl):
        super(TFLCPBarrierReply, self).__init__(local_ctrl)

# HOST_CONNECTED --> up
class TFLCPHostConnected(MsgUpBase):
    def __init__(self, local_ctrl, dpid = None, mac = None):
        super(TFLCPHostConnected, self).__init__(local_ctrl)
        self.dpid = dpid
        self.mac = mac

# DATAPATH_LEAVE --> up
class TFLCPDatapathLeave(MsgUpBase):
    def __init__(self, local_ctrl, dpid = None):
        super(TFLCPDatapathLeave, self).__init__(local_ctrl)
        self.dpid = dpid


# HOST_LEAVE --> up
class TFLCPHostLeave(MsgUpBase):
    def __init__(self, cc_agent, dpid = None, mac = None):
        super(TFLCPHostLeave, self).__init__(cc_agent)
        self.msg_type = msg_proto.TFLCT_HOST_LEAVE
        self.dpid = dpid
        self.mac = mac
