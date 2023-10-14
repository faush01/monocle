using Microsoft.Data.Sqlite;
using Microsoft.Extensions.Configuration;
using System.Collections.Generic;
using System;
using System.Linq;
using System.Text.Json;
using System.IO;

namespace MonocleService.Data
{
    public class TelemetryStoreSqlite
    {
        private static TelemetryStoreSqlite instance = null;
        private static readonly object padlock = new object();

        private string db_file_path = "";
        private Dictionary<string, DateTime> last_delete_check = new Dictionary<string, DateTime>();

        private TelemetryStoreSqlite() { }

        public static TelemetryStoreSqlite GetInstance(IConfiguration config)
        {
            lock (padlock)
            {
                if (instance == null)
                {
                    instance = new TelemetryStoreSqlite(config);
                }
                return instance;
            }
        }

        private TelemetryStoreSqlite(IConfiguration config)
        {
            db_file_path = config["DbServer:DbFilePath"];

            Console.WriteLine("Telemetry Store Created");
            Console.WriteLine("DbServer:DbFilePath : {0}", db_file_path);

            DirectoryInfo di = new DirectoryInfo(db_file_path);
            if(!di.Exists)
            {
                di.Create();
            }
        }

        private void VacuumDatabase(string db_file_name)
        {
            FileInfo fi = new FileInfo(db_file_name);
            Console.WriteLine("DB file size : " + fi.Length);

            using (SqliteConnection conn = new SqliteConnection("Data Source=" + db_file_name))
            {
                conn.Open();
                // vacuum
                Console.WriteLine("Running DB Vacuum");
                string vacuum_cmd = "VACUUM";
                using (SqliteCommand cmd = new SqliteCommand(vacuum_cmd, conn))
                {
                    cmd.ExecuteNonQuery();
                }
            }

            fi = new FileInfo(db_file_name);
            Console.WriteLine("DB file size : " + fi.Length);
        }

        public void SaveTelemetry(TelemetryData telemetry_data)
        {
            // https://learn.microsoft.com/en-us/dotnet/standard/data/sqlite/?tabs=netcore-cli
            // select json_extract(data, '$.am') as am from events

            try
            {
                lock (padlock)
                {
                    foreach (string db_name in telemetry_data.Keys)
                    {
                        string db_file_name = "";
                        if (db_name.EndsWith(".sqlite"))
                            db_file_name = Path.Combine(db_file_path, db_name);
                        else
                            db_file_name = Path.Combine(db_file_path, db_name + ".sqlite");
                        DeleteOld(db_file_name);

                        using (SqliteConnection conn = new SqliteConnection("Data Source=" + db_file_name))
                        {
                            conn.Open();

                            CreateTable("telemetry", conn);
                            
                            string sql = "";
                            sql += "INSERT INTO telemetry ";
                            sql += "(event_date, data_type, data) ";
                            sql += "VALUES (@event_date, @data_type, @data)";

                            List<TelemetryItem> telem_items = telemetry_data[db_name];

                            foreach (TelemetryItem telem in telem_items)
                            {
                                DateTime log_date = DateTime.Now;
                                if (!string.IsNullOrEmpty(telem.event_date))
                                {
                                    log_date = DateTime.Parse(telem.event_date);
                                }
                                log_date = log_date.ToUniversalTime();
                                //"2006-01-02T15:04:05+07:00"
                                //string event_date = log_date_string = log_date.ToString("yyyy-MM-ddTHH:mm:sszzz");
                                long event_date = (long)log_date.Subtract(new DateTime(1970, 1, 1)).TotalSeconds;

                                using (SqliteCommand cmd = new SqliteCommand(sql, conn))
                                {
                                    cmd.Parameters.AddWithValue("event_date", event_date);
                                    cmd.Parameters.AddWithValue("data_type", telem.event_type);
                                    cmd.Parameters.AddWithValue("data", Dic2Json(telem.event_data));
                                    cmd.ExecuteNonQuery();
                                }
                            }
                        }
                    }
                    string data_json = JsonSerializer.Serialize(telemetry_data);
                    Console.WriteLine(DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "|" + data_json);
                }
            }
            catch(Exception e)
            {
                Console.WriteLine(e.Message);
            }
        }

        private string Dic2Json(Dictionary<string, double> event_data)
        {
            List<string> data_items = new List<string>();
            foreach (var kvp in event_data)
            {
                data_items.Add("\"" + kvp.Key + "\":" + Math.Round(kvp.Value, 4));
            }
            string json_string = "{" + string.Join(",", data_items) + "}";
            //Console.WriteLine(json_string);
            return json_string;
        }

        private void CreateTable(string table_name, SqliteConnection conn)
        {
            string sql_create = "";
            sql_create += "CREATE TABLE IF NOT EXISTS " + table_name + " (";
            sql_create += "event_date int NOT NULL, ";
            sql_create += "data_type text NOT NULL, ";
            sql_create += "data text, ";
            sql_create += "PRIMARY KEY (event_date, data_type)";
            sql_create += ")";
            using (SqliteCommand cmd = new SqliteCommand(sql_create, conn))
            {
                cmd.ExecuteNonQuery();
            }
        }

        private void DeleteOld(string db_file_name)
        {
            int keep_days = 14;

            FileInfo fi = new FileInfo(db_file_name);
            if (!fi.Exists) return;

            // remove old content every 24 hours
            if (!last_delete_check.ContainsKey(db_file_name))
            {
                last_delete_check[db_file_name] = DateTime.MinValue;
            }
            DateTime last_check = last_delete_check[db_file_name];
            if (last_check > DateTime.Now.AddDays(-1))
            {
                return;
            }

            last_delete_check[db_file_name] = DateTime.Now;
            DateTime cutoff = DateTime.UtcNow.AddDays(keep_days * -1);
            Console.WriteLine("Deleting old telemetry data");
            Console.WriteLine("Older than : " + cutoff.ToString("yyyy-MM-ddTHH:mm:sszzz"));
            Console.WriteLine("From       : " + db_file_name);
            //string cut_date = cutoff.ToString("yyyy-MM-ddTHH:mm:sszzz");
            long cut_date = (long)cutoff.Subtract(new DateTime(1970, 1, 1)).TotalSeconds;
            string sql_delete = "DELETE FROM telemetry WHERE event_date < " + cut_date;
            Console.WriteLine(sql_delete);

            using (SqliteConnection conn = new SqliteConnection("Data Source=" + db_file_name))
            {
                conn.Open();
                using (SqliteCommand cmd = new SqliteCommand(sql_delete, conn))
                {
                    cmd.ExecuteNonQuery();
                }
            }

            VacuumDatabase(db_file_name);
        }
    }
}
