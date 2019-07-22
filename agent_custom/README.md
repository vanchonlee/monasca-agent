# haproxy_custom
use sock

```shell
vi /usr/lib/monasca/agent/custom_checks.d/haproxy.py
cat >> /etc/monasca/agent/conf.d/haproxy.yaml << eof
init_config:
    key1: value1
    key2: value2

instances:
    - name: john_smith
      username: john_smith
      password: 123456
    - name: jane_smith
      username: jane_smith
      password: 789012
eof
```

> pip install haproxyadmin