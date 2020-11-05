```
 _   _                           _            _     _              _   
| | | | ___  _ __ ___   ___     / \   ___ ___(_)___| |_ __ _ _ __ | |_ 
| |_| |/ _ \| '_ ` _ \ / _ \   / _ \ / __/ __| / __| __/ _` | '_ \| __|
|  _  | (_) | | | | | |  __/  / ___ \\__ \__ \ \__ \ || (_| | | | | |_ 
|_| |_|\___/|_| |_| |_|\___| /_/   \_\___/___/_|___/\__\__,_|_| |_|\__|
```
# Rob's Home Assistant Configuration
Welcome to my repository representing all Home Assistant configuration. I'm sharing this to help others, since many such other repositories helped me a lot.
Keeping this up to date is a continuous process, I discover daily new possibilities and face situations that ask for automation.

# Screenshots
Theme used in below screenshots is [iOS Dark Mode Theme](https://github.com/basnijholt/lovelace-ios-dark-mode-theme/)
> TODO more
![Main Dashboard](https://github.com/robsonke/hass-config/blob/master/www/screenshots/main-dashboard.jpg)

## Software
- Hassio with quite some add-ons
  - A better presence
  - AppDaemon 4
  - Check Home Assistant configuration
  - DOODS
  - Dnsmasq
  - Glances
  - Grafana
  - Home Assistant Google Drive Backup
  - InfluxDB
  - Log Viewer
  - MariaDB
  - Mosquitto broker
  - NGINX Home Assistant SSL proxy
  - Node-RED
  - OpenZWave
  - SSH & Web Terminal
  - Visual Studio Code
  - WireGuard
  - deCONZ
  - motionEye
  - phpMyAdmin

## Hardware
What drives all:
- Intel NUC10i3FNK with 16 GB memory running Proxmox VE
- Aeotec Gen 5 Z-Wave Plus USB Stick
- ConBee II Zigbee USB Stick
- Synology DS918+

### Devices
What controls and measures all.
Lights:
- Philips Hue Bulbs
- LimitlessLED spots
- 4x Osram Zigbee Led Strip (3m)

Switches:
- 3x Philips Hue Dimmer Switch
- Xiaomi Aqara Wireless Switch
- 2x Z-Wave FIBARO Dimmer 2
- 3x Z-Wave Everspring AD147 Plug-in Dimmer
- 3x TP-Link Wi-Fi Smart Plug HS110

Media:
- 4x Sonos One
- 2x Sonos Play5
- 1x Sonos Beam
- 1x Google Nest Hub
- 3x Google Nest Mini
- 2x Chromecast

Sensors:
- Z-Wave Fibaro Smoke Sensor 2
- Many Xiaomi Aqara Door/Window Sensors
- 2x Xiaomi Aqara Motion Sensor
- Xiaomi Aqara Vibration Sensor
- 5x Xiaomi Aqara Light Sensor
- 5x Xiaomi Aqara Temperature Sensor

Vacuum:
- iRobot Roomba 

Cameras
- 2x Foscam C2

Doorbell
- Ring Doorbell
- Ring Chime

Thermostat:
- Nest Thermostat

# Presence Detection
> TODO

# Motion & Object Detection
> TODO

# Main Todo
- Research if I should switch to [Frigate](https://github.com/blakeblackshear/frigate)
- Order a Coral Accelerator
- Implement adaptive lighting
- Implement garden irrigation system
- Implement smart door locks
- Implement floorplans
- Improve security system
- Separate IoT and other devices in differnet subnets
- Document automations

