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

from charms.layer.kafka_mirrormaker import kafka_mirrormaker

from charmhelpers.core import hookenv, unitdata

from charms.reactive import (when, when_not, hook,
                             remove_state, set_state)
from charms.reactive.helpers import data_changed


@hook('upgrade-charm')
def upgrade_charm():
    remove_state('kafka_mirrormaker.nrpe_helper.installed')
    remove_state('kafka_mirrormaker.started')


@when(
    'apt.installed.kafka',
)
@when_not('kafka_mirrormaker.started')
def configure_kafka_mirrormaker():
    hookenv.status_set('maintenance', 'setting up kafka mirrormaker')
    kafkamirrormaker = kafka_mirrormaker()
    kafkamirrormaker.start()
    set_state('kafka_mirrormaker.started')
    hookenv.status_set('active', 'ready')
    # set app version string for juju status output
    kafka_mirrormaker_version = kafkamirrormaker.version()
    hookenv.application_version_set(kafka_mirrormaker_version)


@when('config.changed', 'kafka_mirrormaker.ready')
def config_changed():
    for k, v in hookenv.config().items():
        if k.startswith('nagios') and data_changed('kafka_mirrormaker.config.{}'.format(k),
                                                   v):
            # Trigger a reconfig of nagios if relation established
            remove_state('kafka_mirrormaker.nrpe_helper.registered')
    # Something must have changed if this hook fired, trigger reconfig
    remove_state('kafka_mirrormaker.started')
