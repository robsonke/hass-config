

from ..global_variables     import GlobalVariables as Gb
from ..const                import (NOTIFY, EVLOG_NOTICE, NEXT_UPDATE,
                                    CRLF_DOT, CRLF, NBSP6,RED_X, YELLOW_ALERT, )
from ..helpers.common       import (instr, list_add, )
from ..helpers.messaging    import (post_event, post_error_msg, post_evlog_greenbar_msg,
                                    log_info_msg, log_exception, log_rawdata, _trace, _traceha, )
from ..helpers.time_util    import (secs_to_time, secs_since, mins_since, secs_to_time, format_time_age,
                                    format_timer, time_now_secs)
from homeassistant.helpers  import entity_registry as er, device_registry as dr

import json
# from homeassistant.components import ios
# from homeassistant.components.ios import notify
from homeassistant.util             import slugify
from homeassistant.components.mobile_app import notify as mobile_app_notify
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_TITLE,
    ATTR_TITLE_DEFAULT,
)
PUSH_URL = "https://ios-push.home-assistant.io/push"
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Cycle through HA entity registry and get mobile_app device info that
#   can be monitored for the config_flow mobapp device selection list and
#   setting up the Device object
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def get_entity_registry_mobile_app_devices():
    mobapp_id_by_mobapp_devicename      = {}
    mobapp_devicename_by_mobapp_id      = {}
    device_info_by_mobapp_devicename    = {}
    device_model_info_by_mobapp_devicename = {} # [raw_model, model, model_display_name]
                                                # ['iPhone15,2', 'iPhone', 'iPhone 14 Pro']
    last_updt_trig_by_mobapp_devicename = {}
    mobile_app_notify_devicename           = []
    battery_level_sensors_by_mobapp_devicename = {}
    battery_state_sensors_by_mobapp_devicename = {}

    device_registry = dr.async_get(Gb.hass)

    try:
        with open(Gb.entity_registry_file, 'r') as f:
            entity_reg_data   = json.load(f)
            mobile_app_entities = [x for x in entity_reg_data['data']['entities']
                                        if x['platform'] == 'mobile_app']
            dev_trkr_entities = [x for x in mobile_app_entities
                                    if x['entity_id'].startswith('device_tracker')]

            for dev_trkr_entity in dev_trkr_entities:
                if 'device_id' not in dev_trkr_entity: continue

                mobapp_devicename = dev_trkr_entity['entity_id'].replace('device_tracker.', '')
                dup_cnt = 1
                while mobapp_devicename in mobapp_id_by_mobapp_devicename:
                    dup_cnt += 1
                    mobapp_devicename = f"{mobapp_devicename} ({dup_cnt})"
                if dup_cnt > 1:
                    alert_msg = (f"Duplicate Mobile App devices in Entity Registry for "
                                f"{dev_trkr_entity['entity_id']}")
                    post_evlog_greenbar_msg(alert_msg)

                log_title = (f"MobApp entity_registry entry - <{mobapp_devicename}>)")
                log_rawdata(log_title, dev_trkr_entity, log_rawdata_flag=True)

                raw_model = 'Unknown'
                device_id = dev_trkr_entity['device_id']
                try:
                    # Get raw_model from HA device_registry
                    device_reg_data = device_registry.async_get(device_id)

                    log_title = (f"MobApp device_registry entry - <{mobapp_devicename}>)")
                    log_rawdata(log_title, str(device_reg_data), log_rawdata_flag=True)

                    raw_model = device_reg_data.model

                except Exception as err:
                    log_exception(err)
                    pass

                mobapp_id_by_mobapp_devicename[mobapp_devicename]            = dev_trkr_entity['device_id']
                mobapp_devicename_by_mobapp_id[dev_trkr_entity['device_id']] = mobapp_devicename

                mobapp_fname = dev_trkr_entity['name'] or dev_trkr_entity['original_name']
                device_info_by_mobapp_devicename[mobapp_devicename]       = f"{mobapp_fname} ({raw_model})"
                device_model_info_by_mobapp_devicename[mobapp_devicename] = [raw_model,'','']    # iPhone15,2;iPhone;iPhone 14 Pro

        last_updt_trigger_sensors = _extract_mobile_app_entities(mobile_app_entities, '_last_update_trigger')
        battery_level_sensors     = _extract_mobile_app_entities(mobile_app_entities, '_battery_level')
        battery_state_sensors     = _extract_mobile_app_entities(mobile_app_entities, '_battery_state')

        last_updt_trig_by_mobapp_devicename = _extract_sensor_entities(
                                    mobapp_devicename_by_mobapp_id, last_updt_trigger_sensors)
        battery_level_sensors_by_mobapp_devicename = _extract_sensor_entities(
                                    mobapp_devicename_by_mobapp_id, battery_level_sensors)
        battery_state_sensors_by_mobapp_devicename = _extract_sensor_entities(
                                    mobapp_devicename_by_mobapp_id, battery_state_sensors)

        Gb.debug_log['_.mobapp_id_by_mobapp_devicename'] = {k: v[:10] for k, v in mobapp_id_by_mobapp_devicename.items()}
        Gb.debug_log['_.mobapp_devicename_by_mobapp_id'] = {k[:10]: v for k, v in mobapp_devicename_by_mobapp_id.items()}
        Gb.debug_log['_.last_updt_trig_by_mobapp_devicename'] = last_updt_trig_by_mobapp_devicename
        Gb.debug_log['_.battery_level_sensors_by_mobapp_devicename'] = battery_level_sensors_by_mobapp_devicename
        Gb.debug_log['_.battery_state_sensors_by_mobapp_devicename'] = battery_state_sensors_by_mobapp_devicename

    except Exception as err:
        log_exception(err)

    return [mobapp_id_by_mobapp_devicename,
            mobapp_devicename_by_mobapp_id,
            device_info_by_mobapp_devicename,
            device_model_info_by_mobapp_devicename,
            last_updt_trig_by_mobapp_devicename,
            mobile_app_notify_devicename,
            battery_level_sensors_by_mobapp_devicename,
            battery_state_sensors_by_mobapp_devicename]

