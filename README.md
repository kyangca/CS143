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

### Usage

The Network Editor is a web application that can be used to create and edit
networks.

#### Create hosts

Start out by creating a host. This is done by right-clicking on the middle of
the screen, and selecting the option "Create Host". This will create a square
representing a host on the position you selected. You might notice that the
cursor is now in the middle of the host. You can type into the box representing
the host to change its name. Now right-click somewhere nearby and create a
second host.

#### Create links

You can create links in two ways:

* One way is by right-clicking on one of the devices you want to link, clicking
the option "Link To..." and then clicking on the other device.
* Another way is to right-click on the background, then click "Create Link",
then click on the two devices that you want to link together.

You can then rename the link by clicking on the grey circle on the middle of the
line representing the link, and typing in the name.

#### Create routers

Routers are created in the same way as hosts, and are represented by circles.

#### Import

To import a JSON file for a network, click on the "Import" button at the top.
This will bring up a file dialog, from which you can select the file to import.
You can try this out with the included test cases under `test_cases`.

#### Export

To export the network to a JSON file, click on the "Export" button at the top.
This will bring up a file dialog for where you want to save the file.

## Input file format

JSON is used to specify the structure of the network. The JSON file should
contain a single object, consisting of the following keys:

* **routers**
  * *id* - The id of the router device, typically specified as the character 'R'
followed by the id number, starting at 1.
  * *links* - An array of link ids of the links that are connected to the host.
  * *routing_table* - The routing table mapping host ids to link ids.
  * *BFfreq* The frequency to use with the Bellman-Ford algorithm.
* **hosts**
  * *id* - The id of the host device, typically specified as the character 'H'
followed by the id number, starting at 1.
  * *links* - An array of link ids of the links that are connected to the host.
* **links**
  * *id* - The id of the link, typically specified as the character 'L' followed
by the id number, starting at 1.
  * *left_device_id* - The id of the device on the left.
  * *right_device_id* - The id of the device on the right.
  * *throughput* - The throughput in bits/sec (bps).
  * *link_delay* - The link delay in seconds (s).
  * *buffer_size* - The buffer size in bytes (B).
  * *show_on_plot* - True to show this link on the plot.
* **flows**
  * *id* - The id of the flow, typically specified as the character 'F' followed
by the id number, starting at 1.
  * *src_id* - The id of the source device.
  * *dst_id* - The id of the destination device.
  * *num_bytes* - The number of bytes to transfer.
  * *start_time* - The time the flow starts.
  * *tcp* - The TCP algorithm to use, e.g. 'reno'.
  * *show_on_plot* - True to show this flow on the plot.