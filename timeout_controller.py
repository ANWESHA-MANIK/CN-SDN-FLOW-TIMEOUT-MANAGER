from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

FLOW_TIMEOUT = 10  # seconds


class TimeoutSwitch(object):

    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)
        self.mac_to_port = {}

    def _handle_PacketIn(self, event):
        packet = event.parsed
        in_port = event.port

        src = packet.src
        dst = packet.dst

        # Learn MAC address
        self.mac_to_port[src] = in_port

        # If destination known → install flow
        if dst in self.mac_to_port:
            out_port = self.mac_to_port[dst]

            log.info(f"Installing flow: {src} -> {dst} with timeout {FLOW_TIMEOUT}s")

            # Create flow rule
            msg = of.ofp_flow_mod()
            msg.match.dl_src = src
            msg.match.dl_dst = dst

            # Set timeouts
            msg.idle_timeout = FLOW_TIMEOUT
            msg.hard_timeout = FLOW_TIMEOUT

            # Action → forward packet
            msg.actions.append(of.ofp_action_output(port=out_port))

            # Send flow rule to switch
            self.connection.send(msg)

            #IMPORTANT: also forward the current packet
            packet_out = of.ofp_packet_out()
            packet_out.data = event.ofp
            packet_out.actions.append(of.ofp_action_output(port=out_port))
            self.connection.send(packet_out)

        # If destination unknown → flood
        else:
            msg = of.ofp_packet_out()
            msg.data = event.ofp
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            self.connection.send(msg)


def launch():
    def start_switch(event):
        log.info("Timeout Controller Started")
        TimeoutSwitch(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
