#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Herald transport implementations package

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

# Documentation strings format
__docformat__ = "restructuredtext en"

__author__ = 'Ahmad Shahwan'

# Herald MQTT Transport
from . import ACCESS_ID, TOPIC_PREFIX

# Pelix
#from pelix.misc.mqtt_client import MqttClient

# Paho MQTT client
from paho.mqtt.client import Client as MqttClient

import logging

UID_TOPIC = 'uid'
"""
UID subtopic
"""

GROUP_TOPIC = 'group'
"""
Group subtopic
"""

_log = logging.getLogger(__name__)


class Access(object):
    """
    Access object used by the MQTT implementation of Herald transport
    """
    def __init__(self):
        pass

    def __hash__(self):
        """
        Hash is based on client ID
        """
        return hash(None)

    def __eq__(self, other):
        return False

    def __lt__(self, other):
        return False

    def __str__(self):
        return "MQTT Access"

    @property
    def access_id(self):
        return ACCESS_ID

    def dump(self):
        """
        Returns the content to store in a directory dump to describe this
        access
        """
        return True


class Messenger(object):
    """
    MQTT client for Herald transport.
    """

    def __init__(self, peer):
        """
        Initialize client
        :param peer: The peer behind the MQTT client.
        :return:
        """
        self.__peer = peer
        self.__mqtt = MqttClient()
        self.__mqtt.on_connect = self._on_connect
        self.__mqtt.on_disconnect = self._on_disconnect
        self.__mqtt.on_message = self._on_message
        self.__callback_handler = None

    def __make_uid_topic(self, subtopic):
        """
        Constructs a complete UID topic.
        :param subtopic: The UID
        :return: Fully qualified topic
        :rtype : str
        """
        return TOPIC_PREFIX + '\\' + self.__peer.app_id + '\\'\
            + UID_TOPIC + '\\' + subtopic

    def __make_group_topic(self, subtopic):
        """
        Constructs a complete group topic.
        :param subtopic: The group name
        :return: Fully qualified topic
        :rtype : str
        """
        return TOPIC_PREFIX + '\\' + self.__peer.app_id + '\\'\
            + GROUP_TOPIC + '\\' + subtopic

    def _on_connect(self, *args, **kwargs):
        _log.info("Connection established.")
        _log.debug("Subscribing for topic %s." %
                       self.__make_uid_topic(self.__peer.uid))
        self.__mqtt.subscribe(self.__make_uid_topic(self.__peer.uid))
        self.__mqtt.subscribe(self.__make_group_topic("all"))
        for group in self.__peer.groups:
            _log.debug("Subscribing for topic %s." %
                       self.__make_group_topic(group))
            self.__mqtt.subscribe(self.__make_group_topic(group))
        if self.__callback_handler and self.__callback_handler.on_connected:
            self.__callback_handler.on_connected()
        else:
            _log.warning("Missing callback for on_connect.")

    def _on_disconnect(self, *args, **kwargs):
        _log.info("Connection lost.")
        if self.__callback_handler and self.__callback_handler.on_disconnected:
            self.__callback_handler.on_disconnected()

    def _on_message(self, client, data, message):
        _log.info("Message received.")
        if self.__callback_handler and self.__callback_handler.on_message:
            self.__callback_handler.on_message(message)
        else:
            _log.warning("Missing callback for on_message.")

    def fire(self, peer_uid, message):
        """
        Sends a message to another peer.
        :param peer_uid: Peer UID
        :param message: Message content
        :return:
        """
        self.__mqtt.publish(
            self.__make_uid_topic(peer_uid),
            message,
            1
        )

    def fire_group(self, group, message):
        """
        Sends a message to a group of peers.
        :param group: Group's name
        :param message: Message content
        :return:
        """
        self.__mqtt.publish(
            self.__make_group_topic(group),
            message,
            1
        )

    def set_callback_listener(self, listener):
        """
        Sets callback listener.
        :param listener: the listener
        :return:
        """
        self.__callback_handler = listener

    def connect(self, host, port):
        _log.info("Connecting to MQTT server %s:%s ..." % (host, port))
        self.__mqtt.connect(host, port)
        self.__mqtt.loop_start()

    def disconnect(self):
        _log.info("Disconnecting from MQTT server...")
        self.__mqtt.loop_stop()
        self.__mqtt.disconnect()



