using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace MonocleService.Controllers
{
    [ApiController]
    [Route("/")]
    public class LoggerController : Controller
    {
        private IConfiguration _config;
        private TelemetryStore store;

        public LoggerController(IConfiguration config)
        {
            _config = config;
            store = TelemetryStore.GetInstance(_config);
        }

        [HttpGet]
        public IActionResult Get()
        {
            Console.WriteLine("Hello World");
            Dictionary<string, object> data = new Dictionary<string, object>();
            data.Add("message", "Hello World");
            return Json(data);
        }

        [HttpPost]
        public IActionResult Post(TelemetryData telemetry_data)
        {
            Dictionary<string, object> reponce_data = new Dictionary<string, object>();
            if (telemetry_data == null)
            {
                Console.WriteLine("No Data");
                reponce_data.Add("message", "no data");
                return Json(reponce_data);
            }

            string data_json = JsonSerializer.Serialize(telemetry_data);
            string date_stamp = DateTime.Now.ToString(data_json);
            Console.WriteLine(date_stamp);
            store.SaveTelemetry(telemetry_data);

            reponce_data.Add("message", "Telemetry Saved");
            return Json(reponce_data);
        }
    }
}
