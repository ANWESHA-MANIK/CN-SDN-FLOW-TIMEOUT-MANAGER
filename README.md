# SDN Flow Rule Timeout Manager (Mininet + POX)

## Problem Statement

This project implements a Software Defined Networking (SDN) solution using Mininet and a POX controller. The objective is to demonstrate flow rule installation with timeout-based management, where rules automatically expire and are dynamically reinstalled when new traffic arrives.

---

### Setup Instructions

### 1. Install Mininet

sudo apt install mininet

### 2. Clone POX Controller

git clone https://github.com/noxrepo/pox
cd pox

### 3. Run Controller

python3.8 pox.py log.level --DEBUG timeout_controller

### 4. Run Mininet

sudo mn --topo single,3 --controller=remote

---

## Implementation Details

* Implemented a learning switch using POX controller

* Controller handles PacketIn events

* Flow rules are installed using OpenFlow protocol

* Each flow rule includes:

  * Source MAC address match
  * Destination MAC address match
  * Output port action

* Timeout mechanism implemented:

  * idle_timeout = 10 seconds
  * hard_timeout = 10 seconds

* Flow rules are automatically removed after timeout

* New packets trigger reinstallation of flow rules

---

## Test Scenarios

### Scenario 1: Normal Communication

* Run: pingall
* All hosts successfully communicate
* Flow rules are installed in the switch

### Scenario 2: Timeout Behavior

* Run: pingall
* Wait for 10–15 seconds
* Run: pingall again
* Controller reinstalls flow rules

---

## Flow Table Observation (Flow History)

Flow entries are observed using:

sh ovs-ofctl dump-flows s1

Each flow entry contains:

* n_packets → number of packets matched
* n_bytes → amount of data transferred
* duration → how long the flow existed
* idle_timeout → removed if no activity
* hard_timeout → removed after fixed time

This represents the history and statistics of each flow.

---

## Proof of Execution

Screenshots included:

* Controller logs showing flow installation
* Successful ping results (0% packet loss)
* Flow table entries with packet and byte counters
* Timeout behavior (flow removal and reinstallation)

---

## Concepts Used

* Software Defined Networking (SDN)
* OpenFlow Protocol
* Flow Tables (match-action rules)
* Idle Timeout and Hard Timeout
* Controller–Switch interaction

---

## Conclusion

This project demonstrates how SDN controllers dynamically manage flow rules using timeout mechanisms. Flow entries are automatically removed after a fixed duration and reinstalled when new traffic is detected, ensuring efficient and flexible network control.

-------
