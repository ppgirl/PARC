__author__ = 'Zhang Shaojun'
import networkx
import json
from networkx.readwrite import json_graph

LC_LEVEL_TOPO = networkx.DiGraph()
LC_LEVEL_TOPO.add_node(1, {'type': 'controller', 'win_dpid': [2]})
LC_LEVEL_TOPO.add_node(2, {'type': 'controller', 'win_dpid': [5]})

LC_LEVEL_TOPO.add_edge(1, 2, {'left_dpid': 2, 'out_port': 2})        # out_port reversed for future functions
LC_LEVEL_TOPO.add_edge(2, 1, {'left_dpid': 5, 'out_port': 5})

data = json_graph.node_link_data(LC_LEVEL_TOPO)
json.dump(data, open('lc_topo_json.dat', 'w'))
