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

import unittest
import logging

logger = logging.getLogger(__file__)

from tests.common import get_check
from nose.plugins.skip import SkipTest


class TestWeb(unittest.TestCase):

    def setUp(self):
        self.apache_config = """
init_config:

instances:
    -   apache_status_url: http://localhost:9444/server-status
        dimensions:
            instance:first
    -   apache_status_url: http://localhost:9444/server-status?auto
        dimensions:
            instance:second
"""

        self.nginx_config = """
init_config:

instances:
    -   nginx_status_url: http://localhost:44441/nginx_status/
    -   nginx_status_url: http://localhost:44441/nginx_status/
        dimensions:
            test:first_one
    -   nginx_status_url: http://dummyurl:44441/nginx_status/
        dimensions:
            test1:dummy
    -   nginx_status_url: http://localhost:44441/nginx_status/
        dimensions:
            test2:second
"""

        self.lighttpd_config = """
init_config:

instances:
    -   lighttpd_status_url: http://localhost:9449/server-status
        dimensions:
            instance:first
    -   lighttpd_status_url: http://localhost:9449/server-status?auto
        dimensions:
            instance:second
"""

    def testApache(self):
        raise SkipTest("Requires running apache")
        a, instances = get_check('apache', self.apache_config)

        a.check(instances[0])
        metrics = a.get_metrics()
        self.assertEqual(metrics[0][3].get('dimensions'), {'instance': 'first'})

        a.check(instances[1])
        metrics = a.get_metrics()
        self.assertEqual(metrics[0][3].get('dimensions'), {'instance': 'second'})

    def testApacheOldConfig(self):
        a, _ = get_check('apache', self.apache_config)
        config = {
            'apache_status_url': 'http://example.com/server-status?auto'
        }
        instances = a.parse_agent_config(config)['instances']
        assert instances[0]['apache_status_url'] == config['apache_status_url']

    def testNginx(self):
        raise SkipTest("Requires running Lighthttpd")
        nginx, instances = get_check('nginx', self.nginx_config)
        nginx.check(instances[0])
        r = nginx.get_metrics()
        self.assertEqual(len([t for t in r if t[0] == "nginx.net.connections"]), 1, r)

        nginx.check(instances[1])
        r = nginx.get_metrics()
        self.assertEqual(r[0][3].get('dimensions'), {'test': 'first_one'})

    def testNginxOldConfig(self):
        nginx, _ = get_check('nginx', self.nginx_config)
        config = {
            'nginx_status_url_1': 'http://www.example.com/nginx_status:first_tag',
            'nginx_status_url_2': 'http://www.example2.com/nginx_status:8080:second_tag',
            'nginx_status_url_3': 'http://www.example3.com/nginx_status:third_tag'
        }
        instances = nginx.parse_agent_config(config)['instances']
        self.assertEqual(len(instances), 3)
        for i, instance in enumerate(instances):
            assert ':'.join(config.values()[i].split(':')[:-1]) == instance['nginx_status_url']

    def testLighttpd(self):
        raise SkipTest("Requires running Lighthttpd")
        l, instances = get_check('lighttpd', self.lighttpd_config)

        l.check(instances[0])
        metrics = l.get_metrics()
        self.assertEqual(metrics[0][3].get('dimensions'), {'instance': 'first'})

        l.check(instances[1])
        metrics = l.get_metrics()
        self.assertEqual(metrics[0][3].get('dimensions'), {'instance': 'second'})


if __name__ == '__main__':
    unittest.main()
