# -*- coding: utf-8 -*-
#!/usr/bin/env python

from sys import argv

from os.path import exists, expanduser

from uuid import uuid4

import pyudev
import requests

from logging import getLogger
from logging.config import dictConfig

dict_config = {
  "version": 1,
  "formatters": {
    "standard": {
      "format": "%(asctime)s %(levelname)s %(module)s %(message)s"
    }
  },
  "handlers": {
    "console": {
      "level": "DEBUG",
      "class": "logging.StreamHandler",
      "formatter": "standard"
    }
  },
  "loggers": {
    "": {
      "handlers": ["console"],
      "level": "DEBUG",
    }
  }
}

dictConfig(dict_config)

log = getLogger(__name__)

def read_uuid(path):
  if exists(path):
    with open(path, "r") as f:
      uuid = f.read()
  else:
    uuid = uuid4().hex
    with open(path, "w") as f:
      f.write(uuid)

  return uuid

def get_usb_stick_info(dev):
  return {
    "vendor": {"id": dev["ID_VENDOR_ID"], "name": dev["ID_VENDOR"]}, 
    "product": {"id": dev["ID_MODEL_ID"], "name": dev["ID_MODEL"], "serial": dev.get("ID_SERIAL_SHORT", "ID_SERIAL")}}

def sneak(url, uuid_path):
  uuid = read_uuid(uuid_path)
  log.info("Watching {} for {}".format(uuid, url))
  context = pyudev.Context()
  mon = pyudev.Monitor.from_netlink(context)
  mon.filter_by(subsystem = "block")

  for action, dev in mon:
    if "ID_BUS" in dev and dev["ID_BUS"] == "usb" and dev["DEVTYPE"] == "disk":
      info = get_usb_stick_info(dev)
      if action == "add":
        log.info("Adds: {}".format(info))
        requests.get("{}/plug/{}/{}/{}/{}".format(url, info["product"]["serial"], uuid, info["vendor"]["name"], info["product"]["name"]))
      elif action == "remove":
        log.info("Removes: {}".format(info))
        requests.get("{}/unplug/{}/{}".format(url, info["product"]["serial"], uuid))

if __name__ == "__main__":
  url = argv[1] if len(argv) > 1 else "http://localhost:5000"
  sneak(url, "{}/.eReuseUUID".format(expanduser("~")))

