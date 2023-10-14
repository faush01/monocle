using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.NetworkInformation;
using System.Text;
using System.Threading.Tasks;

namespace SysMon
{
    public class TelemetryData : Dictionary<string, List<TelemetryItem>>
    {

    }

    public class TelemetryItem
    {
        public string event_date { get; set; }
        public string event_type { get; set; }
        public Dictionary<string, double> event_data { get; set; }
    }

    public class NetworkInterface
    {
        public string Name { set; get; }
        public PerformanceCounter BytesInSec { set; get; }
        public PerformanceCounter BytesOutSec { set; get; }
    }

    public class SysMon
    {
        private string[] eng_types = new string[] { "engtype_3d", "engtype_videodecode", "engtype_videoprocessing" };

        private bool IsRequiredEngineType(string interface_string)
        {
            foreach (string eng_type in eng_types)
            {
                if (interface_string.EndsWith(eng_type, StringComparison.CurrentCultureIgnoreCase))
                {
                    return true;
                }
            }
            return false;
        }

        public void GetGpuUsageCounters(Dictionary<string, PerformanceCounter> gpu_usage_counters)
        {
            PerformanceCounterCategory gpu_items = new PerformanceCounterCategory("GPU Engine");
            HashSet<string> instance_names = gpu_items.GetInstanceNames().ToHashSet<string>();
            // it looks like this is all PID process based per instance so we need to add new and remove old counters
            // add new
            foreach (string name in instance_names)
            {
                if (!string.IsNullOrEmpty(name) &&
                    !gpu_usage_counters.ContainsKey(name) &&
                    IsRequiredEngineType(name))
                {
                    gpu_usage_counters[name] = new PerformanceCounter("GPU Engine", "Utilization Percentage", name, true);
                }
            }
            // remove old
            foreach (string key in gpu_usage_counters.Keys)
            {
                if (!instance_names.Contains(key))
                {
                    PerformanceCounter pc = gpu_usage_counters[key];
                    gpu_usage_counters.Remove(key);
                    pc.Close();
                }
            }
        }

        public Dictionary<string, double> GetGpuUsage(Dictionary<string, PerformanceCounter> gpu_usage_counters)
        {
            //g_videodecode
            //g_videoprocessing
            //g_3d
            Dictionary<string, double> totals = new Dictionary<string, double>();

            foreach (string name in gpu_usage_counters.Keys)
            {
                double value = 0.0;
                try
                {
                    value = gpu_usage_counters[name].NextValue();
                }
                catch { }

                if (value > 0.0)
                {
                    int index = name.IndexOf("engtype_");
                    if (index != -1)
                    {
                        string eng_type = "g" + name.Substring(index + 7);
                        if (!totals.ContainsKey(eng_type))
                        {
                            totals[eng_type] = 0.0;
                        }
                        totals[eng_type] += value;
                    }
                }
            }

            return totals;
        }

        public List<NetworkInterface> GetNetworkCounters()
        {
            List<NetworkInterface> list = new List<NetworkInterface>();

            PerformanceCounterCategory interfaces = new PerformanceCounterCategory("Network Interface");
            var interface_names = interfaces.GetInstanceNames();
            foreach (string name in interface_names)
            {
                if (!name.ToLower().Contains("loopback"))
                {
                    NetworkInterface networkInterface = new NetworkInterface();
                    networkInterface.Name = name;
                    networkInterface.BytesInSec = new PerformanceCounter("Network Interface", "Bytes Received/sec", name);
                    networkInterface.BytesOutSec = new PerformanceCounter("Network Interface", "Bytes Sent/sec", name);
                    list.Add(networkInterface);
                }
            }
            return list;
        }

        public Dictionary<string, double> GetTotalNetworkIO(List<NetworkInterface> netCounters)
        {
            double total_in = 0;
            double total_out = 0;
            foreach (NetworkInterface counter in netCounters)
            {
                total_in += counter.BytesInSec.NextValue();
                total_out += counter.BytesOutSec.NextValue();
            }
            Dictionary<string, double> result = new Dictionary<string, double>();
            result.Add("in", total_in);
            result.Add("out", total_out);
            return result;
        }
    }
}
