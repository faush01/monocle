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

        private string db_file_name = "";
        private Dictionary<string, DateTime> last_delete_check = new Dictionary<string, DateTime>();
        private Dictionary<string, int> retention = new Dictionary<string, int>();

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
            db_file_name = config["DbServer:DbFileName"];
            retention = config.GetSection("DbServer:Retention").GetChildren().ToDictionary(x => x.Key, x => int.Parse(x.Value));

            Console.WriteLine("Telemetry Store Created");
            Console.WriteLine("DbServer:DbFileName   ({0})", db_file_name);
            Console.WriteLine("DbServer:Retention    ({0})", string.Join("|", retention));

            VacuumDatabase();
        }

        private void VacuumDatabase()
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
                    string data_json = JsonSerializer.Serialize(telemetry_data);
                    Console.WriteLine(DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "|" + data_json);

                    using (SqliteConnection conn = new SqliteConnection("Data Source=" + db_file_name))
                    {
                        conn.Open();

                        foreach (string table_name in telemetry_data.Keys)
                        {
                            CreateTable(table_name, conn);
                            DeleteOld(table_name, conn);

                            string sql = "";
                            sql += "INSERT INTO " + table_name + " ";
                            sql += "(event_date, data_type, data) ";
                            sql += "VALUES (@event_date, @data_type, @data)";

                            List<TelemetryItem> telem_items = telemetry_data[table_name];

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
            //sql_create += "event_date text NOT NULL, ";
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

        private void DeleteOld(string table_name, SqliteConnection conn)
        {
            if (!retention.ContainsKey(table_name))
            {
                return;
            }
            int keep_days = retention[table_name];

            // remove old content every 24 hours
            if (!last_delete_check.ContainsKey(table_name))
            {
                last_delete_check[table_name] = DateTime.MinValue;
            }
            DateTime last_check = last_delete_check[table_name];
            if (last_check > DateTime.Now.AddDays(-1))
            {
                return;
            }

            last_delete_check[table_name] = DateTime.Now;
            DateTime cutoff = DateTime.UtcNow.AddDays(keep_days * -1);
            Console.WriteLine("Deleting old telemetry in table (" + table_name + ") older than (" + cutoff.ToString("yyyy-MM-ddTHH:mm:sszzz") + ")");
            //string cut_date = cutoff.ToString("yyyy-MM-ddTHH:mm:sszzz");
            long cut_date = (long)cutoff.Subtract(new DateTime(1970, 1, 1)).TotalSeconds;
            string sql_delete = "DELETE FROM " + table_name + " WHERE event_date < " + cut_date;
            Console.WriteLine(sql_delete);
            using (SqliteCommand cmd = new SqliteCommand(sql_delete, conn))
            {
                cmd.ExecuteNonQuery();
            }
        }
    }
}
