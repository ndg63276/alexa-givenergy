import requests


def get_headers(apikey):
    headers = {
        "Authorization": "Bearer " + apikey,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    return headers


def lambda_handler(event, context):
    if "accessToken" not in event["context"]["System"]["user"]:
        return account_not_linked()
    apikey = event["context"]["System"]["user"]["accessToken"]
    headers = get_headers(apikey)
    if event["request"]["type"] == "LaunchRequest":
        return get_help()
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event, headers)


def account_not_linked():
    output = "Hello. To use this skill, you must provide your GivEnergy API key. You can do this from the Alexa app or Amazon website."
    should_end_session = True
    return build_response(build_account_linking_response(output, should_end_session))


def get_help():
    output = "Hello. For example say, 'How full is my battery?'"
    should_end_session = False
    return build_response(build_short_speechlet_response(output, should_end_session))


def get_battery_level_response(headers):
    battery_level = get_battery_level(headers)
    if type(battery_level) in (int, float):
        output = "Your battery is "+str(battery_level)+"% full."
    else:
        output = battery_level
    should_end_session = True
    return build_response(build_short_speechlet_response(output, should_end_session))


def get_battery_level(headers):
    system_data = get_latest_system_data(headers)
    if "error" in system_data:
        return system_data["error"]
    else:
        return system_data["data"]["battery"]["percent"]


def get_grid_voltage_response(headers):
    grid_voltage = get_grid_voltage(headers)
    if type(grid_voltage) in (int, float):
        output = "The grid is at "+str(grid_voltage)+" volts."
    else:
        output = grid_voltage
    should_end_session = True
    return build_response(build_short_speechlet_response(output, should_end_session))


def get_grid_voltage(headers):
    system_data = get_latest_system_data(headers)
    if "error" in system_data:
        return system_data["error"]
    else:
        return system_data["data"]["grid"]["voltage"]


def get_solar_power(headers):
    system_data = get_latest_system_data(headers)
    if "error" in system_data:
        output = system_data["error"]
    else:
        solar_power = system_data["data"]["solar"]["power"]
        output = "You are currently generating "+str(solar_power)+" watts."
    should_end_session = True
    return build_response(build_short_speechlet_response(output, should_end_session))


def get_consumption(headers):
    system_data = get_latest_system_data(headers)
    if "error" in system_data:
        output = system_data["error"]
    else:
        consumption = system_data["data"]["consumption"]
        output = "You are currently using "+str(consumption)+" watts."
    should_end_session = True
    return build_response(build_short_speechlet_response(output, should_end_session))


def get_communication_devices(headers):
    url = "https://api.givenergy.cloud/v1/communication-device"
    params = {"page": "1"}
    r = requests.get(url, headers=headers, params=params)
    return r.json()


def get_status(headers):
    system_data = get_latest_system_data(headers)
    if "error" in system_data:
        output = system_data["error"]
    else:
        consumption = system_data["data"]["consumption"]
        output = "You are currently using "+str(consumption)+" watts."
    should_end_session = True
    return build_response(build_short_speechlet_response(output, should_end_session))


def get_latest_system_data(headers, inverter_id=None):
    if inverter_id is None:
        devices = get_communication_devices(headers)
        if "data" in devices:
            inverter_id = devices["data"][0]["inverter"]["serial"]
        else:
            return {"error": "I wasn't able to get device data from your system. Please try re-linking the skill."}
    url = "https://api.givenergy.cloud/v1/inverter/"+inverter_id+"/system-data/latest"
    r = requests.get(url, headers=headers)
    return r.json()


def restart_inverter(headers):
    devices = get_communication_devices(headers)
    inverter_id = devices["data"][0]["inverter"]["serial"]
    url = "https://givenergy.cloud/internal-api/inverter/actions/"+inverter_id+"/restart"
    r = requests.post(url, headers=headers)
    return r.json()


def on_intent(event, headers):
    intent_name = event["request"]["intent"]["name"]
    # Dispatch to your skill"s intent handlers
    if intent_name == "BatteryIntent":
        return get_battery_level_response(headers)
    elif intent_name == "GridVoltageIntent":
        return get_grid_voltage_response(headers)
    elif intent_name == "SolarGenerationIntent":
        return get_solar_power(headers)
    elif intent_name == "ConsumptionIntent":
        return get_consumption(headers)
    elif intent_name == "StatusIntent":
        return get_status(headers)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help()
    elif intent_name == "AMAZON.CancelIntent":
        return do_nothing()
    elif intent_name == "AMAZON.StopIntent":
        return do_nothing()
    else:
        raise ValueError("Invalid intent")


def build_short_speechlet_response(output, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "shouldEndSession": should_end_session
    }


def build_account_linking_response(output, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "LinkAccount"
        },
        "shouldEndSession": should_end_session
    }


def build_response(speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": {},
        "response": speechlet_response
    }

