# CS 143 Network Simulator

## Authors

Ryan Batterman, Joseph Choi, Archan Luhar, Kevin Yang

## Running the program

To run the program:
```
python3 Controller.py -f [jsonfile]
```

Example:
```
python3 Controller.py -f test_cases/test0.json
```

This will generate graphs of the flow rate, buffer occupancy, link rate, and
window size.

## JSON

JSON is used to specify the structure of the network. The JSON file should
contain a single object, consisting of the following keys:

* **routers**
  * *id* - The id of the router device, usually specified as the character 'R' followed by the id number, starting at 1.
  * *links* - An array of link ids of the links that are connected to the host.
  * *routing_table* - The routing table mapping host ids to link ids.
  * *BFFreq* The frequency to use with the Bellman-Ford algorithm.
* **hosts**
  * *id* - The id of the host device, usually specified as the character 'H' followed by the id number, starting at 1.
  * *links* - An array of link ids of the links that are connected to the host.
* **links**
  * *id* - The id of the link, usually specified as the character 'L' followed by the id number, starting at 1.
  * *left_device_id* - The id of the device on the left.
  * *right_device_id* - The id of the device on the right.
  * *throughput* - The throughput in bits/sec (bps).
  * *link_delay* - The link delay in seconds (s).
  * *buffer_size* - The buffer size in bytes (B).
  * *show_on_plot* - True to show this link on the plot.
* **flows**
  * *id* - The id of the flow, usually specified as the character 'F' followed by the id number, starting at 1.
  * *src_id* - The id of the source device.
  * *dst_id* - The id of the destination device.
  * *num_bytes* - The number of bytes to transfer.
  * *start_time* - The time the flow starts.
  * *tcp* - The TCP algorithm to use, e.g. 'reno'.
  * *show_on_plot* - True to show this flow on the plot.