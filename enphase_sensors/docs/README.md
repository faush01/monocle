

Documentation for local REST connection

https://enphase.com/download/iq-gateway-access-using-local-apis-or-local-ui-token-based-authentication-tech-brief

https://enphase.com/download/iq-gateway-local-apis-or-ui-access-using-token

https://community.home-assistant.io/t/enphase-local-api-with-firmware-7-x-my-setup/563828

https://community.home-assistant.io/t/enphase-envoy-d7-firmware-with-jwt-a-different-approach/594082


HA Sensor setup
Make the REST sesnor in HA
Once you have the token, then you can make a rest sensor in HA:

sensor:
  - platform: rest
    resource: https://envoy.local/ivp/meters/readings
    name: Solar Power Output
    unique_id: solar_array_output_id
    scan_interval: 60
    value_template: "{{ value_json[0].activePower | float }}"
    headers:
      Authorization: Bearer <token>
    verify_ssl: False
    state_class: measurement
    device_class: power
    unit_of_measurement: W
    json_attributes_path: "$.[0]"
    json_attributes:
      - eid
      - actEnergyDlvd
      - timestamp
      - voltage
      - current
      - freq


Example calculations for power usage

value_json[0].activePower 	Power Production 	687.208
value_json[1].activePower 	Power Net 	892.938

Power Consumption (Calculated) (production + net) 	1580.146
Power Export (Calculated) (production - consumption) 	0.000
Power Import (Calculated) (consumption - production) 	892.938
