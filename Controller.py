#!/usr/bin/python

from collections import defaultdict
from Device import Host, Router
from EventQueue import EventQueue
from Flow import Flow
from Link import Link
from matplotlib import pyplot
from optparse import OptionParser
import json

class Controller(object):
    """The main controller class.
    """

    def __init__(self, options):
        self._filename = options['filename']
        self._debug = options['debug']
        self._current_time = 0.0
        self._event_queue = EventQueue()

        self._links = {}
        self._devices = {}
        self._flows = {}

        self._logs = {}

        with open(self._filename) as f:
            json_network = json.loads(f.read())

        json_hosts = json_network['hosts']
        json_links = json_network['links']
        json_flows = json_network['flows']
        json_routers = json_network['routers']

        links = {}
        devices = {}

        for json_link in json_links:
            link_id = json_link['id']
            self._links[link_id] = Link(
                controller=self,
                left_device=None,
                right_device=None,
                throughput=json_link['throughput'],
                link_delay=json_link['link_delay'],
                buffer_size=json_link['buffer_size'],
                link_id=link_id,
                )

        for json_host in json_hosts:
            host_id = json_host['id']
            self._devices[host_id] = Host(
                controller=self,
                links={x: self._links[x] for x in json_host['links']},
                device_id=host_id,
                )

        for json_router in json_routers:
            router_id = json_router['id']
            # Get the statically generated routing table.
            if ("routing_table" in json_router):
                routing_table = json_router["routing_table"]
            else:
                routing_table = {}
            self._devices[router_id] = Router(
                controller=self,
                links={x: self._links[x] for x in json_router['links']},
                device_id=router_id,
                bf_freq=json_router['BFfreq'],
                routing_table=routing_table
                )

        # Now add the references to the devices onto the links.
        for json_link in json_links:
            link_id = json_link['id']
            link_left_device_id = json_link['left_device_id']
            link_right_device_id = json_link['right_device_id']

            left_device = self._devices[link_left_device_id]
            right_device = self._devices[link_right_device_id]

            self._links[link_id].set_left_device(left_device)
            self._links[link_id].set_right_device(right_device)

        for json_flow in json_flows:
            # Instantiate the flow in the source host and the event in
            # EventQueue.
            src_id = json_flow['src_id']
            dst_id = json_flow['dst_id']
            num_bytes = json_flow['num_bytes']
            flow_start = json_flow['start_time']
            flow_id = json_flow['id']
            tcp = json_flow['tcp']
            src_host = self._devices[src_id]
            flow = Flow(
                self,
                src_id,
                dst_id,
                flow_id,
                num_bytes,
                tcp
                )
            src_host.add_flow(flow_id, flow)
            self._event_queue.add_event(flow_start, src_host.send_next_packet,
                [flow])
            self._flows[flow_id] = True
        self.devices = self._devices

    def add_event(self, *args):
        self._event_queue.add_event(*args)

    def get_current_time(self):
        return self._current_time

    def remove_flow(self, flow):
        self._flows.pop(flow.get_flow_id())

    def log(self, device_type, device_name):
        if device_type not in self._logs:
            self._logs[device_type] = defaultdict(list)

        self._logs[device_type][device_name].append(self._current_time)

    def run(self, num_seconds):
        """Runs the simulation.

        Args:
            num_seconds: The number of seconds to run the simulation.
        """
        while (not self._event_queue.is_empty() and self.get_current_time() <
                num_seconds and len(self._flows) > 0):
            event = self._event_queue.pop_event()
            if (self._debug):
                # TODO: add better debugging here.
                print(event)
            event_time, event_method, event_args = event
            self._current_time = event_time
            event_method(*event_args)

    def plot(self):
        figure = 1
        for device_type in network_controller._logs:
            pyplot.figure(figure)
            pyplot.title(device_type)
            for device_name in network_controller._logs[device_type]:
                X = []
                Y = []
                times = network_controller._logs[device_type][device_name]
                for idx, t in enumerate(times):
                    low_idx = idx
                    while (low_idx >= 1 and  t - times[low_idx - 1] <= 0.8):
                        low_idx -= 1
                    if (times[idx] == times[low_idx]):
                        continue
                    y_val = 1024 * (idx - low_idx) / (times[idx] - times[low_idx])
                    X.append(t)
                    Y.append(y_val)
                pyplot.plot(X, Y)
            figure += 1
        pyplot.show()

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
        help="Test json filename (e.g. test0.json)")
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose",
        default=True, help="don't print status messages to stdout")
    parser.add_option("--debug", action="store_true")
    options, _ = parser.parse_args()

    network_controller = Controller(vars(options))
    network_controller.run(float('inf'))
    network_controller.plot()
