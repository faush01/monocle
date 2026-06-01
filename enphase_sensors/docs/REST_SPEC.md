API Name Command Description

System information GET https://{IQ Gateway_ip}/info 
Returns serial number, model id, and firmware

Provisioned device details GET https://{IQ Gateway_ip}/ivp/ensemble/device_list
Returns the commissioning
status of provisioned
devices.

Meter details GET https://{IQ Gateway_ip}/ivp/meters
Returns meter status, type
of meter, and number of
phase measurements.

Meter readings GET https://{IQ Gateway_ip}/ivp/meters/readings
Returns measurements from
Production CT, storage CT,
and Consumption CT, and
all are subjected to the
availability of CTs.

Production meter data GET https://{IQ Gateway_ip}/api/v1/production
Returns production energy
and active power values for
today, the last seven days,
and lifetime in watt-hours.
The API works even when
the production meter is not
installed and enabled at the
site.

Energy data GET https://{IQ Gateway_ip}/ivp/pdm/energy
Returns energy and
active power values for
microinverters, revenue
grade meters, production
and consumption meter for
today, last seven days, and
lifetime in watt-hours. The
API works even when the
production meter is not
installed and enabled at the
site.

Inverter production data GET https://{IQ Gateway_ip}/api/v1/production/inverters
Returns maximum and last
reported active power
production information
of the available
microinverters.

Meter’s live data GET https://{IQ Gateway_ip}/ivp/livedata/status 
Returns meter’s live data
with tasks and counters.

Power consumption data GET https://{IQ Gateway_ip}/ivp/meters/reports/consumption
Returns power consumption information of
the loads.

Grid readings GET https://{IQ Gateway_ip}/ivp/meters/gridReading
Returns the voltage,
current, frequency, active &
reactive power at the point
of grid connection.
