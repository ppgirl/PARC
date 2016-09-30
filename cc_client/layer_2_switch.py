__author__ = 'Zhang Shaojun'

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.ovs import bridge
from ryu.lib import hub
from ryu.lib.mac import BROADCAST_STR

import cfg
import cc_agent
import tflc_event
import msg_proto_parser
import time
import threading
from msg_handler import EVENT_DISPATCHER as EVENT_DISPATCHER
from ryu.lib.packet import packet, ethernet, lldp

from ryu.topology.api import get_switch, get_link
from ryu.topology import event
import networkx as nx


class Layer2Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Layer2Switch, self).__init__(*args, **kwargs)

        self.lcid = None
        self.mac_to_port = {}
        self.datapaths = {}
        self.dpid_to_load = {}
        self.dpid_to_inter_connection_port = {}

        self.load_report_thread = hub.spawn(self._load_report)
        self.packet_timeout_handler_thread = hub.spawn(self._packet_timeout_handler)

        self.dpid_to_is_win = cfg.DPID_2_IS_WIN
        self.dpid_to_out_port = cfg.DPID_2_OUT_PORT

        self.topology_api_app = self
        self.net = nx.DiGraph()
        self.xid_to_packet = {}
        self.xid_to_packet_timestamp = {}
        self.xid_to_buffer_id = {}

        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPHelloDown, self.cc_hello_down_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPRoleAssign, self.cc_role_assign_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPFlowMod, self.cc_flow_mod_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPCtrlPoolChange, self.cc_ctrl_pool_change_handler)
        EVENT_DISPATCHER.add_event_listener(tflc_event.EventTFLCPEchoRequest, self.cc_echo_request_handler)

        self.cc_agent = cc_agent.CentralCtrlAgent(self.logger)
        self.cc_agent_t = threading.Thread(target=self.cc_agent.serve)
        self.cc_agent_t.setDaemon(True)
        self.cc_agent_t.start()

    ####################################################################################################################
    # handlers of Openflow Messages

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def ofp_switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        self.datapaths[dpid] = datapath
        self.dpid_to_load[dpid] = 0
        self.mac_to_port.setdefault(dpid, {})
        self.dpid_to_inter_connection_port.setdefault(dpid, [])

        is_window = self.dpid_to_is_win.get(dpid, False)
        dp_connected_msg = msg_proto_parser.TFLCPDPConnected(self.cc_agent, dpid, is_window)
        self.cc_agent.send_msg(dp_connected_msg)

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPRoleReply, MAIN_DISPATCHER)
    def ofp_role_reply_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        role = ev.msg.role
        role_notify = msg_proto_parser.TFLCPRoleNotify(self.cc_agent, dpid, self.lcid, role)
        self.cc_agent.send_msg(role_notify)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def ofp_packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        src = eth.src
        dst = eth.dst
        if dst == lldp.LLDP_MAC_NEAREST_BRIDGE:
            if in_port not in self.dpid_to_inter_connection_port[dpid]:
                self.dpid_to_inter_connection_port[dpid].append(in_port)
            return
        if self._pkt_not_protocol(src, dst):
            self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
        self.dpid_to_load[dpid] += 1

        if src not in self.net:
            if in_port not in self.dpid_to_inter_connection_port[dpid]:
                # delete old host connected to the same port as src, which may have disconnected for a long time
                for old_mac in self.mac_to_port[dpid]:
                    if self.mac_to_port[dpid][old_mac] == in_port:
                        del self.mac_to_port[dpid][old_mac]
                        self.net.remove_node(old_mac)
                        msg_host_leave = msg_proto_parser.TFLCPHostLeave(self.cc_agent, dpid, old_mac)
                        self.cc_agent.send_msg(msg_host_leave)
                        self.logger.info("********** List of links **********\n%s\n%s",
                                         self.net.nodes(), self.net.edges())
                        break
                # if src has been in net, delete it
                for old_dpid in self.mac_to_port:
                    if src in self.mac_to_port[old_dpid]:
                        del self.mac_to_port[old_dpid][src]
                        self.net.remove_node(src)
                        msg_host_leave = msg_proto_parser.TFLCPHostLeave(self.cc_agent, old_dpid, src)
                        self.cc_agent.send_msg(msg_host_leave)
                        self.logger.info("********** List of links **********\n%s\n%s",
                                         self.net.nodes(), self.net.edges())
                        break

                # add src ----- the newly connected host to net
                self.mac_to_port[dpid][src] = in_port
                self.net.add_node(src)
                self.net.add_edge(dpid, src, {'port': in_port})
                self.net.add_edge(src, dpid)
                msg_host_connected = msg_proto_parser.TFLCPHostConnected(self.cc_agent, dpid, src)
                self.cc_agent.send_msg(msg_host_connected)
                self.logger.info("********** List of links **********\n%s\n%s",
                                 self.net.nodes(), self.net.edges())
        if dst in self.net:
            try:
                path = nx.shortest_path(self.net, dpid, dst)
                self.logger.debug("%%%%%%%%%% path is %s", path)
                next_hop = path[path.index(dpid)+1]
                out_port = self.net[dpid][next_hop]['port']
                actions = [parser.OFPActionOutput(out_port)]
                match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                    return
                else:
                    self.add_flow(datapath, 1, match, actions)
                    data = None
                    if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                        data = msg.data
                    out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                              in_port=in_port, actions=actions, data=data)
                    datapath.send_msg(out)
            except nx.NetworkXNoPath as e:
                self.logger.error("********** No Path, the net is **********\n%s\n%s",
                                 self.net.nodes(), self.net.edges())
                return
        else:
            if dst == BROADCAST_STR:
                out_port = ofproto.OFPP_FLOOD
                actions = [parser.OFPActionOutput(out_port)]
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                          in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)
                return
            if self._pkt_not_protocol(src, dst):
                # send cross-domain flow request message
                packet_in = msg_proto_parser.TFLCPPacketIn(self.cc_agent, dpid, src, dst)
                xid = self.cc_agent.set_xid(packet_in)
                self.xid_to_packet[xid] = None
                self.xid_to_packet_timestamp[xid] = int(round(time.time() * 10000))
                self.xid_to_buffer_id[xid] = msg.buffer_id
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    self.xid_to_packet[xid] = msg.data
                self.cc_agent.send_msg(packet_in)

    ####################################################################################################################
    # handlers of Messages from the central controller

    def cc_hello_down_handler(self, ev):
        self.logger.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        self.lcid = ev.msg.lcid

    def cc_role_assign_handler(self, ev):
        self.logger.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        dpid = ev.msg.dpid
        role = ev.msg.role
        gid = ev.msg.gid
        datapath = self.datapaths[dpid]
        parser = datapath.ofproto_parser
        role_change = parser.OFPRoleRequest(datapath, role, gid)
        datapath.send_msg(role_change)

    def cc_flow_mod_handler(self, ev):
        self.logger.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        in_dpid = ev.msg.in_dpid
        out_dpid = ev.msg.out_dpid
        dst_mac = ev.msg.dst_mac
        wildcards = ev.msg.wildcards        # 0: the src control-region; 1: not the src control-region
        if out_dpid not in self.dpid_to_is_win:
            self.logger.error("app_manager: out_dpid %d is not window datapath", out_dpid)
            return
        xid = ev.msg.xid
        data = None
        in_dp = self.datapaths[in_dpid]
        buffer_id = in_dp.ofproto.OFP_NO_BUFFER
        if xid in self.xid_to_packet:
            data = self.xid_to_packet[xid]
            buffer_id = self.xid_to_buffer_id[xid]
            del self.xid_to_packet[xid]
            del self.xid_to_packet_timestamp[xid]
            del self.xid_to_buffer_id[xid]
        region_out_port = self.dpid_to_out_port[out_dpid]
        self.logger.info("%%%%%%%%%% inter-region flow:\n in_dpid, out_dpid, region_out_port, dst_mac\n"
                         "%s, %s, %s, %s")
        try:
            path = nx.shortest_path(self.net, in_dpid, out_dpid)
        except nx.NetworkXNoPath:
            self.logger.error("********** No Path, the net is **********\n%s\n%s",
                             self.net.nodes(), self.net.edges())
            return
        self.logger.info("%%%%%%%%%% path is %s", path)
        if buffer_id != in_dp.ofproto.OFP_NO_BUFFER:
            if in_dpid == out_dpid:
                actions = [in_dp.ofproto_parser.OFPActionOutput(region_out_port)]
                match = in_dp.ofproto_parser.OFPMatch(eth_dst=dst_mac)
                self.add_flow(in_dp, 1, match, actions, buffer_id)
                return
            next_hop = path[path.index(in_dpid)+1]
            out_port = self.net.edge[in_dpid][next_hop]['port']
            actions = [in_dp.ofproto_parser.OFPActionOutput(out_port)]
            match = in_dp.ofproto_parser.OFPMatch(eth_dst=dst_mac)
            self.add_flow(in_dp, 1, match, actions, buffer_id)
            for node_index in range(1, len(path)-1):
                out_port= self.net.edge[path[node_index]][path[node_index+1]]['port']
                dpid_path = self.datapaths[path[node_index]]
                actions = [dpid_path.ofproto_parser.OFPActionOutput(out_port)]
                match = dpid_path.ofproto_parser.OFPMatch(eth_dst=dst_mac)
                self.add_flow(dpid_path, 1, match, actions)
            out_dp = self.datapaths[out_dpid]
            actions = [out_dp.ofproto_parser.OFPActionOutput(region_out_port)]
            match = out_dp.ofproto_parser.OFPMatch(eth_dst=dst_mac)
            self.add_flow(out_dp, 1, match, actions)
        else:
            if in_dpid == out_dpid:
                actions = [in_dp.ofproto_parser.OFPActionOutput(region_out_port)]
                match = in_dp.ofproto_parser.OFPMatch(eth_dst=dst_mac)
                self.add_flow(in_dp, 1, match, actions)
                return
            for node_index in range(len(path)-1):
                out_port = self.net.edge[path[node_index]][path[node_index+1]]['port']
                dpid_path = self.datapaths[path[node_index]]
                actions = [dpid_path.ofproto_parser.OFPActionOutput(out_port)]
                match = dpid_path.ofproto_parser.OFPMatch(eth_dst=dst_mac)
                self.add_flow(dpid_path, 1, match, actions)
            out_dp = self.datapaths[out_dpid]
            actions = [out_dp.ofproto_parser.OFPActionOutput(region_out_port)]
            match = out_dp.ofproto_parser.OFPMatch(eth_dst=dst_mac)
            self.add_flow(out_dp, 1, match, actions)
            out = out_dp.ofproto_parser.OFPPacketOut(datapath=out_dp, actions=actions, data=data)
            out_dp.send_msg(out)

    def cc_ctrl_pool_change_handler(self, ev):
        self.logger.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        dpid = ev.msg.dpid
        lc_list = ev.msg.lc_list
        lc_list_str = []
        for lc in lc_list:
            lc_str = lc.type + ':' + lc.ip_addr + ':' + str(lc.port)
            lc_list_str.append(lc_str)

        datapath = self.datapaths[dpid]
        ovsdb_addr = 'tcp:' + datapath.address[0] + ':' + '6632'
        ovs_br = bridge.OVSBridge(self.CONF, dpid, ovsdb_addr)
        ovs_br.init()
        ovs_br.set_controller(lc_list_str)

    def cc_echo_request_handler(self, ev):
        self.logger.debug("app_manager: Event %s Received *** handler starting ...", ev.__class__.__name__)
        timestamp = int(round(time.time() * 10000))
        xid = ev.msg.xid
        echo_reply = msg_proto_parser.TFLCPEchoReply(self.cc_agent, timestamp)
        echo_reply.set_xid(xid)
        self.cc_agent.send_msg(echo_reply)

    ####################################################################################################################
    # other functions

    def _load_report(self):
        while True:
            if self.cc_agent.is_live:
                for dp in self.datapaths.values():
                    dpid = dp.id
                    pkt_in_cnt = self.dpid_to_load.setdefault(dpid, 0)
                    self.dpid_to_load[dpid] = 0
                    load_report = msg_proto_parser.TFLCPLoadReport(self.cc_agent, dpid, pkt_in_cnt)
                    self.cc_agent.send_msg(load_report)
            hub.sleep(cfg.LOAD_REPORT_INTERVAL)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    # packets that should not be transmitted to the center controller
    def _pkt_not_protocol(self, src_mac, dst_mac):
        if dst_mac[0:2] == '33':
            return False
        return True

    # xid_to_packet timeout handler
    def _packet_timeout_handler(self):
        timestamp_now = int(round(time.time() * 10000))
        for xid in self.xid_to_packet_timestamp.keys():
            tmp_timestamp = timestamp_now - self.xid_to_packet_timestamp[xid]
            if tmp_timestamp>cfg.PACKET_OUT_TIMEOUT:
                del self.xid_to_packet[xid]
                del self.xid_to_packet_timestamp[xid]
                del self.xid_to_buffer_id[xid]

    ####################################################################################################################
    # handlers of ryu_topology events

    @set_ev_cls([event.EventSwitchEnter, event.EventLinkAdd])
    def get_topology_data(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        switches = [switch.dp.id for switch in switch_list]
        self.net.add_nodes_from(switches)
        links_list = get_link(self.topology_api_app, None)
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links_list]
        self.net.add_edges_from(links)
        links = [(link.dst.dpid, link.src.dpid, {'port': link.dst.port_no}) for link in links_list]
        self.net.add_edges_from(links)

    @set_ev_cls(event.EventSwitchLeave)
    def switch_leave_handler(self, ev):
        dpid = ev.switch.dp.id
        self.net.remove_node(dpid)
        del self.datapaths[dpid]
        del self.dpid_to_load[dpid]
        del self.dpid_to_inter_connection_port[dpid]
        for mac_t in self.mac_to_port[dpid]:
            try:
                self.net.remove_node(mac_t)
            except:
                pass
        del self.mac_to_port[dpid]
        msg_datapath_leave = msg_proto_parser.TFLCPDatapathLeave(self.cc_agent, dpid)
        self.cc_agent.send_msg(msg_datapath_leave)
