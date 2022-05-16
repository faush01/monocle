using MonocleService;
using Newtonsoft.Json;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.

var app = builder.Build();

TelemetryStore store = new TelemetryStore(builder.Configuration);

// Configure the HTTP request pipeline.

app.MapGet("/", () =>
{
    Console.WriteLine(DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " : Hello World");
    return "hello world";
});

app.MapPost("/", (TelemetryData telemetry_data) =>
{
    if(telemetry_data == null)
    {
        Console.WriteLine("No Data");
        return "no_data";
    }

    string date_stamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
    string telem_str = JsonConvert.SerializeObject(telemetry_data);
    Console.WriteLine(date_stamp + " : telemetry : " + telem_str);
    store.SaveTelemetry(telemetry_data);

    return "saved";
});

app.Run();

