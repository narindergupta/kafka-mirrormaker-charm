# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, signal
import re
import subprocess
import json
import shutil

from pathlib import Path
from base64 import b64encode, b64decode

from charmhelpers.core import hookenv, host
from charms.reactive.relations import RelationBase
from charmhelpers.core.templating import render

from charms import apt

KAFKAMIRROR_APP = 'kafka-mirror'
KAFKAMIRROR_SERVICE = '{}.service'.format(KAFKAMIRROR_APP)
KAFKAMIRROR_SERVICE_CONF = '/lib/systemd/system/'
KAFKA_APP = 'kafka'
KAFKA_SERVICE = '{}.service'.format(KAFKA_APP)
KAFKA_APP_DATA = '/etc/{}'.format(KAFKA_APP)
KAFKA_SERVICE_CONF = '/lib/systemd/system/'


class kafka_mirrormaker(object):
    def install(self):
        '''
        Nothing to install as kafka charm will installs all utility
        '''
        host.service_stop(KAFKA_SERVICE)

    def restart(self):
        '''
        Restarts the Kafka service.
        '''
        host.service_restart(KAFKAMIRROR_SERVICE)

    def start(self):
        '''
        Starts the Kafka mirror rervice.
        '''
        config = hookenv.config()
        streams = config["streams"]
        whitelist = config["whitelist"]
        producerconfig = b64decode(config['producer_config']).decode("utf-8")
        consumerconfig = b64decode(config['consumer_config']).decode("utf-8")
        producer_res_path = self._resource_get("producer.jks")
        if producer_res_path is False:
            producerjks = b64decode(config['producer_jks']).decode("utf-8")
            with open('/etc/kafka/producer_truststore.jks', 'w') as outfile:
                json.dump(producerjks, outfile)
        else:
            shutil.copy(producer_res_path, '/etc/kafka/producer_truststore.jks')

        consumer_res_path = self._resource_get("consumer.jks")
        if consumer_res_path is False:
            consumerjks = b64decode(config['consumer_jks']).decode("utf-8")
            with open('/etc/kafka/consumer_truststore.jks', 'w') as outfile:
                json.dump(consumerjks, outfile)
        else:
            shutil.copy(consumer_res_path, '/etc/kafka/consumer_truststore.jks')

        with open('/etc/kafka/producerconfig-file', 'w') as outfile:
            json.dump(producerconfig, outfile)
        with open('/etc/kafka/consumerconfig-file', 'w') as outfile:
            json.dump(consumerconfig, outfile)

        render(
            source='broker.env',
            target=os.path.join(KAFKA_APP_DATA, 'broker.env'),
            owner='root',
            perms=0o644,
            context={
                'kafka_heap_opts': config.get('kafka_heap_opts', ''),
            }
        )

        # mirror the topics if kafka is running
        try:
            process = subprocess.Popen([
                        '/usr/lib/kafka/bin/kafka-mirror-maker.sh',
                        '--producer.config', producerconfig,
                        '--consumer.config', consumerconfig,
                        '--num.streams', str(streams),
                        '--whitelist', str(whitelist)])
            mirrorpid = open("/etc/kafka/kafkamirror.pid","w")
            mirrorpid.write(str(process.pid))
            mirrorpid.close()
        except subprocess.CalledProcessError as e:
            hookenv.status_set('failed', 'kafka mirror failed to start')

        host.service_start(KAFKAMIRROR_SERVICE)

    def stop(self):
        '''
        Stops the Kafka service.

        '''
        if os.path.exists("/etc/kafka/kafkamirror.pid"):
            pidfile = open("/etc/kafka/kafkamirror.pid","r")
            mirrorpid = pidfile.readline()
            pidfile.close()
            os.kill(int(mirrorpid), signal.SIGKILL)
            os.remove("/etc/kafka/kafkamirror.pid")

        host.service_stop(KAFKAMIRROR_SERVICE)

    def is_running(self):
        '''
        Restarts the Kafka service.
        '''
        return host.service_running(KAFKAMIRROR_SERVICE)

    def version(self):
        '''
        Will attempt to get the version from the version fieldof the
        Kafka application.

        If there is a reader exception or a parser exception, unknown
        will be returned
        '''
        return apt.get_package_version(KAFKA_APP) or 'unknown'

    def _resource_get(self, snapname):
        '''Used to fetch the resource path of the given name.

        This wrapper obtains a resource path and adds an additional
        check to return False if the resource is zero length.
        '''
        res_path = hookenv.resource_get(snapname)
        if res_path and os.stat(res_path).st_size != 0:
            return res_path
        return False
