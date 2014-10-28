import json
from Link import Link
from Device import Host
from Flow import Flow
from EventQueue import EventQueue

class Controller:
    __current_time = 0.0

    # Initialize with the network specified in the given file.
    @classmethod
    def init(cls, filename):
        json_network = json.loads(open(filename).read())

        #TODO: add code for dealing with routers.
        json_hosts = json_network['hosts']
        json_links = json_network['links']
        json_flows = json_network['flows']

        links = {}
        devices = {}

        for json_link in json_links:
            link_id = json_link['id']
            link_throughput = json_link['throughput']
            link_buffer_size = json_link['buffer_size']
            link_delay = json_link['link_delay']
            links[link_id] = Link(None, None, link_throughput,
                                  link_delay, link_buffer_size,
                                  link_id)

        for json_host in json_hosts:
            host_id = json_host['id']
            host_link_ids = json_host['links']
            host_links = [links[x] for x in host_link_ids]
            devices[host_id] = Host(host_links, host_id)

        # Now add the references to the devices onto the links
        for json_link in json_links:
            link_left_device_id = json_link['left_device_id']
            left_device = devices[link_left_device_id]
            link_right_device_id = json_link['right_device_id']
            right_device = devices[link_right_device_id]
            link_id = json_link['id']
            links[link_id].set_left_device(left_device)
            links[link_id].set_right_device(right_device)

        for json_flow in json_flows:
            # Instantiate the flow in the source host and the event in EventQueue
            src_id = json_flow['src_id']
            dst_id = json_flow['dst_id']
            num_bytes = json_flow['num_bytes']
            flow_start = json_flow['start_time']
            flow_id = json_flow['id']
            src_host = devices[src_id]
            flow = Flow(src_id, dst_id, num_bytes)
            src_host.add_flow(flow_id, flow)
            EventQueue.add_event(flow_start, src_host.send_next_packet, [flow])

    @classmethod
    def get_current_time(cls):
        return cls.__current_time

    @classmethod
    def run(cls, num_seconds):
        while (not EventQueue.is_empty() and cls.get_current_time() < num_seconds):
            event_time, event_method, event_args = EventQueue.pop_event()
            cls.__current_time = event_time
            event_method(*event_args)

Controller.init('test0.json')
Controller.run()
