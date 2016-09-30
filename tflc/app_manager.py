__author__ = 'Zhang Shaojun'
# message event handlers and app manager
# function 1: message event handler
# function 2: generate sending messages
# function 3: app manager: with an initial central controller

import time
import hub
import wsgi
import threading
import controller
import cfg
import msg_proto_parser
import tflc_event
import msg_proto
import networkx
import lc_level_topo
import wsgi_handler
from msg_handler import EVENT_DISPATCHER as EVENT_DISPATCHER
from cfg import LOG

class AppManager(object):
    def __init__(self, *args, **kwargs):
        super(AppManager, self).__init__()

        # global local controllers id
        self.glcid = 1
        self.lcip_to_lcid = {}

        # global device list
        self.local_ctrl_list = {}
        self.datapath_list = {}
        self.host_to_lcid = {}

        # network topology
        self.LC_LEVEL_TOPO = lc_level_topo.LC_LEVEL_TOPO
        self.dp_win = lc_level_topo.win_dpid_to_lcid           # {dpid:lcid}, the lcid that the window dpid connected to

        # master-slave-switching
        self.lc_outline = {}
        self.lc_outline_0 = {}
        self.lc_outline_1 = {}

        # threads
        self.echo_threads = hub.spawn(self._echo_request)
        self.ms_switch_threads = hub.spawn(self._ms_switch_decide)

        # event system
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPHelloUp, self._tflcp_hello_up_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPDPConnected, self._tflcp_datapath_connected_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPGidRequest, self._tflcp_gid_request_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPPacketIn, self._tflcp_packet_in_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPLoadReport, self._tflcp_load_report_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPRoleNotify, self._tflcp_role_notify_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPEchoReply, self._tflcp_echo_reply_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPError, self._tflcp_error_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPHostConnected, self._tflcp_host_connected_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPDatapathLeave, self._tflcp_datapath_leave_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPHostLeave, self._tflcp_host_leave_handler)

        # WSGI server
        self.wsgi_app = wsgi.WSGIApplication()
        wsgi_server = wsgi.WSGIServer(self.wsgi_app)
        wsgi_server_t = threading.Thread(target=wsgi_server)
        wsgi_server_t.setDaemon(True)
        wsgi_server_t.start()
        self._rest_stats()


    def __call__(self):
        LOG.info("app_manager: app manager starting ...")
        hub.spawn(controller.CentralController())

    def _tflcp_hello_up_handler(self, ev):
        LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        local_ctrl = ev.msg.local_ctrl
        local_ctrl.set_state(cfg.LC_STATE_LIVE)
        lcip = local_ctrl.address[0]
        if lcip in self.lcip_to_lcid:
            local_ctrl.set_id(self.lcip_to_lcid[lcip])
        else:
            local_ctrl.set_id(self.glcid)
            self.lcip_to_lcid[lcip] = self.glcid
            self.glcid += 1
            if self.glcid > cfg.MAX_LC_ID:
                self.glcid = 1
        self.local_ctrl_list[local_ctrl.id] = local_ctrl

        self.lc_outline[local_ctrl.id] = False
        self.lc_outline_0[local_ctrl.id] = False
        self.lc_outline_1[local_ctrl.id] = False
        LOG.info("app_manager: the id of this local controller is %d", local_ctrl.id)
        msg_hello_down = msg_proto_parser.TFLCPHelloDown(local_ctrl = local_ctrl, lcid = local_ctrl.id)
        local_ctrl.send_msg(msg_hello_down)

    def _tflcp_datapath_connected_handler(self, ev):
        LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        local_ctrl = ev.msg.local_ctrl
        dpid = ev.msg.dpid
        is_window = ev.msg.is_window
        if dpid in self.datapath_list:
            LOG.debug("app_manager: hello, I has not disconnected from the older controller -_-")
            datapath = self.datapath_list[dpid]
            for mac_t in datapath.mac:
                # once the datapath gets connected to a new controller, the host must be cleared,
                # and the local region must ping each other to perform host discovering
                del self.host_to_lcid[mac_t]
                datapath.del_mac(mac_t)
        else:
            datapath = controller.Datapath(dpid)
            self.datapath_list[dpid] = datapath
        datapath.add_lc(local_ctrl)
        datapath.set_home_lc(local_ctrl)
        LOG.info("app_manager: datapath connected: lcid: %d, dpid: %d", local_ctrl.id, dpid)

        local_ctrl.dpid_to_role[dpid] = msg_proto.OFPCR_ROLE_MASTER
        local_ctrl.dpid_to_load[dpid] = datapath.load
        if is_window:
            local_ctrl.dp_win[dpid] = self.dp_win.get(dpid, local_ctrl.id)
        msg_role_assign = msg_proto_parser.TFLCPRoleAssign(
            local_ctrl, dpid, local_ctrl.id, msg_proto.OFPCR_ROLE_MASTER, datapath.get_generation_id())
        local_ctrl.send_msg(msg_role_assign)

    def _tflcp_gid_request_handler(self, ev):
        LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        local_ctrl = ev.msg.local_ctrl
        dpid = ev.msg.dpid
        datapath = self.datapath_list[dpid]
        msg_gid_reply = msg_proto_parser.TFLCPGidReply(local_ctrl, dpid, datapath.get_generation_id())
        local_ctrl.send_msg(msg_gid_reply)

    def _tflcp_packet_in_handler(self, ev):
        LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        local_ctrl = ev.msg.local_ctrl
        xid = ev.msg.xid
        in_dpid = ev.msg.in_dpid
        src_mac = ev.msg.src_mac
        dst_mac = ev.msg.dst_mac
        LOG.debug("app_manager: packet in %s %s %s %s", local_ctrl.id, in_dpid, src_mac, dst_mac)
        if not ((src_mac in self.host_to_lcid) and (dst_mac in self.host_to_lcid)):
            return

        # if the packet is from the current lc domain, the in_dpid field should be ignored
        src_lcid = self.host_to_lcid[src_mac]

        start_lcid = local_ctrl.id
        dst_lcid = self.host_to_lcid[dst_mac]
        path = networkx.shortest_path(self.LC_LEVEL_TOPO, start_lcid, dst_lcid)
        if cfg.FLOW_DISPATCH_STEPBYSTEP:
            next_lc = path[path.index(start_lcid)+1]
            wildcards = 0
            if src_lcid == local_ctrl.id:
                wildcards = 1
            out_dpid = self.LC_LEVEL_TOPO.edge[start_lcid][next_lc]['left_dpid']
            msg_flow_mod = msg_proto_parser.TFLCPFlowMod(local_ctrl, in_dpid, out_dpid, dst_mac, wildcards)
            msg_flow_mod.set_xid(xid)
            local_ctrl.send_msg(msg_flow_mod)
        else:
            for node_index in range(len(path)-1):
                out_dpid = self.LC_LEVEL_TOPO.edge[path[node_index]][path[node_index+1]]['left_dpid']
                local_ctrl_path = self.local_ctrl_list[path[node_index]]
                wildcards = 0
                if src_lcid == local_ctrl_path.id:
                    wildcards = 1
                if wildcards == 0:
                    in_dpid = self.LC_LEVEL_TOPO.edge[path[node_index-1]][path[node_index]]['right_dpid']
                msg_flow_mod = msg_proto_parser.TFLCPFlowMod(local_ctrl_path, in_dpid, out_dpid, dst_mac, wildcards)
                msg_flow_mod.set_xid(xid)
                local_ctrl_path.send_msg(msg_flow_mod)

    def _tflcp_load_report_handler(self, ev):
        # LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        local_ctrl = ev.msg.local_ctrl
        dpid = ev.msg.dpid
        pkt_in_cnt = ev.msg.pkt_in_cnt
        datapath = self.datapath_list[dpid]
        datapath.set_load(pkt_in_cnt)
        local_ctrl.dpid_to_load[dpid] = pkt_in_cnt
        # LOG.debug("app_manager: dpid: %d load: %d", dpid, pkt_in_cnt)
        pass

    def _tflcp_role_notify_handler(self, ev):
        LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        dpid = ev.msg.dpid
        lcid = ev.msg.lcid
        role = ev.msg.role
        LOG.info("app_manager: the role of controller %d at datapath %d is %d", lcid, dpid, role)

    def _tflcp_echo_reply_handler(self, ev):
        LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        local_ctrl = ev.msg.local_ctrl
        timestamp_lc = ev.msg.timestamp
        timestamp_cc = int(round(time.time() * 10000))
        LOG.debug("app_manager: timestamp_lc: %d timestamp_cc: %d", timestamp_lc, timestamp_cc)
        self.lc_outline[local_ctrl.id] = False
        self.lc_outline_0[local_ctrl.id] = False
        self.lc_outline_1[local_ctrl.id] = False
        pass

    def _tflcp_error_handler(self, ev):
        LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        local_ctrl = ev.msg.local_ctrl
        type = ev.msg.type
        code = ev.msg.code
        data = ev.msg.data
        LOG.info("app_manager: error occurred, type - %d  code - %d  data - %s", type, code, data)

    def _tflcp_host_connected_handler(self, ev):
        LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        local_ctrl = ev.msg.local_ctrl
        dpid = ev.msg.dpid
        mac = ev.msg.mac
        # if the new host has existed, delete it
        if mac in self.host_to_lcid:
            del self.host_to_lcid[mac]
            for old_dpid in self.datapath_list:
                old_dp = self.datapath_list[old_dpid]
                if mac in old_dp.mac:
                    old_dp.del_mac(mac)
                    break
        # add the new host to the list
        self.host_to_lcid[mac] = local_ctrl.id
        LOG.debug("app_manager: host_to_lcid/n%s", self.host_to_lcid)
        datapath = self.datapath_list[dpid]
        datapath.add_mac(mac)
        LOG.info("app_manager: host connected, lcid: %d, dpid: %d, mac: %s", local_ctrl.id, dpid, mac)

    def _tflcp_datapath_leave_handler(self, ev):
        LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        local_ctrl = ev.msg.local_ctrl
        dpid = ev.msg.dpid
        LOG.info("app_manager: datapath leave, lcid: %d, dpid: %d", local_ctrl.id, dpid)
        datapath = self.datapath_list[dpid]
        for mac_t in datapath.mac:
            del self.host_to_lcid[mac_t]
            datapath.del_mac(mac_t)
        if len(datapath.lc_connected) == 1:
            del self.datapath_list[dpid]
        del local_ctrl.dpid_to_role[dpid]
        del local_ctrl.dpid_to_load[dpid]
        datapath.del_lc(local_ctrl)
        if dpid in local_ctrl.dp_win:
            del local_ctrl.dp_win[dpid]

    def _tflcp_host_leave_handler(self, ev):
        LOG.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        local_ctrl = ev.msg.local_ctrl
        dpid = ev.msg.dpid
        mac = ev.msg.mac
        if mac in self.host_to_lcid:
            del self.host_to_lcid[mac]
        datapath = self.datapath_list[dpid]
        if mac in datapath.mac:
            datapath.del_mac(mac)
        LOG.info("app_manager: host connected, lcid: %d, dpid: %d, mac: %s", local_ctrl.id, dpid, mac)

    def _echo_request(self):
        while True:
            for lc in self.local_ctrl_list.values():
                if lc.is_active:
                    timestamp = int(round(time.time() * 10000))
                    msg_echo_request = msg_proto_parser.TFLCPEchoRequest(lc, timestamp)
                    lc.send_msg(msg_echo_request)
            hub.sleep(cfg.ECHO_REQ_INTERVAL)

    # decide when to carry out master-slave-switching
    def _ms_switch_decide(self):
        while True:
            for lcid in self.local_ctrl_list:
                if not self.lc_outline[lcid]:
                    if not self.lc_outline_0[lcid]:
                        self.lc_outline_0[lcid] = True
                        if self.lc_outline_1[lcid]:
                            self.lc_outline_1[lcid] = False
                    else:
                        if self.lc_outline_1[lcid]:
                            self.lc_outline[lcid] = True
                            self._ms_switch_execute(lcid)
                        else:
                            self.lc_outline_1[lcid] = True
            hub.sleep(cfg.MS_SWITCH_INTERVAL)

    # carry out master-slave-switching
    def _ms_switch_execute(self, lcid):
        pass

    def _rest_stats(self):
        wsgi_stats_data = {}
        self.waiters = {}
        wsgi_stats_data['app_manager'] = self
        wsgi_stats_data['waiters'] = self.waiters

        self.wsgi_app.registory['StatsController'] = wsgi_stats_data
        mapper = self.wsgi_app.mapper

        path = '/stats'
        uri = path + '/app_name'
        mapper.connect('stats', uri, controller=wsgi_handler.StatsController,
                       action='get_app_name', conditions=dict(method=['GET']))

        uri = path + '/controller_list'
        mapper.connect('stats', uri, controller=wsgi_handler.StatsController,
                       action='get_controller_list', conditions=dict(method=['GET']))

        uri = path + '/lc_topo'
        mapper.connect('stats', uri, controller=wsgi_handler.StatsController,
                       action='get_lc_topo', conditions=dict(method=['GET']))
        mapper.connect('stats', uri, controller=wsgi_handler.StatsController,
                       action='set_lc_topo', conditions=dict(method=['POST']))

        uri = path + '/dp_win'
        mapper.connect('stats', uri, controller=wsgi_handler.StatsController,
                       action='get_dp_win', conditions=dict(method=['GET']))
        mapper.connect('stats', uri, controller=wsgi_handler.StatsController,
                       action='set_dp_win', conditions=dict(method=['POST']))

        uri = path + '/controller/{lcid}'
        mapper.connect('stats', uri, controller=wsgi_handler.StatsController,
                       action='get_controller', conditions=dict(method=['GET']))

        uri = path + '/datapath_list'
        mapper.connect('stats', uri, controller=wsgi_handler.StatsController,
                       action='get_datapath_list', conditions=dict(method=['GET']))

        uri = path + '/datapath/{dpid}'
        mapper.connect('stats', uri, controller=wsgi_handler.StatsController,
                       action='get_datapath', conditions=dict(method=['GET']))

        uri = path + '/host/{lcid}'
        mapper.connect('stats', uri, controller=wsgi_handler.StatsController,
                       action='get_host', conditions=dict(method=['GET']))

