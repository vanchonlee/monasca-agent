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

import monasca_setup.detection


class Ceilometer(monasca_setup.detection.ServicePlugin):

    """Detect Ceilometer daemons and setup configuration to monitor them."""

    def __init__(self, template_dir, overwrite=True, args=None):
        service_params = {
            'args': args,
            'template_dir': template_dir,
            'overwrite': overwrite,
            'service_name': 'telemetry',
            'process_names': ['ceilometer-agent-compute', 'ceilometer-agent-central',
                              'ceilometer-agent-notification', 'ceilometer-collector',
                              'ceilometer-alarm-notifier', 'ceilometer-alarm-evaluator',
                              'ceilometer-api'],
            # TO DO: Update once the health check is implemented in Ceilometer
            # 'service_api_url': 'http://localhost:8777/v2/health',
            # 'search_pattern' : '.*200 OK.*',
            'service_api_url': '',
            'search_pattern': ''
        }

        super(Ceilometer, self).__init__(service_params)
