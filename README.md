# PARC
A hierarchical control plane for SDN (Software-Defined Networking) with a central controller and several local controllers.  
PARC is the highlights of this system, which means a Control plane with features like Partition, Abstract and Recursion.  
The local agent is run on ryu, and the topology can be based on mininet.  
# Steps
0. The package tflc is the code of central controller and package cc_client is the code of the local controller, which runs on ryu.
1. Design a LOCAL CONTROLLER topology with their links and ports represented, then update lc_level_topo.py in tflc and cfg.py in cc_client according to the LOCAL CONTROLLER topology.
2. On the central controller, run tflc.py to start the central controller. You can also use REST debug tools like POSTMAN to check the status and parameter, reference: `tflc/app_manager.py line 287`. 
3. On local controllers, run the local client using `ryu-manager --observe-links layer_2_switch.py`. `--observe-links` is used to discover the switch topology in the controller's control domain.
