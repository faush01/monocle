

## Documentation for local REST connection

https://enphase.com/download/iq-gateway-access-using-local-apis-or-local-ui-token-based-authentication-tech-brief

https://enphase.com/download/iq-gateway-local-apis-or-ui-access-using-token

https://community.home-assistant.io/t/enphase-local-api-with-firmware-7-x-my-setup/563828

https://community.home-assistant.io/t/enphase-envoy-d7-firmware-with-jwt-a-different-approach/594082


## HA Sensor setup
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

## Docker Image

The `Build and Push Enphase Sensors Docker Image` GitHub Actions workflow
builds the image and publishes it to:

```text
ghcr.io/faush01/monocle/enphase-sensors
```

The image contains every Python script from `scripts/` and the example
configuration at `/app/config_example.yaml`. Create the logger container with a
named volume, then copy the example configuration out of the container:

```shell
docker volume create enphase-config
docker create --name enphase-sensors \
  --restart unless-stopped \
  --volume enphase-config:/config \
  ghcr.io/faush01/monocle/enphase-sensors:latest
docker cp enphase-sensors:/app/config_example.yaml ./config.yaml
```

Update `config.yaml` with the account, Envoy, and telemetry settings, then copy
it into the container's configuration volume:

```shell
docker cp ./config.yaml enphase-sensors:/config/config.yaml
```

Run `get_token.py` manually against the same volume to retrieve and save the
access token. The persistent container is not running yet, so this initial
setup uses a temporary container:

```shell
docker run --rm \
  --user root \
  --volume enphase-config:/config \
  --entrypoint python \
  ghcr.io/faush01/monocle/enphase-sensors:latest \
  /app/get_token.py
```

Start the logger:

```shell
docker start enphase-sensors
```

Once the logger is running, verify the token from inside that container:

```shell
docker exec enphase-sensors python /app/get_usage.py
```

To refresh the token later, run `get_token.py` inside the running container and
restart it:

```shell
docker exec --user root enphase-sensors python /app/get_token.py
docker restart enphase-sensors
```

To use another directory for `config.yaml`, set the `config_path` environment
variable and mount that directory into the container.
