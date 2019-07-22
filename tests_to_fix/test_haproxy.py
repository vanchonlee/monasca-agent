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
import subprocess
import time
import tempfile
import os
import logging

from tests.common import load_check, kill_subprocess
from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest

from six.moves import urllib


logging.basicConfig()

MAX_WAIT = 30
HAPROXY_CFG = os.path.realpath(os.path.join(os.path.dirname(__file__), "haproxy.cfg"))
HAPROXY_OPEN_CFG = os.path.realpath(os.path.join(os.path.dirname(__file__), "haproxy-open.cfg"))


class HaproxyTestCase(unittest.TestCase):

    def _wait(self, url):
        loop = 0
        while True:
            try:
                STATS_URL = ";csv;norefresh"
                passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                passman.add_password(None, url, "datadog", "isdevops")
                authhandler = urllib.request.HTTPBasicAuthHandler(passman)
                opener = urllib.request.build_opener(authhandler)
                urllib.request.install_opener(opener)
                url = "%s%s" % (url, STATS_URL)
                req = urllib.request.Request(url)
                request = urllib.request.urlopen(req)
                break
            except Exception:
                time.sleep(0.5)
                loop += 1
                if loop >= MAX_WAIT:
                    break
        return request

    def setUp(self):
        self.process = None
        self.cfg = None

    def start_server(self, config_fn, config):
        self.agent_config = {
            'version': '0.1',
            'api_key': 'toto'
        }

        # Initialize the check from checks_d
        self.check = load_check('haproxy', config, self.agent_config)

        try:
            self.cfg = tempfile.NamedTemporaryFile()
            self.cfg.write(open(config_fn).read())
            self.cfg.flush()
            # Start haproxy
            self.process = subprocess.Popen(["haproxy", "-d", "-f", self.cfg.name],
                                            executable="haproxy",
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)

            # Wait for it to really start
            self._wait("http://localhost:3834/stats")
        except Exception:
            logging.getLogger().exception("Cannot instantiate haproxy")

    @attr('haproxy')
    def testCheck(self):
        raise SkipTest('Requires Haproxy')
        config = {
            'init_config': {},
            'instances': [{
                'url': 'http://localhost:3834/stats',
                'username': 'datadog',
                'password': 'isdevops',
                'status_check': True,
                'collect_aggregates_only': False,
            }]
        }
        self.start_server(HAPROXY_CFG, config)

        # Run the check against our running server
        self.check.check(config['instances'][0])
        # Sleep for 1 second so the rate interval >=1
        time.sleep(1)
        # Run the check again so we get the rates
        self.check.check(config['instances'][0])

        # Metric assertions
        metrics = self.check.get_metrics()
        assert metrics
        self.assertIsInstance(metrics, list)
        self.assertTrue(len(metrics) > 0)

        self.assertEqual(len([t for t in metrics
                              if t[0] == "haproxy.backend.bytes.in_rate"]), 4, metrics)
        self.assertEqual(len([t for t in metrics
                              if t[0] == "haproxy.frontend.session.current"]), 1, metrics)

        inst = config['instances'][0]
        data = self.check._fetch_data(inst['url'], inst['username'], inst['password'])
        new_data = [l.replace("OPEN", "DOWN") for l in data]
        self.check._process_data(new_data, False, True, inst['url']),

        assert self.check.has_events()
        assert len(self.check.get_events()) == 1

    @attr('haproxy')
    def testWrongConfig(self):
        # Same check, with wrong data
        config = {
            'init_config': {},
            'instances': [{
                'url': 'http://localhost:3834/stats',
                'username': 'wrong',
                'password': 'isdevops',
                'collect_aggregates_only': False,
            }]
        }
        self.start_server(HAPROXY_CFG, config)

        # Run the check, make sure there are no metrics or events
        try:
            self.check.check(config['instances'][0])
        except Exception:
            pass
        else:
            assert False, "Should raise an error"
        metrics = self.check.get_metrics()
        assert len(metrics) == 0
        assert self.check.has_events() is False

    @attr('haproxy')
    def testOpenConfig(self):
        raise SkipTest('Requires Haproxy')
        # No passwords this time
        config = {
            'init_config': {},
            'instances': [{
                'url': 'http://localhost:3834/stats',
                'collect_aggregates_only': False,
            }]
        }
        self.start_server(HAPROXY_OPEN_CFG, config)

        # Run the check against our running server
        self.check.check(config['instances'][0])
        # Sleep for 1 second so the rate interval >=1
        time.sleep(1)
        # Run the check again so we get the rates
        self.check.check(config['instances'][0])

        metrics = self.check.get_metrics()
        assert metrics
        self.assertIsInstance(metrics, list)
        self.assertTrue(len(metrics) > 0)

        self.assertEqual(len([t for t in metrics
                              if t[0] == "haproxy.backend.bytes.in_rate"]), 4, metrics)
        self.assertEqual(len([t for t in metrics
                              if t[0] == "haproxy.frontend.session.current"]), 1, metrics)

    def tearDown(self):
        if self.process is not None:
            kill_subprocess(self.process)
        del self.cfg

if __name__ == "__main__":
    unittest.main()
