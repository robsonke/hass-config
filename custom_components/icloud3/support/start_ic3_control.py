from ..global_variables     import GlobalVariables as Gb
from ..const                import (VERSION, VERSION_BETA, ICLOUD3, ICLOUD3_VERSION, DOMAIN, ICLOUD3_VERSION_MSG,
                                    NOT_SET, IC3LOG_FILENAME,
                                    CRLF, CRLF_DOT, CRLF_HDOT, CRLF_X, NL, NL_DOT, LINK, YELLOW_ALERT,
                                    EVLOG_ALERT, EVLOG_ERROR, EVLOG_IC3_STARTING, EVLOG_IC3_STAGE_HDR,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    CONF_VERSION, ICLOUD, ZONE_DISTANCE,
                                    CONF_USERNAME, CONF_PASSWORD, CONF_LOCATE_ALL,
                                    ICLOUD, MOBAPP, DISTANCE_TO_DEVICES,
                                    )

from ..support              import hacs_ic3
from ..support              import start_ic3
from ..support              import config_file
from ..support              import mobapp_interface
from ..support              import pyicloud_ic3_interface
from ..support              import determine_interval as det_interval

from ..helpers.common       import (instr, is_empty, isnot_empty, list_to_str, list_add, list_del, )
from ..helpers.messaging    import (broadcast_info_msg,
                                    post_event, post_error_msg, log_error_msg, post_startup_alert,
                                    post_monitor_msg, post_internal_error,
                                    write_ic3log_recd,
                                    log_debug_msg, log_warning_msg, log_info_msg, log_exception, log_rawdata,
                                    _evlog, _log, more_info, format_filename,
                                    write_config_file_to_ic3log,
                                    open_ic3log_file, )
from ..helpers.time_util    import (time_now_secs, calculate_time_zone_offset, )

