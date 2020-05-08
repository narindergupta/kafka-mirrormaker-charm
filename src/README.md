# kafka-charm

Kafka's mirroring feature makes it possible to maintain a replica of an
existing Kafka cluster. The following diagram shows how to use the MirrorMaker
tool to mirror a source Kafka cluster into a target (mirror) Kafka cluster.
The tool uses a Kafka consumer to consume messages from the source cluster,
and re-publishes those messages to the local (target) cluster using an
embedded Kafka producer.

# Building

    cd src
    charm build

Will build the Kafka charm, and then the charm in `/tmp/charm-builds`.

# Operating

This charm require the private ppa configuration.

    juju deploy cs:~narindergupta/kafka-mirrormaker

# Notes

The Kafka charm requires at least 4GB of memory.

# Details

Much of the charm implementation is borrowed from the Apache kafka
charm, but it's been heavily simplified and pared down. Jinja templating is
used instead of Puppet, and a few helper functions that were imported from
libraries are inlined.
