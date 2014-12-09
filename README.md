# CS 143 Network Simulator and Editor

## Authors

* *Ryan Batterman* - Structure, Bellman-Ford, TCP Reno for Simulator
* *Joseph Choi* - Code Documentation for Simulator, Network Editor
* *Archan Luhar* - Structure Debugging, Graphing for Simulator
* *Kevin Yang* - FAST TCP for Simulator

## Network Simulator

### Prerequisites

* Python 3
* matplotlib

### Running the simulator

To run the program:
```bash
python3 network_simulator/Controller.py -f [jsonfile]
```

Example:
```bash
python3 network_simulator/Controller.py -f test_cases/test0.json
```

This will generate graphs of the flow rate, link rate, buffer occupancy, packet
loss, and window size.

## Network Editor

### Prerequisites

* Google Chrome

### Running the editor

Open the file `network_editor/main.html` in your web browser. For instance, on
Linux, you can open the network editor in Google Chrome by running the command:

```bash
google-chrome network_editor/main.html
```

It is highly recommended that Google Chrome is the web browser used to run the
network editor. The network editor has not been tested for compatibility on
Firefox, Safari, or Internet Explorer yet.

## Input file format

JSON is used to specify the structure of the network. The JSON file should
contain a single object, consisting of the following keys:

* **routers**
  * *id* - The id of the router device, typically specified as the character 'R' followed by the id number, starting at 1.
  * *links* - An array of link ids of the links that are connected to the host.
  * *routing_table* - The routing table mapping host ids to link ids.
  * *BFfreq* The frequency to use with the Bellman-Ford algorithm.
* **hosts**
  * *id* - The id of the host device, typically specified as the character 'H' followed by the id number, starting at 1.
  * *links* - An array of link ids of the links that are connected to the host.
* **links**
  * *id* - The id of the link, typically specified as the character 'L' followed by the id number, starting at 1.
  * *left_device_id* - The id of the device on the left.
  * *right_device_id* - The id of the device on the right.
  * *throughput* - The throughput in bits/sec (bps).
  * *link_delay* - The link delay in seconds (s).
  * *buffer_size* - The buffer size in bytes (B).
  * *show_on_plot* - True to show this link on the plot.
* **flows**
  * *id* - The id of the flow, typically specified as the character 'F' followed by the id number, starting at 1.
  * *src_id* - The id of the source device.
  * *dst_id* - The id of the destination device.
  * *num_bytes* - The number of bytes to transfer.
  * *start_time* - The time the flow starts.
  * *tcp* - The TCP algorithm to use, e.g. 'reno'.
  * *show_on_plot* - True to show this flow on the plot.