# TODOs
* put room info (climate/doors) in a picture element in the main view
* eufy doorbell (https://github.com/matijse/eufy-ha-mqtt-bridge) Does not integrate well
* https://github.com/blakeblackshear/frigate-hass-integration
* grafana dashboard (add glances entitities: https://home.tigrou.nl/config/entities?historyBack=1&config_entry=3f315d8b0bd411eb81808560d7a0e4f2)
* search for TODO in yaml files
* investigate options notifications in ios app (https://companion.home-assistant.io/docs/notifications/notifications-basic) - https://www.youtube.com/watch?v=I1xBnz5ibjY
* thermostat / heatpump BRP069A62 (https://www.daikin.nl/nl_nl/products/BRC1HHDW.html)
* garden irrigation system
* garden lights
* detect license plates https://github.com/openalpr/openalpr
* weather station (https://github.com/tomvanswam/compass-card)
* floorplan langeweide (https://www.juanmtech.com/set-up-the-picture-elements-card-in-home-assistant/) https://github.com/pkozul/lovelace-floorplan/tree/master/www/floorplan/examples/simple https://github.com/pkozul/ha-floorplan
* implement todo list for garden stuff, sjorsje bin, etc
* sonos speaker grouping
* curtains: https://nl.slide.store
* why so red/orange: http://192.168.0.25:1400/support/review
* visualise costs of heavy ops (https://www.reddit.com/r/homeassistant/comments/ixnr5z/creating_useful_notifications_using_the_new/)
* adaptive lights: https://github.com/home-assistant/core/pull/40626

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

