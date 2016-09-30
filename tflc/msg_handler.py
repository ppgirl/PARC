__author__ = 'Zhang Shaojun'


import tflc_event
import msg_proto
import msg_proto_parser
import struct
from cfg import LOG

# Global Event Dispatcher
EVENT_DISPATCHER = tflc_event.EventDispatcher()

# uplink message handling
def hello_up_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPHelloUp(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    ev = tflc_event.EventTFLCPHelloUp(msg)
    # LOG.debug("msg_handler: event dispatched, message type is %d", ev.msg.msg_type)
    EVENT_DISPATCHER.dispatch_event(ev)

def dp_connected_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPDPConnected(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.dpid, msg.is_window = struct.unpack_from(msg_proto.TFLCP_DATAPATH_CONNECTED_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPDPConnected(msg)
    # LOG.debug("msg_handler: event dispatched, message type is %d", ev.msg.msg_type)
    EVENT_DISPATCHER.dispatch_event(ev)

def gid_request_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPGidRequest(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    (msg.dpid, ) = struct.unpack_from(msg_proto.TFLCP_GID_REQUEST_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPGidRequest(msg)
    # LOG.debug("msg_handler: event dispatched, message type is %d", ev.msg.msg_type)
    EVENT_DISPATCHER.dispatch_event(ev)

def packet_in_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPPacketIn(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.in_dpid, msg.src_mac, msg.dst_mac = struct.unpack_from(
        msg_proto.TFLCP_PACKET_IN_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPPacketIn(msg)
    # LOG.debug("msg_handler: event dispatched, message type is %d", ev.msg.msg_type)
    EVENT_DISPATCHER.dispatch_event(ev)

def load_report_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPLoadReport(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.dpid, msg.pkt_in_cnt = struct.unpack_from(
        msg_proto.TFLCP_LOAD_REPORT_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPLoadReport(msg)
    # LOG.debug("msg_handler: event dispatched, message type is %d", ev.msg.msg_type)
    EVENT_DISPATCHER.dispatch_event(ev)

def role_notify_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPRoleNotify(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.dpid, msg.lcid, msg.role = struct.unpack_from(
        msg_proto.TFLCP_ROLE_NOTIFY_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPRoleNotify(msg)
    # LOG.debug("msg_handler: event dispatched, message type is %d", ev.msg.msg_type)
    EVENT_DISPATCHER.dispatch_event(ev)

def echo_rep_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPEchoReply(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    (msg.timestamp, ) = struct.unpack_from(msg_proto.TFLCP_ECHO_REPLY_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPEchoReply(msg)
    # LOG.debug("msg_handler: event dispatched, message type is %d", ev.msg.msg_type)
    EVENT_DISPATCHER.dispatch_event(ev)

def error_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPError(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.type, msg.code = struct.unpack_from(msg_proto.TFLCP_ERROR_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    msg.data = msg.data[msg_proto.TFLCP_ERROR_SIZE:]
    ev = tflc_event.EventTFLCPError(msg)
    # LOG.debug("msg_handler: event dispatched, message type is %d", ev.msg.msg_type)
    EVENT_DISPATCHER.dispatch_event(ev)

def barrier_rep_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPBarrierReply(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    ev = tflc_event.EventTFLCPBarrierReply(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

def host_connected_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPHostConnected(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.dpid, msg.mac = struct.unpack_from(msg_proto.TFLCP_HOST_CONNECTED_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPHostConnected(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

def datapath_leave_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPDatapathLeave(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    (msg.dpid, ) = struct.unpack_from(msg_proto.TFLCP_DATAPATH_LEAVE_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPDatapathLeave(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

def host_leave_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPDatapathLeave(local_ctrl)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.dpid, msg.mac = struct.unpack_from(msg_proto.TFLCP_HOST_LEAVE_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPHostLeave(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

# downlink message handling
# not needed
def hello_down_handler():
    pass

def role_assign_handler():
    pass

def gid_reply_handler():
    pass

def flow_mod_handler():
    pass

def dp_migration_handler():
    pass

def ctl_pool_change_handler():
    pass


def echo_req_handler():
    pass

def barrier_req_handler():
    pass

# msg_handler dict, indexed by message type
msg_handler = {msg_proto.TFLCT_HELLO_UP: hello_up_handler,  # up
               msg_proto.TFLCT_HELLO_DOWN: hello_down_handler,  # down
               msg_proto.TFLCT_DATAPATH_CONNECTED: dp_connected_handler,  # up
               msg_proto.TFLCT_ROLE_ASSIGN: role_assign_handler,  # down
               msg_proto.TFLCT_GID_REQUEST: gid_request_handler,  # up
               msg_proto.TFLCT_GID_REPLY: gid_reply_handler,  # down
               msg_proto.TFLCT_PACKET_IN: packet_in_handler,  # up
               msg_proto.TFLCT_FLOW_MOD: flow_mod_handler,  # down
               msg_proto.TFLCT_LOAD_REPORT: load_report_handler,  # up
               msg_proto.TFLCT_DATAPATH_MIGRATION: dp_migration_handler,  # down
               msg_proto.TFLCT_CONTRL_POOL_CHANGE: ctl_pool_change_handler,  # down
               msg_proto.TFLCT_ROLE_NOTIFY: role_notify_handler,  # up
               msg_proto.TFLCT_ECHO_REQUEST: echo_req_handler,  # down
               msg_proto.TFLCT_ECHO_REPLY: echo_rep_handler,  # up
               msg_proto.TFLCT_ERROR: error_handler,  # up
               msg_proto.TFLCT_BARRIER_REQUEST: barrier_req_handler, #down
               msg_proto.TFLCT_BARRIER_REPLY: barrier_rep_handler, #up
               msg_proto.TFLCT_HOST_CONNECTED: host_connected_handler, #up
               msg_proto.TFLCT_DATAPATH_LEAVE: datapath_leave_handler, #up
               msg_proto.TFLCT_HOST_LEAVE: host_leave_handler #up
               }