#!/usr/bin/python

from collections import defaultdict
from Device import Host, Router
from EventQueue import EventQueue
from Flow import Flow
from Link import Link
import matplotlib
from matplotlib import pyplot
from optparse import OptionParser
import json
import numpy

font = {
        'weight' : 'bold',
        'size'   : 9}

matplotlib.rc('font', **font)

class Controller(object):
    """The main controller class.

    Attributes:
        _filename: The filename of the JSON representation of the network that
            will be used in the simulation.
        _debug: The debug data for the simualtion.
        _current_time: The current time in the simulation, in seconds.
        _log_interval_start: The start time of collecting log data, in seconds.
        _log_interval_length: The length of time for collecting log data, in
            seconds.
        _event_queue: The event queue object, which keeps track of the events
            that happen and the order in which they happen.
        _links: The list of links in the network.
        _devices: The list of devices (hosts and routers) in the network.
        _flows: The list of flows in the network, which represents the data
            source and destination.
        _logs: The logs resulting from the simulation.
        _show_on_plot: The set of links to show on the plot.
    """

    def __init__(self, options):
        """Initializes the Controller instance.

        Args:
            options: A dictionary with option attributes. Currently supported
                options are 'filename' and 'debug'.
        """
        self._filename = options['filename']
        self._debug = options['debug']
        self._current_time = 0.0
        self._log_interval_start = 0.0
        if ('log_interval_length' in options and options['log_interval_length']
                is not None):
            self._log_interval_length = float(options['log_interval_length'])
        else:
            self._log_interval_length = 1.0
        self._event_queue = EventQueue()

        self._links = {}
        self._devices = {}
        self._flows = {}

        self._logs = {}
        self._show_on_plot = set()

        # Opens the file and parses the JSON representation of the network.
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
            if 'show_on_plot' in json_link and json_link['show_on_plot']:
                self._show_on_plot.add(link_id)

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
            if "routing_table" in json_router:
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
                tcp,
                num_bytes
                )
            src_host.add_flow(flow_id, flow)
            self._event_queue.add_event(flow_start, src_host.send_next_packet,
                [flow])
            self._flows[flow_id] = True
            if 'show_on_plot' in json_flow and json_flow['show_on_plot']:
                self._show_on_plot.add(flow_id)
        self.devices = self._devices

    def add_event(self, *args):
        """Adds an event to the event queue.

        Args:
            *args: The events the add.
        """
        self._event_queue.add_event(*args)

    def get_current_time(self):
        """Returns the current time in the network simulation.

        Returns:
            The current time.
        """
        return self._current_time

    def remove_flow(self, flow):
        """Removes a flow from the network simulation.

        Args:
            flow: The flow to remove.
        """
        self._flows.pop(flow.get_flow_id())

    def _process_temp_interval_values(self):
        """Moves data point into X, Y lists and resets all temp intervals.
        """
        interval_length = min(self._log_interval_length,
            self._current_time - self._log_interval_start)

        for log_type in self._logs:
            if 'devices' in self._logs[log_type]:
                devices_logs = self._logs[log_type]['devices']

                for device_name in devices_logs:
                    device_log = self._logs[log_type]['devices'][device_name]

                    temp_values = device_log['temp_interval_values']
                    if temp_values:
                        time = self._log_interval_start + interval_length / 2.0
                        aggregated_value = self._logs[log_type] \
                            ['values_aggregator'](temp_values, interval_length)

                        self._new_point(log_type, device_name, time,
                            aggregated_value)

                        device_log['temp_interval_values'] = []

        self._log_interval_start = int(self._current_time /
            self._log_interval_length) * self._log_interval_length

    def _new_point(self, log_type, device_name, x, y):
        """Creates a new point in the plot and draws.

        Args:
            log_type: The type of log.
            device_name: The name of th device for the point.
            x: The x position of the point.
            y: The y position of the point.
        """
        line = self._logs[log_type]['devices'][device_name]['line']
        line.set_xdata(numpy.append(line.get_xdata(), x))
        line.set_ydata(numpy.append(line.get_ydata(), y))
        self._logs[log_type]['subplot'].set_ymargin(0.05)
        self._logs[log_type]['subplot'].relim()
        self._logs[log_type]['subplot'].autoscale_view()
        self._logs[log_type]['subplot'].set_ylim(bottom=0, auto=True)
        pyplot.draw()

    def log(
        self,
        log_type,
        device_name,
        value,
        values_aggregator=lambda values, interval_length:
            sum(values) / float(len(values)),
        ylabel=None,
    ):
        """Logs the data using a given aggregator.

        Args:
            log_type: The type of log.
            device_name: The name of the device.
            value: The value to log.
            values_aggregator: Function that takes values, and aggregates them.
                By default, the average aggregator is used.
            ylabel: The label on the y-axis. By default, the log type is used.
        """
        if device_name not in self._show_on_plot:
            return
        if ylabel is None:
            ylabel = log_type

        assert(log_type in self._logs)
        if 'devices' not in self._logs[log_type]:
            self._logs[log_type]['devices'] = {}
            self._logs[log_type]['values_aggregator'] = values_aggregator
            self._logs[log_type]['min_y'] = 0.0
            self._logs[log_type]['max_y'] = 1.0
            self._logs[log_type]['min_x'] = 0.0
            self._logs[log_type]['max_x'] = 15.0
            self._logs[log_type]['ylabel'] = ylabel
            self._logs[log_type]['subplot'].set_ylabel(ylabel)

        if device_name not in self._logs[log_type]['devices']:
            self._logs[log_type]['devices'][device_name] = {
                'temp_interval_values': [],
            }
            self._logs[log_type]['devices'][device_name]['line'], = \
                self._logs[log_type]['subplot'].plot([], [], label=device_name)
            self._logs[log_type]['subplot'].legend(bbox_to_anchor=(1.1, 1.0))

        if (self._current_time - self._log_interval_length >=
                self._log_interval_start):
            self._process_temp_interval_values()

        self._logs[log_type]['devices'][device_name]['temp_interval_values'] \
            .append(value)

    def init_graphing(self):
        """Initializes the graphing functionality.
        """
        pyplot.ion()

        subplots = (
            'flow-rate',
            'window-size',
            'link-rate',
            'buffer-occupancy',
            'packet-loss'
        )
        f, axarr = pyplot.subplots(len(subplots), sharex=True)

        for index, subplot in enumerate(subplots):
            self._logs[subplot] = {}
            self._logs[subplot]['subplot'] = axarr[index]

        axarr[-1].set_xlabel('time (s)')
        pyplot.autoscale()

    def run(self, num_seconds):
        """Runs the simulation.

        Args:
            num_seconds: The number of seconds to run the simulation.
        """
        while (
            not self._event_queue.is_empty()
            and self.get_current_time() < num_seconds
            and len(self._flows) > 0
        ):
            event = self._event_queue.pop_event()
            # if self._debug:
            #     # TODO: add better debugging here.
            #     print(event)
            event_time, event_method, event_args = event
            self._current_time = event_time
            event_method(*event_args)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
        help="Test json filename (e.g. test0.json)")
    parser.add_option("-i", "--interval", dest="log_interval_length",
        help="Log interval length as float > 0.0")
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose",
        default=True, help="don't print status messages to stdout")
    parser.add_option("--debug", action="store_true")
    options, _ = parser.parse_args()

    network_controller = Controller(vars(options))

    network_controller.init_graphing()
    network_controller.run(float('inf'))

    # This is necessary since otherwise the graph window disappears after the
    # simulation finishes.
    input()
