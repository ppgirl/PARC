__author__ = 'Zhang Shaojun'


import tflc_event
import msg_proto
import msg_proto_parser
import struct

# Global Event Dispatcher
EVENT_DISPATCHER = tflc_event.EventDispatcher()

# uplink message handling
# not needed
def hello_up_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def dp_connected_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def gid_request_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def packet_in_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def load_report_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def role_notify_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def echo_rep_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def error_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def barrier_rep_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def host_connected_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def datapath_leave_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

def host_leave_handler(local_ctrl, version, msg_type, msg_len, xid, data):
    pass

# downlink message handling
def hello_down_handler(cc_agent, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPHelloDown(cc_agent)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    (msg.lcid, ) = struct.unpack_from(msg_proto.TFLCP_HELLO_DOWN_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPHelloDown(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

def role_assign_handler(cc_agent, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPRoleAssign(cc_agent)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.dpid, msg.lcid, msg.role, msg.gid = struct.unpack_from(
        msg_proto.TFLCP_ROLE_ASSIGN_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPRoleAssign(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

def gid_reply_handler(cc_agent, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPGidReply(cc_agent)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.dpid, msg.gid = struct.unpack_from(msg_proto.TFLCP_GID_REPLY_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPGidReply(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

def flow_mod_handler(cc_agent, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPFlowMod(cc_agent)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.in_dpid, msg.out_dpid, msg.dst_mac, msg.wildcards = struct.unpack_from(
        msg_proto.TFLCP_FLOW_MOD_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPFlowMod(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

def dp_migration_handler(cc_agent, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPDpMigration(cc_agent)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.src_lcid, msg.dst_lcid, msg.m_dpid = struct.unpack_from(
        msg_proto.TFLCP_DATAPATH_MIGRATION_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPDpMigration(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

def ctl_pool_change_handler(cc_agent, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPCtrlPoolChange(cc_agent)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    msg.dpid, msg.lc_cnt = struct.unpack_from(
        msg_proto.TFLCP_CONTRL_POOL_CHANGE_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    msg.lc_list = []
    for n in range(msg.lc_cnt):
        lc = struct.unpack_from(msg_proto.TFLCP_LOCAL_CTRL_ADDRESS_PACK_STR, data,
                                msg_proto.TFLCP_CONTRL_POOL_CHANGE_SIZE+n*msg_proto.TFLCP_LOCAL_CTRL_ADDRESS_SIZE)
        msg.lc_list.append(lc)
    ev = tflc_event.EventTFLCPCtrlPoolChange(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

def echo_req_handler(cc_agent, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPEchoRequest(cc_agent)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    (msg.timestamp, ) = struct.unpack_from(
        msg_proto.TFLCP_ECHO_REQUEST_PACK_STR, data, msg_proto.TFLCP_HEADER_SIZE)
    ev = tflc_event.EventTFLCPEchoRequest(msg)
    EVENT_DISPATCHER.dispatch_event(ev)

def barrier_req_handler(cc_agent, version, msg_type, msg_len, xid, data):
    msg = msg_proto_parser.TFLCPBarrierRequest(cc_agent)
    msg.version = version
    msg.msg_type = msg_type
    msg.msg_len = msg_len
    msg.xid = xid
    ev = tflc_event.EventTFLCPBarrierRequest(msg)
    EVENT_DISPATCHER.dispatch_event(ev)


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