#-----------------------------------------------------------------------------------------------------
def _extract_mobile_app_entities(mobile_app_entities, entity_name):
    '''
    Extract mobile_app entities fields (dictionary) for the specific type
    of entity (_last_update_trigger, _battery_state

    Return - A list of the mobile_app entities
    '''
    return [x   for x in mobile_app_entities
                if instr(x['unique_id'], entity_name)]

#-----------------------------------------------------------------------------------------------------
def _extract_sensor_entities(mobapp_id_by_mobapp_devicename, sensor_entities):
    '''
    Match the mobile_app sensors entities with the devices they belong to.
    Example: {'gary_iphone_app': 'gary_iphone_app_last_update_trigger',
                'gary_ipad_2': 'gary_ipad_last_update_trigger'}}

    Return - A dictionary of the sensor entity for the specific mobapp device

    Return - A list of the mobile_app entities
    '''
    return  {mobapp_id_by_mobapp_devicename[sensor['device_id']]: _entity_name_disabled_by(sensor)
                                                    for sensor in sensor_entities
                                                    if sensor['device_id'] in mobapp_id_by_mobapp_devicename}

#-----------------------------------------------------------------------------------------------------
def _entity_name(entity_id):
    return entity_id.replace('sensor.', '')

def x_entity_name_disabled_by(sensor):
    disabled_prefix = ''   if sensor['disabled_by'] is None \
                             else f"{RED_X}DISABLED SENSOR{CRLF}{NBSP6}{NBSP6}{NBSP6}"

    return f"{disabled_prefix}{sensor['entity_id'].replace('sensor.', '')}"

def _entity_name_disabled_by(sensor):
    if sensor['disabled_by']:
        Gb.mobapp_fnames_disabled = list_add(Gb.mobapp_fnames_disabled, sensor['device_id'])

    return sensor['entity_id'].replace('sensor.', '')

