# (C) Copyright 2015 Hewlett Packard Enterprise Development Company LP
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Windows Only.

Generic WMI check. This check allows you to specify particular metrics that you
want from WMI in your configuration. Check wmi.yaml.example in your conf.d
directory for more details on configuration.
"""
try:
    import wmi
except Exception:
    wmi = None

from monasca_agent.collector.checks import AgentCheck

UP_METRIC = 'Up'
SEARCH_WILDCARD = '*'


class WMICheck(AgentCheck):

    def __init__(self, name, init_config, agent_config):
        AgentCheck.__init__(self, name, init_config, agent_config)
        self.wmi_conns = {}

    def _get_wmi_conn(self, host, user, password):
        key = "%s:%s:%s" % (host, user, password)
        if key not in self.wmi_conns:
            self.wmi_conns[key] = wmi.WMI(computer=host, user=user,
                                          password=password)
        return self.wmi_conns[key]

    def check(self, instance):
        if wmi is None:
            raise Exception("Missing 'wmi' module")

        host = instance.get('host', None)
        user = instance.get('username', None)
        password = instance.get('password', None)
        w = self._get_wmi_conn(host, user, password)

        wmi_class = instance.get('class')
        metrics = instance.get('metrics')
        filters = instance.get('filters')
        tag_by = instance.get('tag_by')

        if not wmi_class:
            raise Exception('WMI instance is missing a value for `class` in wmi.yaml')

        # If there are filters, we need one query per filter.
        if filters:
            for f in filters:
                prop = list(f.keys())[0]
                search = list(f.values())[0]
                if SEARCH_WILDCARD in search:
                    search = search.replace(SEARCH_WILDCARD, '%')
                    wql = "SELECT * FROM %s WHERE %s LIKE '%s'" % (wmi_class, prop, search)
                    results = w.query(wql)
                else:
                    results = getattr(w, wmi_class)(**f)
                self._extract_metrics(results, metrics, tag_by, instance)
        else:
            results = getattr(w, wmi_class)()
            self._extract_metrics(results, metrics, tag_by, instance)

    def _extract_metrics(self, results, metrics, tag_by, instance):
        if len(results) > 1 and tag_by is None:
            raise Exception(
                'WMI query returned multiple rows but no `tag_by` value was given. metrics=%s' %
                metrics)

        for wmi_property, name, mtype in metrics:
            for res in results:
                if wmi_property == UP_METRIC:
                    # Special-case metric will just submit 1 for every value
                    # returned in the result.
                    val = 1
                else:
                    val = float(getattr(res, wmi_property))

                # Grab the tag from the result if there's a `tag_by` value (e.g.: "name:jenkins")
                if tag_by:
                    dimensions = {'{0}'.format(tag_by.lower()): getattr(res, tag_by)}
                else:
                    dimensions = None

                try:
                    func = getattr(self, mtype)
                except AttributeError:
                    raise Exception('Invalid metric type: {0}'.format(mtype))

                # submit the metric
                func(name, val, dimensions=self._set_dimensions(dimensions, instance))
