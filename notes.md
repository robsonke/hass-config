# TODOs
* add alerts / automations on battery levels
* put room info (climate/doors) in a picture element in the main view
* add a picture element card inside the groundfloor view with the details of climate/doors
* https://github.com/blakeblackshear/frigate-hass-integration
* grafana dashboard (add glances entitities: https://home.tigrou.nl/config/entities?historyBack=1&config_entry=3f315d8b0bd411eb81808560d7a0e4f2)
* search for TODO in yaml files
* investigate options notifications in ios app (https://companion.home-assistant.io/docs/notifications/notifications-basic) - https://www.youtube.com/watch?v=I1xBnz5ibjY
* nuki / yale / danalock (check if cilinder allows 2 side keys)
* thermostat / heatpump BRP069A62 (https://www.daikin.nl/nl_nl/products/BRC1HHDW.html)
* garden irrigation system
* cctv solutions (shinobi, integration frigate, etc)
* detect license plates https://github.com/openalpr/openalpr
* weather station (https://github.com/tomvanswam/compass-card)
* floorplan langeweide (https://www.juanmtech.com/set-up-the-picture-elements-card-in-home-assistant/) https://github.com/pkozul/lovelace-floorplan/tree/master/www/floorplan/examples/simple https://github.com/pkozul/ha-floorplan
* implement todo list for garden stuff, sjorsje bin, etc
* sonos speaker grouping
* curtains: https://nl.slide.store
* why so red/orange: http://192.168.0.25:1400/support/review
* make automations smarter/shorter/less with templating
* visualise costs of heavy ops (https://www.reddit.com/r/homeassistant/comments/ixnr5z/creating_useful_notifications_using_the_new/)
* wall display (https://mbmounts.com/)
* adaptive lights: https://github.com/basnijholt/home-assistant-config/blob/a76ec6ffa435d09955be94b5c7822ad86bd84558/includes/adaptive_lighting.yaml#L10-L108 / https://www.reddit.com/r/homeassistant/comments/j09219/any_circadian_lighting_users_good_news_i_just/ / https://github.com/home-assistant/core/pull/40626

# Ideas and other links that I should keep
* https://github.com/eximo84/homeassistant-config-v2
* https://github.com/nervetattoo/simple-thermostat
* https://github.com/DBuit?tab=repositories
* https://github.com/awahlig/homebridge-casambi
* https://github.com/bachya/smart-home / https://github.com/stanvx/Home-Assistant-Configuration / https://github.com/DubhAd/Home-AssistantConfig / https://github.com/skalavala/mysmarthome / https://github.com/basnijholt/home-assistant-config / https://github.com/pqpxo/SWAKES_hassio
* https://www.rainmachine.com/products/rainmachine-touch-hd.html
* https://www.solaredge.com/nl/mysolaredge
* https://www.reddit.com/r/homeassistant/comments/ioddq9/progress_so_far_on_wall_mounted_ipad_dashboard/
* laundry/dishes progress (see also basnijholt): https://github.com/ShunichiSan/HomeAssistantApplianceCard/blob/master/AppliancesCard.yaml / https://www.reddit.com/r/homeassistant/comments/iyznyx/my_appliances_card_shows_appliance_status_time/
* https://github.com/thomasloven/hass-browser_mod/wiki/Cookbook

# Frigate info on Proxmox
* https://jackcuthbert.dev/blog/intel-nuc-gpu-passthrough-in-proxmox-plex-docker/
* https://pve.proxmox.com/wiki/Pci_passthrough#Enable_the_IOMMU
* now hitting a driver issue in the container (https://community.home-assistant.io/t/local-realtime-person-detection-for-rtsp-cameras/103107/2359)

# ZWave remove failed/dead node
* publish { "node": 5 } to OpenZWave/1/command/hasnodefailed/ (where 5 is node id)
* publish { "node": 5 } to OpenZWave/1/command/removefailednode/ (where 5 is node id)

# Info presence detection
Based on https://github.com/andrewjfreyer/monitor with Pi Zeros, 

Specific install steps for monitor.sh:
* follow install procedure from Monitor for pi zero
* set wifi country to NL with raspi-config
* disable power save, add in /etc/rc.local: iwconfig wlan0 power off (check after reboot with: dmesg | grep brcm)
* copy the config from another pi zero
* run once to store the settings for the service: sudo bash monitor.sh -a -u
* simple zsh setup: https://www.uberbuilder.com/oh-my-zsh-on-raspberry-pi/

In case the "better presence detection" addon is not supported anymore, consider:
https://github.com/arsaboo/homeassistant-config/blob/master/python_scripts/meta_device_tracker.py
combined with a Bayesian sensor

## HCI Permissions
Not required but easier.
```
sudo setcap cap_net_raw+eip $(eval readlink -f `which hcitool`)
sudo setcap cap_net_admin+eip $(eval readlink -f `which hciconfig`)
```

## Test a scan
```
hcitool -i hci0 info f6:74:ed:11:5d:24
hcitool -i hci0 info c2:6e:8b:2a:07:96
```

## Make journals persistent
```
sudo mkdir -p /var/log/journal
sudo systemd-tmpfiles --create --prefix /var/log/journal
sudo journalctl --vacuum-time=10d
```

## Upgrade OS on Pi Zeros
```
sudo apt-get update && sudo apt-get upgrade
# keep in mind that if bluetooth/bluez is upgraded, the hciconfig/tool permissions need to be set again
```