#-----------------------------------------------------------------------------------------------------
def get_mobile_app_notify_devicenames():
    '''
    Get the mobile_app_[devicename] notify services entries from ha that are used to
    send notifications to a device.
    '''

    mobile_app_notify_devicenames = []
    try:
        notify_targets = mobile_app_notify.push_registrations(Gb.hass)
        for notify_target in notify_targets:
            mobile_app_notify_devicenames.append(f"mobile_app_{slugify(notify_target)}")

        return mobile_app_notify_devicenames

    except Exception as err:
        log_info_msg("Mobile App Notify Service has not been set up yet. iCloud3 will retry later.")
        # log_exception(err)
        pass

    return mobile_app_notify_devicenames

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Send a message to the mobapp
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def send_message_to_device(Device, service_data):
    '''
    Send a message to the device. An example message is:
        service_data = {
            "title": "iCloud3/MobApp Zone Action Needed",
            "message": "The iCloud3 Stationary Zone may "\
                "not be loaded in the MobApp. Force close "\
                "the MobApp from the Mobile App Switcher. "\
                "Then restart the MobApp to reload the HA zones. "\
                f"Distance-{dist_fm_zone_m} m, "
                f"StatZoneTestDist-{zone_radius * 2} m",
            "data": {"subtitle": "Stationary Zone Exit "\
                "Trigger was not received"}}
    '''
    try:
        if Device.mobapp[NOTIFY] == '':
            return

        if service_data.get('message') != "request_location_update":
            post_event(Device,
                        f"{EVLOG_NOTICE}Sending Message to Device > "
                        f"Message-{service_data.get('message')}")

        Gb.hass.services.call("notify", Device.mobapp[NOTIFY], service_data)

        return True

    except Exception as err:
        log_exception(err)
        event_msg =(f"iCloud3 Error > An error occurred sending a message to device "
                    f"{Device.mobapp[NOTIFY]} via the Notify service. "
                    f"{CRLF_DOT}Message-{str(service_data)}")
        if instr(err, "notify/none"):
            event_msg += (f"{CRLF_DOT}The devicename can not be found")
        else:
            event_msg += f"{CRLF_DOT}Error-{err}"
        post_error_msg(Device.devicename, event_msg)

    return False

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Using the mobapp tracking method or iCloud is disabled
#   Trigger the mobapp to send a location request transaction
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def request_location(Device, is_alive_check=False, force_request=False):
    '''
    Send location request to phone. Check to see if one has been sent but not responded to
    and, if true, set interval based on the retry count.
    '''

    if (Gb.used_data_source_MOBAPP is False
            or Device.mobapp_monitor_flag is False
            or Device.mobapp[NOTIFY] == ''
            or Device.is_offline):
        return

    devicename = Device.devicename

    try:
        # Do not send a request if one has already been sent until it is older than the offline interval
        # mod-7/5/2022-add 1200 chk, add loc_data_secs > inzone_secs
        send_msg_interval_secs = max(Gb.offline_interval_secs, 1800)
        if force_request:
            pass

        elif (Device.mobapp_request_loc_last_secs > 0
                and secs_since(Device.mobapp_request_loc_last_secs) < send_msg_interval_secs):
            return

        elif Device.is_mobapp_data_good:

            return

        if is_alive_check:
            event_msg =(f"MobApp Alive Check > Location Requested, "
                        f"LastContact-{format_time_age(Device.mobapp_data_secs)}")

            if Device.mobapp_request_loc_last_secs > 0:
                event_msg +=  f", LastRequest-{format_time_age(Device.mobapp_request_loc_last_secs)}"
        else:
            event_msg =(f"MobApp Location Requested > "
                        f"LastLocated-{format_time_age(Device.mobapp_data_secs)}")
            if Device.old_loc_cnt > 2:
                event_msg += f", OldThreshold-{format_timer(Device.old_loc_threshold_secs)}"
        post_event(Device, event_msg)

        if Device.mobapp_request_loc_first_secs == 0:
            Device.mobapp_request_loc_first_secs = Gb.this_update_secs
        message = {"message": "request_location_update"}
        message_sent_ok = send_message_to_device(Device, message)

        #Gb.hass.async_create_task(
        #    Gb.hass.services.async_call('notify',  entity_id, service_data))

        if message_sent_ok:
            Device.mobapp_request_loc_last_secs = Gb.this_update_secs
            Device.mobapp_request_loc_sent_secs = Gb.this_update_secs
            Device.write_ha_sensor_state(NEXT_UPDATE, 'LOC RQSTD')
            Device.display_info_msg(event_msg)
        else:
            Device.mobapp_request_loc_last_secs = 0
            Device.mobapp_request_loc_sent_secs = 0
            post_event(Device, f"{EVLOG_NOTICE}{event_msg} > Failed to send message")

    except Exception as err:
        log_exception(err)
        error_msg = (f"iCloud3 Error > An error occurred sending a location request > "
                    f"Device-{Device.fname_devicename}, Error-{err}")
        post_error_msg(devicename, error_msg)

#-----------------------------------------------------------------------------------------------------
def request_sensor_update(Device):
    '''
    Request the mobapp to update it's sensors
    '''
    #if mins_since(Device.mobapp_request_sensor_update_secs) > 15:
    Device.mobapp_request_sensor_update_secs = time_now_secs()

    message = {"message": "command_update_sensors"}
    message_sent_ok = send_message_to_device(Device, message)

    return message_sent_ok
