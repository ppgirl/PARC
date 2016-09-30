__author__ = 'Zhang Shaojun'

# this script is to define and store the local-controller level
# topology, which is used for generating inter-domain flow

import networkx

LC_LEVEL_TOPO = networkx.DiGraph()
LC_LEVEL_TOPO.add_node(1, {'type': 'controller', 'win_dpid': [3]})
LC_LEVEL_TOPO.add_node(2, {'type': 'controller', 'win_dpid': [4]})

LC_LEVEL_TOPO.add_edge(1, 2, {'left_dpid': 3, 'out_port': 4, 'right_dpid': 4, 'in_port': 3})        # out_port reversed for future functions
LC_LEVEL_TOPO.add_edge(2, 1, {'left_dpid': 4, 'out_port': 3, 'right_dpid': 4, 'in_port': 3})

win_dpid_to_lcid = {3: 2, 4: 1}            # {dpid:lcid}, the lcid that the window dpid connected to
