using Microsoft.AspNetCore.Mvc.Infrastructure;
using Microsoft.Extensions.Configuration;
using MonocleService.Data;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;

namespace MonocleService
{
    public class NetworkInterface
    {
        public string Name { set; get; }
        public PerformanceCounter BytesInSec { set; get; }
        public PerformanceCounter BytesOutSec { set; get; }
    }

    public class SysMonitor
    {
        private bool running = false;
        private IConfiguration configuration;

        public SysMonitor(IConfiguration config)
        {
            configuration = config;
        }

        public void Start()
        {
            if (!running)
            {
                running = true;
                new Thread(new ThreadStart(Run)).Start();
            }
        }

        private List<NetworkInterface> GetNetworkCounters()
        {
            List<NetworkInterface> list = new List<NetworkInterface>();

            PerformanceCounterCategory interfaces = new PerformanceCounterCategory("Network Interface");
            var interface_names = interfaces.GetInstanceNames();
            foreach (string name in interface_names)
            {
                if(!name.ToLower().Contains("loopback"))
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

        private Dictionary<string, double> GetTotalNetworkIO(List<NetworkInterface> netCounters)
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

        private void Run()
        {
            // Get-Counter -ListSet "Memory" | Select -ExpandProperty Counter
            // Get-Counter -Counter "\Memory\Transition Faults/sec" -SampleInterval 5 -MaxSamples 5
            // https://docs.microsoft.com/en-us/previous-versions/ms804008(v=msdn.10)?redirectedfrom=MSDN
            // Pages Input/sec

            TelemetryStoreSqlite store = TelemetryStoreSqlite.GetInstance(configuration);

            //cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total");
            PerformanceCounter cpuCounter = new PerformanceCounter("Processor Information", "% Processor Utility", "_Total");
            PerformanceCounter ramCounter = new PerformanceCounter("Memory", "Available MBytes");
            PerformanceCounter pageFaultsCounter = new PerformanceCounter("Memory", "Pages Input/sec");
            PerformanceCounter disk_read = new PerformanceCounter("PhysicalDisk", "Disk Read Bytes/sec", "_Total");
            PerformanceCounter disk_write = new PerformanceCounter("PhysicalDisk", "Disk Write Bytes/sec", "_Total");
            List<NetworkInterface> netCounters = GetNetworkCounters();

            while (true)
            {
                double cpu = cpuCounter.NextValue();
                double am = ramCounter.NextValue();
                double pfs = pageFaultsCounter.NextValue();
                Dictionary<string, double> network = GetTotalNetworkIO(netCounters);
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

                string line = "";
                line += "cpu(" + cpu + ") ";
                line += "ram(" + am + ") ";
                line += "pfs(" + pfs + ") ";
                line += "net(" + net_in + "," + net_out + ") ";
                line += "disk(" + d_read + "," + d_write + ") ";

                string date_string = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                List<TelemetryItem> tele_items = new List<TelemetryItem>();

                TelemetryItem item = new TelemetryItem();
                item.event_date = date_string;
                item.event_type = "server";
                Dictionary<string, double> event_data = new Dictionary<string, double>();
                event_data.Add("c", cpu);
                event_data.Add("am", am);
                event_data.Add("pfs", pfs);
                event_data.Add("ni", net_in);
                event_data.Add("no", net_out);
                event_data.Add("dr", d_read);
                event_data.Add("dw", d_write);
                item.event_data = event_data;
                tele_items.Add(item);

                TelemetryData data = new TelemetryData();
                data.Add("events", tele_items);

                store.SaveTelemetry(data);

                Console.WriteLine(line);

                Thread.Sleep(60000);
            }

        }
    }
}
