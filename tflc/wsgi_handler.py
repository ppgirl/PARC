__author__ = 'Zhang Shaojun'
import wsgi
import json
from webob import Response
from networkx.readwrite import json_graph

class StatsController(wsgi.ControllerBase):
    def __init__(self, req, link, data, **config):
        super(StatsController, self).__init__(req, link, data, **config)
        self.app_manager = data['app_manager']
        self.local_ctrl_list = self.app_manager.local_ctrl_list
        self.lcip_to_lcid = self.app_manager.lcip_to_lcid
        self.datapath_list = self.app_manager.datapath_list
        self.host_to_lcid = self.app_manager.host_to_lcid
        self.LC_LEVEL_TOPO = self.app_manager.LC_LEVEL_TOPO
        self.dp_win = self.app_manager.dp_win
        self.waiters = data['waiters']

    def get_app_name(self, req):
        name = "Central Controller by NDSC 973"
        body = json.dumps(name)
        return Response(content_type='application/json', body=body)

    def get_controller_list(self, req):
        lc_list = {}
        for lcid in self.local_ctrl_list:
            lc_list[lcid] = [self.local_ctrl_list[lcid].address[0], 'live'] \
                if self.local_ctrl_list[lcid].is_active \
                else [self.local_ctrl_list[lcid].address[0], 'dead']
        body = json.dumps(lc_list)
        return Response(content_type='application/json', body=body)

    def get_lc_topo(self, req):
        data = json_graph.node_link_data(self.LC_LEVEL_TOPO)
        body = json.dumps(data)
        return Response(content_type='application/json', body=body)

    def set_lc_topo(self, req):
        data = json.loads(req.body)
        try:
            t_topo = json_graph.node_link_graph(data)
        except Exception:
            return Response(status=400)
        self.app_manager.LC_LEVEL_TOPO = t_topo
        return Response(status=200)

    def get_dp_win(self, req):
        body = json.dumps(self.dp_win)
        return Response(content_type='application/json', body=body)

    def set_dp_win(self, req):
        data = json.loads(req.body)
        if not isinstance(data, dict):
            return Response(status=400)
        self.app_manager.dp_win = data
        return Response(status=200)

    def get_controller(self, req, lcid):
        if str(lcid) == 'all':
            lcs_flat = {}
            for t_id in self.local_ctrl_list:
                lcs_flat[t_id] = self._flat_lc(self.local_ctrl_list[t_id])
            body = json.dumps(lcs_flat)
            return Response(content_type='application/json', body=body)
        lcid = int(lcid)
        lc = self.local_ctrl_list.get(lcid)
        if lc is None:
            return Response(status=404)
        body = json.dumps(self._flat_lc(lc))
        return Response(content_type='application/json', body=body)

    def _flat_lc(self, lc):
        lc_flat = {}
        lc_flat['address'] = lc.address
        lc_flat['id'] = lc.id
        lc_flat['is_active'] = lc.is_active
        lc_flat['dpid_to_role'] = lc.dpid_to_role
        lc_flat['dpid_to_load'] = lc.dpid_to_load
        lc_flat['dp_win'] = lc.dp_win
        return lc_flat

    def get_datapath_list(self, req):
        dpids = self.datapath_list.keys()
        body = json.dumps(dpids)
        return Response(content_type='application/json', body=body)

    def get_datapath(self, req, dpid):
        if str(dpid) == 'all':
            dps_flat = {}
            for t_id in self.datapath_list:
                dps_flat[t_id] = self._flat_dp(self.datapath_list[t_id])
            body = json.dumps(dps_flat)
            return Response(content_type='application/json', body=body)
        dpid = int(dpid)
        dp = self.datapath_list.get(dpid)
        if dp is None:
            return Response(status=404)
        body = json.dumps(self._flat_dp(dp))
        return Response(content_type='application/json', body=body)

    def _flat_dp(self, dp):
        dp_flat = {}
        dp_flat['id'] = dp.id
        dp_flat['mac'] = dp.mac
        dp_flat['lc_home'] = dp.lc_home.id
        lc_connected_ids = []
        for lc in dp.lc_connected:
            lc_connected_ids.append(lc.id)
        dp_flat['lc_connected'] = lc_connected_ids
        dp_flat['load'] = dp.load
        return dp_flat

    def get_host(self, req, lcid):
        lcid_to_host = {}
        for mac in self.host_to_lcid:
            t_lcid = self.host_to_lcid[mac]
            if t_lcid not in lcid_to_host:
                lcid_to_host[t_lcid] = []
            lcid_to_host[t_lcid].append(mac)
        if str(lcid) == 'all':
            body = json.dumps(lcid_to_host)
            return Response(content_type='application/json', body=body)
        lcid = int(lcid)
        if lcid not in lcid_to_host:
            return Response(status=404)
        mac = lcid_to_host[lcid]
        body = json.dumps(mac)
        return Response(content_type='application/json', body=body)
