from pox.core import core
import pox.openflow.libopenflow_01 as of

# Logger for printing controller messages
log = core.getLogger()

# Flow timeout in seconds
FLOW_TIMEOUT = 10

class TimeoutSwitch(object):
    def __init__(self, connection):
        """
        Constructor: runs when switch connects to controller
        """
        self.connection = connection

        # Register event listeners (PacketIn, FlowRemoved, etc.)
        connection.addListeners(self)

        # MAC address table: maps MAC → port
        self.mac_to_port = {}

    def _handle_PacketIn(self, event):
        """
        Handles incoming packets from switch
        (Triggered when no matching flow rule exists)
        """
        packet = event.parsed
        in_port = event.port

        # Ignore incomplete packets
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        # Extract source and destination MAC
        src = packet.src
        dst = packet.dst

        # 🔹 Learn source MAC → port mapping
        self.mac_to_port[src] = in_port

        log.info(f"[PACKET_IN] {src} → {dst} received on port {in_port}")

        # 🔹 Case 1: Destination is known → install flow rule
        if dst in self.mac_to_port:
            out_port = self.mac_to_port[dst]

            log.info(f"[FLOW_INSTALL] {src} → {dst} | timeout={FLOW_TIMEOUT}s")

            # Create flow rule
            msg = of.ofp_flow_mod()

            # Match fields (Layer 2 matching)
            msg.match.dl_src = src
            msg.match.dl_dst = dst

            # 🔹 Timeout settings
            msg.idle_timeout = FLOW_TIMEOUT   # expires if no traffic
            msg.hard_timeout = 0              # no forced expiry

            # 🔹 Ask switch to notify when flow is removed
            msg.flags |= of.OFPFF_SEND_FLOW_REM

            # Action: forward to correct port
            msg.actions.append(of.ofp_action_output(port=out_port))

            # Send flow rule to switch
            self.connection.send(msg)

            # 🔹 Also forward the CURRENT packet
            # (otherwise first packet will be dropped)
            packet_out = of.ofp_packet_out()
            packet_out.data = event.ofp
            packet_out.actions.append(of.ofp_action_output(port=out_port))
            self.connection.send(packet_out)

        # 🔹 Case 2: Destination unknown → flood
        else:
            log.info(f"[FLOOD] Unknown destination {dst}, flooding...")

            msg = of.ofp_packet_out()
            msg.data = event.ofp

            # Send packet to all ports except incoming
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))

            self.connection.send(msg)

    def _handle_FlowRemoved(self, event):
        """
        Triggered when a flow rule expires or is removed
        Used to track rule lifecycle
        """
        reason = event.ofp.reason

        # Determine why flow was removed
        if reason == of.OFPRR_IDLE_TIMEOUT:
            reason_str = "IDLE TIMEOUT"
        elif reason == of.OFPRR_HARD_TIMEOUT:
            reason_str = "HARD TIMEOUT"
        else:
            reason_str = "OTHER"

        log.info(f"[FLOW_REMOVED] Flow expired due to {reason_str}")

def launch():
    """
    Entry point of POX module
    Runs when controller starts
    """
    def start_switch(event):
        log.info("Timeout Controller Started")
        TimeoutSwitch(event.connection)

    # Listen for switch connection event
    core.openflow.addListenerByName("ConnectionUp", start_switch)