import homeassistant.util.dt as dt_util


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_1_setup_variables():

    Gb.trace_prefix = 'STAGE1'
    stage_title = f'Stage 1 > Initial Preparations'

    open_ic3log_file()

    # if Gb.prestartup_log:
    #     _prestartup_log = Gb.prestartup_log
    #     Gb.prestartup_log = ''
    #     write_ic3log_recd(f"$$$$$\n#####\n{_prestartup_log}")

    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    broadcast_info_msg(stage_title)

    Gb.EvLog.display_user_message(f'iCloud3 v{Gb.version} > Initializiing')

    try:
        Gb.this_update_secs             = time_now_secs()
        Gb.startup_alerts               = []
        Gb.EvLog.alert_message          = ''
        Gb.config_track_devices_change_flag = False
        Gb.reinitialize_icloud_devices_flag = False     # Set when no devices are tracked and iC3 needs to automatically restart
        Gb.reinitialize_icloud_devices_cnt  = 0

        config_file.load_storage_icloud3_configuration_file()
        write_config_file_to_ic3log()
        start_ic3.initialize_global_variables()
        start_ic3.set_global_variables_from_conf_parameters()

        # Run these setup items on a restart. Do not then when initially starting iC3
        if Gb.initial_icloud3_loading_flag is False:
            Gb.EvLog.startup_event_recds = []
            Gb.EvLog.startup_event_save_recd_flag = True
            post_event( f"{EVLOG_IC3_STARTING}iCloud3 v{Gb.version} > Restarting, "
                        f"{dt_util.now().strftime('%A, %b %d')}")

            if (Gb.use_data_source_ICLOUD):
                # Can not run this as an executor job to avoid 'no running event loop' error
                # Gb.hass.async_add_executor_job(
                #        pyicloud_ic3_interface.create_all_PyiCloudServices)
                pyicloud_ic3_interface.create_all_PyiCloudServices()

        start_ic3.define_tracking_control_fields()

        if Gb.ha_config_directory != '/config':
            post_event( f"Base Config Directory > "
                        f"{CRLF_DOT}{Gb.ha_config_directory}")
        post_event( f"iCloud3 Directory > "
                    f"{CRLF_DOT}{Gb.icloud3_directory}")
        if Gb.conf_profile[CONF_VERSION] == 0:
            post_event( f"iCloud3 Configuration File > "
                        f"{CRLF_DOT}{format_filename(Gb.config_ic3_yaml_filename)}")
        else:
            post_event( f"iCloud3 Configuration File > "
                        f"{CRLF_DOT}{format_filename(Gb.icloud3_config_filename)}")

        start_ic3.display_platform_operating_mode_msg()
        Gb.hass.loop.create_task(start_ic3.update_lovelace_resource_event_log_js_entry())
        Gb.hass.loop.create_task(hacs_ic3.check_hacs_icloud3_update_available())
        start_ic3.check_ic3_event_log_file_version()

        post_monitor_msg(f"LocationInfo-{Gb.ha_location_info}")

        calculate_time_zone_offset()
        start_ic3.set_event_recds_max_cnt()

        post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_2_prepare_configuration():

    Gb.trace_prefix = 'STAGE2'
    stage_title = f'Stage 2 > Prepare Support Services'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        start_ic3.create_Zones_object()
        start_ic3.create_Waze_object()

        Gb.WazeHist.load_track_from_zone_table()

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.update_event_log_display("")

    try:
        configuration_needed_msg = ''
        # Default configuration that has not been updated or migrated from v2
        if Gb.conf_profile[CONF_VERSION] == -1:
            configuration_needed_msg = 'INITIAL INSTALLATION - CONFIGURATION IS REQUIRED'

        elif Gb.conf_profile[CONF_VERSION] == 0:
            configuration_needed_msg = 'CONFIGURATION PARAMETERS WERE MIGRATED FROM v2 to v3 - ' \
                                        'THEY MUST BE REVIEWED BEFORE STARTING ICLOUD3'
        elif ((is_empty(Gb.conf_apple_accounts) and Gb.conf_data_source_ICLOUD)
                or is_empty(Gb.conf_devices)):
            configuration_needed_msg = 'ICLOUD3 CONFIGURATION NEEDS TO BE SET UP'

        if configuration_needed_msg:
            post_startup_alert('iCloud3 Configuration not set up')
            event_msg =(f"{EVLOG_ALERT}CONFIGURATION ALERT > {configuration_needed_msg}{CRLF}"
                        f"{more_info('configure_icloud3')}")
            post_event(event_msg)

            Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_3_setup_configured_devices():

    Gb.trace_prefix = 'STAGE3'
    stage_title = f'Stage 3 > Device Configuration'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        # Make sure a full restart is done if all of the devices were not found in the iCloud data
        data_sources = ''
        Gb.conf_startup_errors_by_devicename = {}

        if Gb.conf_data_source_ICLOUD: data_sources += f"{ICLOUD}, "
        if Gb.conf_data_source_MOBAPP: data_sources += f"{MOBAPP}, "
        data_sources = data_sources[:-2] if data_sources else 'NONE'
        post_event(f"Data Sources > {data_sources}")

        if Gb.config_track_devices_change_flag:
            pass
        elif (Gb.conf_data_source_ICLOUD
                and Gb.icloud_device_verified_cnt < len(Gb.Devices)):
            Gb.config_track_devices_change_flag = True
        elif Gb.log_debug_flag:
            Gb.config_track_devices_change_flag = True

        start_ic3.create_Devices_object()

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.update_event_log_display("")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_4_setup_data_sources():

    Gb.trace_prefix = 'STAGE4'
    stage_title = f"Stage 4 > Data Source Device Assignment"
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.display_user_message(stage_title)
    broadcast_info_msg(stage_title)

    # Remove any device related errors so a retry will not show previous alerts
    _startup_alerts = [_startup_alert   for _startup_alert in Gb.startup_alerts
                                        if instr(_startup_alert.lower(), 'device') is False]
    Gb.startup_alerts = _startup_alerts

    for Device in Gb.Devices:
        Device.set_fname_alert('')

    post_event(f"Data Source > Apple Account used-{Gb.use_data_source_ICLOUD}")
    post_event(f"Data Source > HA Mobile App used-{Gb.use_data_source_MOBAPP}")

    try:
        # Get list of all unique Apple Acct usernames in config
        Gb.conf_usernames = [apple_account[CONF_USERNAME]
                                    for apple_account in Gb.conf_apple_accounts
                                    if (apple_account[CONF_USERNAME] in Gb.username_valid_by_username
                                            and apple_account[CONF_USERNAME] != '')]

        if Gb.use_data_source_ICLOUD and isnot_empty(Gb.conf_usernames):
            _log_into_apple_accounts(retry=True)

            start_ic3.setup_data_source_ICLOUD()

            for PyiCloud in Gb.PyiCloud_by_username.values():
                if PyiCloud.account_locked:
                    post_error_msg( f"{EVLOG_ERROR}Apple Account {PyiCloud.account_owner} "
                                    f"is Locked. Log onto www.icloud.com and unlock "
                                    f"your account to reauthorize location services.")
                    post_startup_alert(f"Apple Account {PyiCloud.account_owner} is Locked")

        mobapp_interface.get_entity_registry_mobile_app_devices()
        mobapp_interface.get_mobile_app_integration_device_info()

        if Gb.conf_data_source_MOBAPP:
            start_ic3.setup_tracked_devices_for_mobapp()

        start_ic3.set_devices_verified_status()
        return_code = _are_all_devices_verified()

        if isnot_empty(Gb.username_pyicloud_503_connection_error):
            post_event( f"{EVLOG_ERROR}Apple Acct > {list_to_str(Gb.username_pyicloud_503_connection_error)}, "
                        f"Failed to log into the Apple Account (Connection Error 503), will "
                        f"retry every 15-minutes")

    except Exception as err:
        log_exception(err)
        return_code = False

    post_event(f"{EVLOG_IC3_STAGE_HDR} {stage_title}")
    Gb.EvLog.update_event_log_display("")

    return return_code

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_4_setup_data_sources_retry(final_retry=False):
    '''
    Apple accounts with login errors or containing tracked devices that are not found
    in Stage 4 are added to Gb.usernames_setup_error_retry_list. iCloud3_main checks to
    see if there are any devices that are in this list when starting up. Their setup
    will be retried here if necessary. This is a shortened version of the full Stage 4
    where all devices for all data sources are set up.
    '''

    Gb.trace_prefix = 'STAGE4'
    stage_title = f"Stage 4 > Data Source Device Assignment (Retry)"
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.display_user_message(stage_title)
    broadcast_info_msg(stage_title)

    post_event(f"{EVLOG_ALERT}Apple Acct setup will be retried to resolve Missing Devices:"
                f"{CRLF_DOT}Apple Account > {list_to_str(Gb.usernames_setup_error_retry_list)}")

    # Remove any device related errors so a retry will not show previous alerts
    _startup_alerts = [_startup_alert   for _startup_alert in Gb.startup_alerts
                                        if instr(_startup_alert.lower(), 'device') is False]
    Gb.startup_alerts = _startup_alerts
    for Device in Gb.Devices:
        Device.set_fname_alert('')

        # Test code for invalid apple_account value. Set config value for dev #2 to invalid@gmail.com
        # Then set it to the valid apple_account value here. It will fail in Stage 4 & retry #1
        # but pass in the last_retry
        # if final_retry and Device.conf_apple_acct_username == 'invalid@gmail.com':
        #     Device.conf_apple_acct_username = 'valid@gmail.com'
        #     Gb.conf_devices[1]['apple_account'] = 'valid@gmail.com'

    try:
        all_verified_flag = True
        for username in Gb.usernames_setup_error_retry_list:
            _log_into_apple_accounts(retry=True)

            PyiCloud = Gb.PyiCloud_by_username.get(username)

            if PyiCloud:
                post_event(f"Verify Apple Acct > {PyiCloud.account_owner_username}, Verified")
                start_ic3.setup_data_source_ICLOUD(retry=True)
                start_ic3.set_devices_verified_status()

                if PyiCloud.account_locked:
                    post_error_msg( f"{EVLOG_ERROR}Apple Account {PyiCloud.account_owner} "
                                    f"is Locked. Log onto www.icloud.com and unlock "
                                    f"your account to reauthorize location services.")
                    post_startup_alert(f"Apple Account {PyiCloud.account_owner_USERNAME} is Locked")
            else:
                post_event(f"{EVLOG_ALERT}APPLE ACCT LOGIN ALERT > {username}, Login Unsuccessful")

            all_verified_flag = _are_all_devices_verified(retry=True)

            if all_verified_flag:
                Gb.usernames_setup_error_retry_list = \
                    list_del(Gb.usernames_setup_error_retry_list, PyiCloud.account_owner_username)

    except Exception as err:
        log_exception(err)
        all_verified_flag = False


    post_event(f"{EVLOG_IC3_STAGE_HDR} {stage_title}")
    Gb.EvLog.update_event_log_display("")

    if final_retry:
        if is_empty(Gb.usernames_setup_error_retry_list):
            post_event(f"{EVLOG_ALERT}ALL ICLOUD STARTUP ERRORS RESOLVED")
        else:
            post_startup_alert(f"Apple Acct Login Error-{list_to_str(Gb.usernames_setup_error_retry_list)}")

    return all_verified_flag

