namespace MonocleService
{

 /*
{
    "test": [
	    {
		    "event_date": "2022-03-01 10:30:00",
		    "event_type": "power",
		    "event_data": {"ws": 100.1, "ps": 10}
	    },
		{
		    "event_date": "2022-03-01 10:31:00",
		    "event_type": "temperature",
		    "event_data": {"rh": 80.1, "t": 25.89}
	    }
    ]
}
*/

    public class TelemetryData : Dictionary<string, List<TelemetryItem>>
    {

    }

    public class TelemetryItem
    { 
        public string? event_date { get; set; }
        public string? event_type { get; set; }
        public Dictionary<string, double>? event_data { get; set; }
    }

}
