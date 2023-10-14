using System.Configuration;
using System.Diagnostics;
using System.Diagnostics.Contracts;
using System.Net;
using System.Security.Policy;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace SysMon
{
    public class Program
    {
        //private static WebClient wc = new WebClient();
        private static HttpClient http_client = new HttpClient();

        private static Dictionary<string, string> ParseParams(string[] args)
        {
            HashSet<string> p_names = new HashSet<string>() { "-server", "-db", "-name" };
            Dictionary<string, string> clp = new Dictionary<string, string>();
            for(int i = 0; i < args.Length-1; i++)
            {
                string p_name = args[i];
                if(!p_names.Contains(p_name)) continue; // not a param name so try next arg
                string p_val = args[i+1];
                if (p_names.Contains(p_val)) continue; // param vale was actuall a name so continue
                clp[p_name] = p_val;
                i++;
            }
            return clp;
        }

        static async Task Main(string[] args)
        {
            Console.WriteLine("Usage :\n -server <url of the collection server http://localhost:3456>\n -db <the name of the db file to use>\n -name <the name of data being logged>");

            // params
            string server_url = "http://localhost:3456";
            string db_filename = "server_stats";
            string section_name = "server";
            Dictionary<string, string> clp = ParseParams(args);
            if (clp.ContainsKey("-server")) server_url = clp["-server"];
            if (clp.ContainsKey("-db")) db_filename = clp["-db"];
            if (clp.ContainsKey("-name")) section_name = clp["-name"];

            // Get-Counter -Counter "\Processor Information(*)\% Processor Utility"

            // https://www.appsloveworld.com/csharp/100/347/class-performancecounter-documentation
            // Get-Counter -ListSet *
            // Get-Counter -ListSet "Thermal Zone Information" | Select -ExpandProperty Counter
            // Get-Counter -Counter "\Thermal Zone Information(*)\High Precision Temperature" -SampleInterval 5 -MaxSamples 5
            // Get-Counter -Counter "\Thermal Zone Information(*)\*"
            // t_counter - 273.15

            // Get-Counter -ListSet "Memory" | Select -ExpandProperty Counter
            // Get-Counter -Counter "\Memory\Transition Faults/sec" -SampleInterval 5 -MaxSamples 5
            // https://docs.microsoft.com/en-us/previous-versions/ms804008(v=msdn.10)?redirectedfrom=MSDN
            // Pages Input/sec

            // Get-Counter -Counter "\GPU Engine(*)\Utilization Percentage"

            SysMon sysMon = new SysMon();

            //cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total");
            PerformanceCounter cpuCounter = new PerformanceCounter("Processor Information", "% Processor Utility", "_Total");
            PerformanceCounter ramCounter = new PerformanceCounter("Memory", "Available MBytes");
            PerformanceCounter pageFaultsCounter = new PerformanceCounter("Memory", "Pages Input/sec");
            PerformanceCounter disk_read = new PerformanceCounter("PhysicalDisk", "Disk Read Bytes/sec", "_Total");
            PerformanceCounter disk_write = new PerformanceCounter("PhysicalDisk", "Disk Write Bytes/sec", "_Total");
            List<NetworkInterface> netCounters = sysMon.GetNetworkCounters();
            Dictionary<string, PerformanceCounter> gpu_usage_counters = new Dictionary<string, PerformanceCounter>();

            while (true)
            {
                sysMon.GetGpuUsageCounters(gpu_usage_counters);
                Dictionary<string, double> gpu_usage = sysMon.GetGpuUsage(gpu_usage_counters);

                double cpu = cpuCounter.NextValue();
                double am = ramCounter.NextValue();
                double pfs = pageFaultsCounter.NextValue();
                Dictionary<string, double> network = sysMon.GetTotalNetworkIO(netCounters);
                double net_in = network["in"];
                double net_out = network["out"];
                double d_read = disk_read.NextValue();
                double d_write = disk_write.NextValue();

                cpu = Math.Round(cpu, 1);
                pfs = Math.Round(pfs, 1);
                net_in = Math.Round(net_in, 1);
                net_out = Math.Round(net_out, 1);
                d_read = Math.Round(d_read, 1);
                d_write = Math.Round(d_write, 1);
                
                string date_string = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                List<TelemetryItem> tele_items = new List<TelemetryItem>();

                TelemetryItem item = new TelemetryItem();
                item.event_date = date_string;
                item.event_type = section_name;
                Dictionary<string, double> event_data = new Dictionary<string, double>();

                event_data.Add("c", cpu);
                event_data.Add("am", am);
                event_data.Add("pfs", pfs);
                event_data.Add("ni", net_in);
                event_data.Add("no", net_out);
                event_data.Add("dr", d_read);
                event_data.Add("dw", d_write);

                foreach (var i in gpu_usage)
                {
                    event_data.Add(i.Key.ToLower(), i.Value);
                }

                item.event_data = event_data;
                tele_items.Add(item);

                TelemetryData data = new TelemetryData();
                data.Add(db_filename, tele_items);

                string data_json = JsonSerializer.Serialize(data);
                Console.WriteLine(data_json);

                // send data
                //wc.Headers[HttpRequestHeader.ContentType] = "application/json";
                StringContent content = new StringContent(data_json, Encoding.UTF8, "application/json");
                try
                {
                    //string response = wc.UploadString("http://localhost:3456", data_json);
                    var result = await http_client.PostAsync(server_url, content);
                    string ret_content = await result.Content.ReadAsStringAsync();
                    Console.WriteLine(result.StatusCode + " " + ret_content);
                    result = null;
                    ret_content = null;
                }
                catch(Exception ex)
                {
                    Console.WriteLine("Error sending data : " + ex.Message);
                }

                content = null;
                data_json = null;
                item = null;
                tele_items = null;
                data = null;
                gpu_usage = null;
                event_data = null;
                
                //System.GC.Collect();

                Thread.Sleep(60000);
            }
        }
    }
}