#------------------------------------------------------------------
def _log_into_apple_accounts(retry=False):
    '''
    Verify that all Apple Account PyiCloud objects have been created
    '''
    if Gb.use_data_source_ICLOUD is False:
        return False

    if Gb.initial_icloud3_loading_flag is False:
        return True

    # # Get list of all unique Apple Acct usernames in config
    # Gb.conf_usernames = [apple_account[CONF_USERNAME]
    #                                     for apple_account in Gb.conf_apple_accounts
    #                                     if (apple_account[CONF_USERNAME] in Gb.username_valid_by_username
    #                                             and apple_account[CONF_USERNAME] != '')]
    if is_empty(Gb.conf_usernames):
        return False

    # Verify that all apple accts have been setup. Restart the setup process for any that
    # are not complete
    for username in Gb.conf_usernames:
        PyiCloud = Gb.PyiCloud_by_username.get(username)
        if (PyiCloud is None
                or PyiCloud.RawData_by_device_id == {}):

            conf_apple_acct, _idx = config_file.conf_apple_acct(username)

            PyiCloud = pyicloud_ic3_interface.log_into_apple_account(
                                        username,
                                        Gb.PyiCloud_password_by_username[username],
                                        locate_all_devices=conf_apple_acct[CONF_LOCATE_ALL])

            if PyiCloud:
                Gb.PyiCloud_by_username[username] = PyiCloud

    if is_empty(Gb.devices_without_location_data):
        post_event(f"Apple Acct > {PyiCloud.username_base}, All Devices Located")
    # else:
    #     post_event(f"{YELLOW_ALERT}Apple Acct > Devices not Located, {list_to_str(Gb.devices_without_location_data)}")

    return True

