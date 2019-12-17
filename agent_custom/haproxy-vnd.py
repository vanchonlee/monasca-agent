import time

from haproxyadmin import utils
from haproxyadmin import haproxy
import haproxyadmin as ha
import requests
import json

import monasca_agent.collector.checks as checks


class services():
    def __init__(self):
        self.hap = haproxy.HAProxy(socket_dir='/var/lib/octavia')
        self.frontend_metrics = {}
        self.backend_metrics = {}
        self.server_metrics = {}
        self.FRONTEND = "frontend"
        self.BACKEND = "backend"
        self.SERVER = "server"

    def fetch_data(self):
        # lay metric tu tat cac cac frontend 
        for frontend in self.hap.frontends():
            frontend_metric_tmp = {}
            
            for metric in ha.FRONTEND_METRICS:
                value_metric_tmp = frontend.metric(metric)
                frontend_metric_tmp[metric] = value_metric_tmp
            
            self.frontend_metrics[frontend.name] = frontend_metric_tmp

        # lay metric tu tat ca backend 
        for backend in self.hap.backends():
            backend_metrics_tmp = {}

            for metric in ha.BACKEND_METRICS:
                value_metric_tmp = backend.metric(metric)
                backend_metrics_tmp[metric] = value_metric_tmp

            self.backend_metrics[backend.name] = backend_metrics_tmp

        # lay metric tu tat ca server
        for server in self.hap.servers():
            server_metrics_tmp = {}

            for metric in ha.SERVER_METRICS:
                value_metric_tmp = server.metric(metric)
                server_metrics_tmp[metric] = value_metric_tmp

            self.server_metrics[server.name] = server_metrics_tmp
        
        # print(self.server_metrics)
        

class haproxy_vnd(checks.AgentCheck):
    def __init__(self, name, init_config, agent_config):
        checks.AgentCheck.__init__(self, name, init_config, agent_config)
        self.delegated_tenant_id = ""

    def check(self, instance):

        metadata = requests.get("http://169.254.169.254/openstack/2017-02-22/meta_data.json")
        metadata = json.loads(metadata.content)['meta']
        try:
            self.delegated_tenant_id = metadata["tenant_id"]
            product = metadata["product"]
            lb_id = metadata["loadbalancer_id"]
            lb_name = metadata["loadbalancer_name"]
        except KeyError as e:
            self.log.debug('KeyError metadata: %s' % e)

        self.dimensions = self._set_dimensions({
            'service':'haproxy',
            'product':product,
            'loadbalancer_id': lb_id,
            'loadbalancer_name': lb_name,
        }, instance)


        # self.delegated_tenant_id = self.dimensions.pop("delegated_tenant_id")

        #self.log.debug('Processing HAProxy data for %s' % url)
        service = services()
        service.fetch_data()
        if self.delegated_tenant_id != "":
            self.process_metric(service.frontend_metrics,service.FRONTEND)
            self.process_metric(service.backend_metrics,service.BACKEND)
            self.process_metric(service.server_metrics,service.SERVER)

    def process_metric(self, metric_data, prefix):
        for key in metric_data:            
            dimensions_metric = self.dimensions.copy()
            dimensions_metric.update({prefix:key})

            for metric_name in metric_data[key]:
                value = metric_data[key][metric_name]
                name = "haproxy.%s.%s" % (prefix, metric_name)
                self.gauge(name,value,dimensions=dimensions_metric, delegated_tenant=self.delegated_tenant_id)