#!/usr/bin/python
__author__ = 'Zhang Shaojun'

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel


def two_region():
    """Create a network from semi-scratch with multiple controllers."""

    net = Mininet(controller=RemoteController, switch=OVSSwitch, autoSetMacs=True)

    print "*** Creating controllers"
    c1 = net.addController('c1', ip='192.168.124.128', port=6633)
    c2 = net.addController('c2', ip='192.168.124.129', port=6633)

    print "*** Creating switches"
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')
    s5 = net.addSwitch('s5')
    s6 = net.addSwitch('s6')

    print "*** Creating hosts"
    hosts1 = [net.addHost('h%d' % n) for n in 1, 2]
    hosts2 = [net.addHost('h%d' % n) for n in 3, 4]
    hosts3 = [net.addHost('h%d' % n) for n in 5, 6]
    hosts4 = [net.addHost('h%d' % n) for n in 7, 8]
    hosts5 = [net.addHost('h%d' % n) for n in 9, 10]
    hosts6 = [net.addHost('h%d' % n) for n in 11, 12]

    print "*** Creating links"
    for h in hosts1:
        net.addLink(s1, h)
    for h in hosts2:
        net.addLink(s2, h)
    for h in hosts3:
        net.addLink(s3, h)
    for h in hosts4:
        net.addLink(s4, h)
    for h in hosts5:
        net.addLink(s5, h)
    for h in hosts6:
        net.addLink(s6, h)
    net.addLink(s1, s2)
    net.addLink(s2, s3)
    link_inter_region_1_2 = net.addLink(s3, s4)
    net.addLink(s4, s5)
    net.addLink(s5, s6)

    for link in net.links:
        if link == link_inter_region_1_2:
            left_s = link.intf1.node
            left_p = left_s.ports[link.intf1]
            left_s_dpid = left_s.dpid
            right_s = link.intf2.node
            right_p = right_s.ports[link.intf2]
            right_s_dpid = right_s.dpid
            print "##### inter-region link from r1 to r2 is:"
            print "      left switch:", left_s, "dpid:", left_s_dpid, "window port:", left_p
            print "      right switch:", right_s, "dpid:", right_s_dpid, "window port:", right_p
            print "      please modify the topo in cc_client and tflc"


    print "*** Starting network"
    net.build()
    c1.start()
    c2.start()
    s1.start([c1])
    s2.start([c1])
    s3.start([c1])
    s4.start([c2])
    s5.start([c2])
    s6.start([c2])

    print "*** Running CLI"
    CLI(net)

    print "*** Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )  # for CLI output
    two_region()