#------------------------------------------------------------------
def _are_all_devices_verified(retry=False):
    '''
    See if all tracked devices are verified.

    Arguments:
        retry   - True  - The verification was retried
                - False - This is the first time the verification was done

    Return:
        True  - All were verifice
        False - Some were not verified
    '''


    # Get a list of all tracked devices that have not been set up by icloud or the Mobile App
    unverified_devices = [Device.fname_devicename
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if Device.verified_flag is False and Device.isnot_inactive]
    unverified_device_usernames = [Device.conf_apple_acct_username
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if Device.verified_flag is False and Device.isnot_inactive]

    Gb.usernames_setup_error_retry_list   = list(set(unverified_device_usernames))
    Gb.devicenames_setup_error_retry_list = list(set(unverified_devices))

    Gb.startup_lists['_.usernames_setup_error_retry_list']   = Gb.usernames_setup_error_retry_list
    Gb.startup_lists['_.devicenames_setup_error_retry_list'] = Gb.devicenames_setup_error_retry_list

    if is_empty(unverified_devices):
        return True

    if retry:
        post_startup_alert("Some Tracked Devices could not be verified. Restart may be needed.")
        event_msg = (f"{EVLOG_ALERT}Some Tracked Devices could not be verified. Review and correct "
                    f"any configuration errors. Then restart iCloud3")
    else:
        event_msg = f"{EVLOG_ALERT}UNVERIFIED DEVICES ALERT > Some Tracked Devices could not be verified."
    event_msg += (f"{CRLF_DOT}Unverified Devices > {', '.join(unverified_devices)}")
    post_event(event_msg)

    return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_5_configure_tracked_devices():

    Gb.trace_prefix = 'STAGE5'
    stage_title = f'Stage 5 > Device Configuration Summary'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    # if Gb.PyiCloud:
        # log_debug_msg(f"PyiCloud Finialized > {Gb.PyiCloud.account_owner}")
    for username, PyiCloud in Gb.PyiCloud_by_username.items():
        log_debug_msg(f"PyiCloud Finialized > {PyiCloud.account_owner}")

    try:
        Gb.EvLog.display_user_message(stage_title)
        broadcast_info_msg(stage_title)

        # start_ic3.remove_unverified_untrackable_devices()
        start_ic3.identify_tracked_monitored_devices()
        Gb.EvLog.setup_event_log_trackable_device_info()

        start_ic3.setup_trackable_devices()
        start_ic3.display_inactive_devices()
        Gb.EvLog.update_event_log_display("")

    except Exception as err:
        log_exception(err)

    post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
    Gb.EvLog.display_user_message('')


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_6_initialization_complete():

    Gb.trace_prefix = 'STAGE6'
    stage_title = f'{ICLOUD3} Initialization Complete'
    log_info_msg(f"* > {EVLOG_IC3_STAGE_HDR}{stage_title}")

    broadcast_info_msg(stage_title)

    start_ic3.display_platform_operating_mode_msg()
    Gb.EvLog.display_user_message('')

    Gb.startup_log_msgs = ''

    try:
        start_ic3.display_object_lists()
        start_ic3.dump_startup_lists_to_log()

        if Gb.startup_alerts:
            item_no = 1
            alert_msg = ''
            for alert in Gb.startup_alerts:
                alert_msg += f"{CRLF}{item_no}. {alert}"
                item_no += 1

            # Build alert msg for the evlog.attrs['alert_startup'] attribute for display
            alerts_str = alert_msg.replace(CRLF_HDOT, NL_DOT)
            alerts_str = alerts_str.replace(CRLF_X, NL_DOT)
            alerts_str = alerts_str.replace(CRLF, NL)
            Gb.startup_alerts_str = alerts_str

            Gb.EvLog.alert_message = 'Problems occured during startup up that should be reviewed'
            post_event( f"{EVLOG_ALERT}The following issues were detected when starting iCloud3. "
                        f"Scroll through the Startup Log for more information: "
                        f"{alert_msg}")

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def stage_7_initial_locate():
    '''
    The PyiCloud Authentication function updates the iCloud raw data after the account
    has been authenticated. Requesting the initial data update there speeds up loading iC3
    since the Apple Acct login & authentication was started in the __init__ module.

    This routine processes the new raw iCloud data and set the initial location.
    '''

    # The restart will be requested if using iCloud as a data source and no data was returned
    # from PyiCloud
    if Gb.PyiCloud_by_username == {}:
        return

    if Gb.reinitialize_icloud_devices_flag and Gb.conf_icloud_device_cnt > 0:
        return_code = reinitialize_icloud_devices()

    Gb.trace_prefix = '1stLOC'

    Gb.this_update_secs = time_now_secs()
    Gb.this_update_time = dt_util.now().strftime('%H:%M:%S')
    post_event("Requesting Initial Locate")
    post_event(f"{EVLOG_IC3_STARTING}{ICLOUD3_VERSION_MSG} > Start up Complete")

    for Device in Gb.Devices:
        if Device.PyiCloud_RawData_icloud:
            Device.update_dev_loc_data_from_raw_data_FAMSHR(Device.PyiCloud_RawData_icloud)

        else:
            continue

        post_event(Device,
                    f"{Device.dev_data_source} Trigger > Initial Locate@"
                    f"{Device.loc_data_time_gps}")

        if Device.no_location_data:
            post_event(Device, f"{EVLOG_ALERT}NO GPS DATA RETURNED FROM ICLOUD LOCATION SERVICE")
            error_msg = (f"iCloud3 > {Device.fname_devicename} > "
                        "No GPS data was returned from iCloud Location "
                        "Service on the initial locate")
            log_warning_msg(error_msg)

        Device.update_sensors_flag = True

        Gb.iCloud3.process_updated_location_data(Device, ICLOUD)

        Device.icloud_initial_locate_done = True

    # Update the distance between all devices not that they have all been located
    # Then go back through and update the device_tracker entity to set the distance
    # between devices for the first time
    det_interval.set_dist_to_devices(post_event_msg=True)
    for Device in Gb.Devices:
        Device.sensors[DISTANCE_TO_DEVICES] = \
                    det_interval.format_dist_to_devices_msg(Device, time=True, age=False)
        Device.write_ha_device_tracker_state()

#------------------------------------------------------------------
def reinitialize_icloud_devices():
    '''
    Setup restarting iCloud3 if it has not already been done.

    Return  - True - Continue with Initial Locate
            - False - Restart failes
    '''
    try:
        if Gb.PyiCloud is None:
            return

        Gb.reinitialize_icloud_devices_cnt += 1
        if Gb.reinitialize_icloud_devices_cnt > 2:
            return

        Gb.start_icloud3_inprocess_flag = False
        Gb.reinitialize_icloud_devices_flag = False
        Gb.initial_icloud3_loading_flag = False

        alert_msg = f"{EVLOG_ALERT}"
        if Gb.conf_data_source_ICLOUD:
            unverified_devices = [devicename
                        for devicename, Device in Gb.Devices_by_devicename.items() \
                        if Device.verified_flag is False]

            alert_msg +=(f"UNVERIFIED DEVICES > One or more devices was not verified. "
                        f"Apple Account access may be down, slow to respond or the internet may be down."
                        f"{CRLF_DOT}Unverified Devices > {', '.join(unverified_devices)}")
        post_event(alert_msg)

    except Exception as err:
        log_exception(err)

    return