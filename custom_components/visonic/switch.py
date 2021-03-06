"""
Support for visonic partitions when used with a connection to a Visonic Alarm Panel.
Currently, there is only support for a single partition

  Initial setup by David Field

"""
import logging
import asyncio

from collections import defaultdict
from homeassistant.util import slugify
from homeassistant.helpers.entity import Entity
from homeassistant.components.switch import ( SwitchDevice, ENTITY_ID_FORMAT)
from homeassistant.const import (ATTR_ARMED, ATTR_BATTERY_LEVEL, ATTR_LAST_TRIP_TIME, ATTR_TRIPPED, 
     ATTR_CODE, STATE_STANDBY, STATE_ALARM_DISARMED, STATE_ALARM_ARMED_AWAY, STATE_ALARM_DISARMING, 
     STATE_ALARM_ARMED_NIGHT, STATE_ALARM_ARMED_HOME, STATE_ALARM_PENDING, STATE_ALARM_ARMING, STATE_ALARM_TRIGGERED)
from .const import DOMAIN, DOMAINCLIENT, VISONIC_UNIQUE_ID
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DEPENDENCIES = ['visonic']

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry( hass: HomeAssistant, entry: ConfigEntry, async_add_entities ) -> None:
    """Set up the Visonic Alarm Binary Sensors"""
    if DOMAIN in hass.data:
        client = hass.data[DOMAIN][DOMAINCLIENT][entry.unique_id]
        devices = [
            VisonicSwitch(hass, client, device)
            for device in hass.data[DOMAIN]['switch']   
        ]
        hass.data[DOMAIN]["switch"] = list()
        async_add_entities(devices, True)

class VisonicSwitch(SwitchDevice):
    """Representation of a Visonic X10 Switch."""

    def __init__(self, hass: HomeAssistant, client, visonic_device):
        """Initialise a Visonic X10 Device."""
        #_LOGGER.info("Creating X10 Switch {0}".format(visonic_device.name))
        self.client = client
        self.visonic_device = visonic_device
        self.x10id = self.visonic_device.id
        self._name = "Visonic " + self.visonic_device.name
        # Append device id to prevent name clashes in HA.
        self.visonic_id = slugify(self._name) # VISONIC_ID_FORMAT.format( slugify(self._name), visonic_device.getDeviceID())
        self.entity_id = ENTITY_ID_FORMAT.format(self.visonic_id)
        self.current_value = self.visonic_device.state
        self.visonic_device.install_change_handler(self.onChange)
    
    def onChange(self):
        self.current_value = self.visonic_device.state
        self.schedule_update_ha_state()

    @property
    def should_poll(self):
        """Get polling requirement from visonic device."""
        return False

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self.visonic_id

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def assumed_state(self):
        """Return true if unable to access real state of entity."""
        return False
        
    @property
    def is_on(self):
        """Return true if device is on."""
        return self.current_value

    def turn_on(self, **kwargs):
        """Turn the device on."""
        self.turnmeonandoff("on")
        
    def turn_off(self, **kwargs):
        """Turn the device off."""
        self.turnmeonandoff("off")

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            'manufacturer': 'Visonic',
            "identifiers": {(DOMAIN, self._name)},
            "name": f"Visonic X10 ({self.visonic_device.name})",
            "model": self.visonic_device.type,
            "via_device" : (DOMAIN, VISONIC_UNIQUE_ID),
            #"sw_version": self._api.information.version_string,
        }

    async def async_remove_entry(hass, entry) -> None:
        """Handle removal of an entry."""
        _LOGGER.info('switch async_remove_entry')

    # "off"  "on"  "dim"  "brighten"
    def turnmeonandoff(self, state):
        """Send disarm command."""
        #import custom_components.visonic.pyvisonic as visonicApi   # Connection to python Library
        self.client.setX10(self.x10id, state)

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        #_LOGGER.warning("in device_state_attributes")
        attr = {}

        attr["Location"] = self.visonic_device.location
        attr["Name"] = self.visonic_device.name
        attr["Type"] = self.visonic_device.type
        attr["Visonic Device"] = self.visonic_device.id
#        attr["State"] = "Yes" if self.visonic_device.state else "No"
        
        return attr
            

# class VisonicPartition(Entity):
    # """Representation of a Visonic Partition."""

    # def __init__(self, hass, partition):
        # """Initialise a Visonic device."""
        # self._name = "Visonic Alarm Partition"
        # self._address = "Visonic_Partition_" + str(partition)     # the only thing that is available on startup, eventually need to start all partitions
        # self.current_value = self._name

    # def doUpdate(self):    
        # self.schedule_update_ha_state(False)
        
    # @property
    # def should_poll(self):
        # """Get polling requirement from visonic device."""
        # return False # self.visonic_device.should_poll

    # @property
    # def unique_id(self) -> str:
        # """Return a unique ID."""
        # return self._address
        
    # @property
    # def name(self):
        # """Return the name of the device."""
        # return self._name

    # def getStatus(self, s : str):
        # if visonicApi is None:
            # return "Unknown"
        # return "Unknown" if s not in visonicApi.PanelStatus else visonicApi.PanelStatus[s]
        
    # @property
    # def device_info(self):
        # """Return information about the device."""
        # return {
            # 'manufacturer': 'Visonic',
            # 'name': self.getStatus("Panel Name"),
            # 'sw_version': self.getStatus("Panel Software"),
            # 'model': self.getStatus("Model"),
        # }

    # @property
    # def state(self):    
        # """Return the state of the device."""
        # #isArmed = visonicApi.PanelStatus["Panel Armed"]
        
        # armcode = visonicApi.PanelStatus["Panel Status Code"]
        # sirenActive = visonicApi.PanelStatus["Panel Siren Active"]
        
        # # -1  Not yet defined
        # # 0   Disarmed
        # # 1   Exit Delay Arm Home
        # # 2   Exit Delay Arm Away
        # # 3   Entry Delay
        # # 4   Armed Home
        # # 5   Armed Away
        # # 6   Special ("User Test", "Downloading", "Programming", "Installer")
        
        # #_LOGGER.warning("alarm armcode is " + str(armcode))
        
        # if sirenActive == 'Yes':
            # return STATE_ALARM_TRIGGERED
        # elif armcode == 0 or armcode == 6:
            # return STATE_ALARM_DISARMED
        # elif armcode == 1:
            # return STATE_ALARM_PENDING
        # elif armcode == 2:
            # return STATE_ALARM_ARMING
        # elif armcode == 3:
            # return STATE_ALARM_DISARMING
        # elif armcode == 4:
            # return STATE_ALARM_ARMED_HOME
        # elif armcode == 5:
            # return STATE_ALARM_ARMED_AWAY
        
        # return STATE_STANDBY

    # #def entity_picture(self):
    # #    return "/config/myimages/20160807_183340.jpg"
        
    # @property
    # def device_state_attributes(self):  #
        # """Return the state attributes of the device."""
        # # maybe should filter rather than sending them all
        # return None
        
    # @property
    # def state_attributes(self):  #
        # """Return the state attributes of the device."""
        # # maybe should filter rather than sending them all
        # return visonicApi.PanelStatus
