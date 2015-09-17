#!/usr/bin/env python
# -- Content-Encoding: UTF-8 --
"""
Runs an Herald MQTT framework

:author: Ahmad Shahwan
:copyright: Copyright 2015, isandlaTech
:license: Apache License 2.0
:version: 0.0.4
:status: Alpha

..

    Copyright 2015 isandlaTech

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

# Module version
__version_info__ = (0, 0, 4)
__version__ = ".".join(str(x) for x in __version_info__)

# Documentation strings format
__docformat__ = "restructuredtext en"

# ------------------------------------------------------------------------------

# Herald constants
import herald.transports.mqtt

# Pelix
from pelix.ipopo.constants import use_waiting_list
import pelix.framework

# Standard library
import argparse
import logging

# ------------------------------------------------------------------------------


def main(host, port, peer_name, node_name, app_id,
         username=None, password=None):
    """
    Runs an MQTT peer.

    :param host: Address of the MQTT server
    :param port: Port of the MQTT server
    :param peer_name: Name of the peer
    :param node_name: Name (also, UID) of the node hosting the peer
    :param app_id:
    :param username:
    :param password:
    :return:
    """
    # Create the framework
    framework = pelix.framework.create_framework(
        ('pelix.ipopo.core',
         'pelix.ipopo.waiting',
         'pelix.shell.core',
         'pelix.shell.ipopo',
         'pelix.shell.console',

         # Herald core
         'herald.core',
         'herald.directory',
         'herald.shell',

         # Herald MQTT
         'herald.transports.mqtt.directory',
         'herald.transports.mqtt.transport',

         # RPC
         'pelix.remote.dispatcher',
         'pelix.remote.registry',
         'herald.remote.discovery',
         'herald.remote.herald_xmlrpc',),
        {
            herald.FWPROP_NODE_UID: node_name,
            herald.FWPROP_NODE_NAME: node_name,
            herald.FWPROP_PEER_NAME: peer_name,
            herald.FWPROP_APPLICATION_ID: app_id,
            herald.transports.mqtt.PROP_MQTT_HOST: host,
            herald.transports.mqtt.PROP_MQTT_PORT: port,
            herald.transports.mqtt.PROP_MQTT_USERNAME: username,
            herald.transports.mqtt.PROP_MQTT_PASSWORD: password})
    #context = framework.get_bundle_context()

    # Start everything
    framework.start()

    # Instantiate components
    # with use_waiting_list(context) as ipopo:
    #     # ... MQTT Transport
    #     ipopo.add("herald-mqtt-transport-factory",
    #               "herald-mqtt-transport-example",
    #               {herald.transports.mqtt.PROP_MQTT_HOST: host,
    #                herald.transports.mqtt.PROP_MQTT_PORT: port,
    #                herald.transports.mqtt.PROP_MQTT_USERNAME: username,
    #                herald.transports.mqtt.PROP_MQTT_PASSWORD: password})

    # Start the framework and wait for it to stop
    framework.wait_for_stop()

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Pelix Herald demo")

    # MQTT server
    group = parser.add_argument_group("MQTT Configuration",
                                      "Configuration of the MQTT transport")
    group.add_argument("-s", "--server", action="store", default="localhost",
                       dest="server", help="Broker of the MQTT server")
    group.add_argument("-p", "--port", action="store", type=int, default=1883,
                       dest="port", help="Port of the MQTT server")

    # XMPP login
    group.add_argument("-u", "--user", action="store", default=None,
                       dest="username", help="Users' login")
    group.add_argument("--password", action="store", default=None,
                       dest="password", help="Password for authentication")
    group.add_argument("--ask-password", action="store_true", default=False,
                       dest="ask_password",
                       help="Ask password for authentication")

    # Peer info
    group = parser.add_argument_group("Peer Configuration",
                                      "Identity of the Peer")
    group.add_argument("-n", "--name", action="store", default=None,
                       dest="name", help="Peer name")
    group.add_argument("--node", action="store", default=None,
                       dest="node", help="Node name")
    group.add_argument("-a", "--app", action="store",
                       default=herald.DEFAULT_APPLICATION_ID,
                       dest="app_id", help="Application ID")

    # Parse arguments
    args = parser.parse_args()

    # Configure the logging package
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('herald').setLevel(logging.DEBUG)
    #logging.getLogger().addHandler(logging.StreamHandler())

    if args.username and args.ask_password:
        import getpass
        password = getpass.getpass("Password for {0}: ".format(args.xmpp_jid))
    else:
        password = args.password

    # Run the framework
    main(args.server, args.port, args.name, args.node, args.app_id,
         args.username, password)
