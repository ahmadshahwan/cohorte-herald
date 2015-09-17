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

# Standard libraries
import logging
import time

# Pelix
from pelix.ipopo.decorators import ComponentFactory, Requires, Provides, \
    Property, Validate, Invalidate, Instantiate, RequiresBest
import pelix.utilities

# Herald
import herald
import herald.utils as utils
import herald.transports.mqtt.models as models
from herald.beans import Message
from herald.transports.peer_contact import PeerContact, \
    SUBJECT_DISCOVERY_PREFIX, SUBJECT_DISCOVERY_STEP_1
from herald.transports.mqtt import ACCESS_ID, PROP_MQTT_HOST, \
    PROP_MQTT_PASSWORD, PROP_MQTT_PORT, PROP_MQTT_USERNAME

# Documentation strings format
__docformat__ = "restructuredtext en"

__author__ = 'Ahmad Shahwan'

# Logging
_log = logging.getLogger(__name__)

DEFAULT_MQTT_HOST = 'localhost'
DEFAULT_MQTT_PORT = 1883


@ComponentFactory('herald-mqtt-transport-factory')
@RequiresBest('_probe', herald.SERVICE_PROBE)
@Requires('_directory', herald.SERVICE_DIRECTORY)
@Requires('_herald', herald.SERVICE_HERALD_INTERNAL)
@Provides(herald.SERVICE_TRANSPORT)
@Property('_access_id', herald.PROP_ACCESS_ID, ACCESS_ID)
@Property('_host', PROP_MQTT_HOST, DEFAULT_MQTT_HOST)
@Property('_port', PROP_MQTT_PORT, DEFAULT_MQTT_PORT)
@Property('_username', PROP_MQTT_USERNAME, None)
@Property('_password', PROP_MQTT_PASSWORD, None)
@Instantiate('herald-mqtt-transport')
class MqttTransport(object):
    """
    MQTT transport component for Herald.
    """
    def __init__(self):
        """
        Sets up the transport component.
        """
        # Properties
        # Herald core directory
        self._directory = None
        # Herald core service
        self._herald = None
        # Debug probe
        self._probe = None
        # Access ID
        self._access_id = ACCESS_ID
        # Host name
        self._host = None
        # Port number
        self._port = None
        # Username
        self._username = None
        # Password
        self._password = None

        # Local peer
        self.__peer = None
        # MQTT messenger
        self.__messenger = None
        # Peer contact
        self.__contact = None

    def __get_content(self,
                      message,
                      target_uid=None,
                      target_group=None,
                      parent_uid=None):
        """
        Prepares a message to be sent with relevant headers and content type.
        :param message: Message object
        :param target_peer: The target peer, if any
        :param target_group: The group name, if any
        :param parent_uid: Parent UID, if any
        :return: Content of the message to be sent, in JSON format
        ":rtype: str
        """
        # Convert content to JSON
        if message.subject in herald.SUBJECTS_RAW:
            return pelix.utilities.to_str(message.content)
        # Update headers
        message.add_header(herald.MESSAGE_HEADER_SENDER_UID,
                           self.__peer.uid)
        if target_uid is not None:
            message.add_header(herald.MESSAGE_HEADER_TARGET_PEER,
                               target_uid)
        if target_group is not None:
            message.add_header(herald.MESSAGE_HEADER_TARGET_GROUP,
                               target_group)
        if parent_uid:
            message.add_header(herald.MESSAGE_HEADER_REPLIES_TO,
                               parent_uid)
        return utils.to_json(message)

    def on_message(self, content):
        """
        Callback when message is received
        :param content: Message content, in JSON format as it was sent
        """
        message = utils.from_json(content)
        # :type message: herald.beans.MessageReceived
        sender_uid = message.get_header(herald.MESSAGE_HEADER_SENDER_UID)
        # Ignore loop-backs
        if sender_uid == self.__peer.uid:
            return
        reply_to = message.get_header(herald.MESSAGE_HEADER_REPLIES_TO)
        subject = message.subject

        extra = {
            "sender_uid": sender_uid,
            "parent_uid": message.uid
        }

        message.set_extra(extra)
        message.set_access(ACCESS_ID)

        # Log before giving message to Herald
        self._probe.store(herald.PROBE_CHANNEL_MSG_RECV, {
            "uid": message.uid,
            "timestamp": time.time(),
            "transport": ACCESS_ID,
            "subject": subject,
            "source": sender_uid,
            "repliesTo": reply_to or "",
            "transportSource": sender_uid})

        if subject.startswith(SUBJECT_DISCOVERY_PREFIX):
            # Handle discovery message
            self.__contact.herald_message(self._herald, message)
        else:
            try:
                # Is peer familiar?
                self._directory.get_peer(sender_uid)
            except KeyError:
                # Case when message by peer was sent to a group
                pass
            else:
                # All other messages are given to Herald Core
                self._herald.handle_message(message)

    def on_connected(self, *args, **kwargs):
        """
        Add new access on connection
        :return:
        """
        self.__peer.set_access(ACCESS_ID, models.Access())
        message = Message(SUBJECT_DISCOVERY_STEP_1, self.__peer.dump())
        self.fire_group("all", None, message)

    def on_disconnected(self, *args, **kwargs):
        pass

    @Validate
    def _validate(self, _):
        """
        Component validated
        """
        _log.debug("MQTT transport validated.")
        self.__peer = self._directory.get_local_peer()
        self.__messenger = models.Messenger(self.__peer)
        self.__messenger.set_callback_listener(self)
        # Prepare the peer contact handler
        self.__contact = PeerContact(
            self._directory,
            None,
            __name__ + ".contact")
        if self._username is not None:
            self.__messenger.login(self._username, self._password)
        self.__messenger.connect(self._host, self._port)

    @Invalidate
    def _invalidate(self, _):
        """
        Component invalidated
        """
        _log.debug("MQTT transport invalidated.")
        self.__messenger.disconnect()
        self.__peer.unset_access(ACCESS_ID)
        self.__peer = None

    def fire(self, peer, message, extra=None):
        """
        Fires a message to a peer

        :param peer: A Peer object
        :param message: The message to send
        :param extra: Extra information used in case of a reply
        :raise InvalidPeerAccess: No information found to access the peer
        :type peer: herald.beans.Peer
        """
        peer_uid = peer.uid if peer else extra.get("sender_uid")
        parent_uid = extra.get("parent_uid") if extra else None

        _log.debug("Firing message to peer %s.", peer_uid)
        content = self.__get_content(message,
                                     target_uid=peer_uid,
                                     parent_uid=parent_uid)
        # Log before sending
        self._probe.store(herald.PROBE_CHANNEL_MSG_SEND, {
            "uid": message.uid,
            "timestamp": time.time(),
            "transport": ACCESS_ID,
            "subject": message.subject,
            "target": peer_uid
        })

        self._probe.store(herald.PROBE_CHANNEL_MSG_CONTENT, {
            "uid": message.uid,
            "content": content
        })

        self.__messenger.fire(peer_uid, content)

    def fire_group(self, group, peers, message):
        """
        Fires a message to a group of peers

        :param group: Name of a group
        :param peers: Peers to communicate with
        :param message: Message to send
        :return: The list of reached peers

        """
        _log.debug("Firing message to group %s.", group)
        # Prepare the message
        content = self.__get_content(message, target_group=group)

        self.__messenger.fire_group(group, content)
        return peers
