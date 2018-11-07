# -*- coding: utf-8 -*-

"""
Fetch a list of channels from TVHeadend
"""

import requests
import requests.auth
import socket

from typing import Dict, List, NamedTuple, Optional, Union


class Channel(NamedTuple):
  channel_id: str
  channel_name: str
  service_name: str


class TVHeadendClient(object):
  auth: Optional[Union[requests.auth.HTTPDigestAuth, requests.auth.HTTPBasicAuth]]
  # Base URL without final slash
  base_url: str

  def __init__(self, host: str, port: int = 9981,
               username: Optional[str] = None,
               password: Optional[str] = None, use_digest=True):
    if username and password:
      if use_digest:
        self.auth = requests.auth.HTTPDigestAuth(username, password)
      else:
        self.auth = requests.auth.HTTPBasicAuth(username, password)
    else:
      self.auth = None

    self.base_url = 'http://{:s}:{:d}'.format(host, port)

  def json(self, relative_path: str, params=None, method: str = 'get') -> object:
    url = "{}/{}".format(self.base_url, relative_path)
    r = requests.request(method, url, auth=self.auth, params=params)

    if r.status_code == 401:
      raise Exception('Not authorized - user may need admin acces')
    elif r.status_code != 200:
      raise Exception('Connection to TVHeadend failed HTTP {}'.format(
        r.status_code))

    return r.json()

  def get_channel_list(self):
    data = self.json('api/channel/list')

    if 'entries' not in data:
      raise Exception('Missing channels in response')
    return data['entries']

  def get_service_grid(self):
    data = self.json('api/mpegts/service/grid', params={'limit': 999})

    if 'entries' not in data:
      raise Exception('Missing channel grid')
    return data['entries']

  def get_channels(self) -> List[Channel]:
    channels = self.get_channel_list()
    services = self.get_service_grid()

    # Get channel key to name map
    channel_by_id: Dict[str, str] = {
      c['key']: c['val'] for c in channels
    }

    channels = []

    for service in services:
      # Look up channel for service
      for channel_id in service['channel']:
        ch = channel_by_id.get(channel_id, None)

        if ch:
          channels.append(Channel(channel_id, ch, service['svcname']))

    return channels


class TVHXMLTVSocket(object):
  def __init__(self, path):
    self.path = path
    self.sock = False
  def __enter__(self):
    return self
  def __exit__(self, type, value, traceback):
    if(self.sock):
      self.sock.close()
  def send(self, data):
    self.sock = socket.socket(socket.AF_UNIX)
    self.sock.connect(self.path)
    self.sock.sendall(data)
    self.sock.close()
