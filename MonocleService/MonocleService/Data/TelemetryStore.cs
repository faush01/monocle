using Npgsql;
using NpgsqlTypes;
using System;
using System.Collections.Generic;
using Microsoft.Extensions.Configuration;
using System.Linq;

namespace MonocleService
{
    public class TelemetryStore
    {
        private static TelemetryStore instance = null;
        private static readonly object padlock = new object();

        private string db_server = "";
        private string db_name = "";
        private string db_user = "";
        private string db_password = "";
        private Dictionary<string, DateTime> last_delete_check = new Dictionary<string, DateTime>();
        private Dictionary<string, int> retention = new Dictionary<string, int>();

        public static TelemetryStore GetInstance(IConfiguration config)
        {
            lock (padlock)
            {
                if (instance == null)
                {
                    instance = new TelemetryStore(config);
                }
                return instance;
            }
        }

        private TelemetryStore()
        {

        }

        private TelemetryStore(IConfiguration config)
        {
            db_server = config["DbServer:Host"];
            db_name = config["DbServer:Database"];
            db_user = config["DbServer:User"];
            db_password = config["DbServer:Password"];
            retention = config.GetSection("DbServer:Retention").GetChildren().ToDictionary(x => x.Key, x => int.Parse(x.Value));

            Console.WriteLine("Telemetry Store Created");
            Console.WriteLine("DbServer:Host      ({0})", db_server);
            Console.WriteLine("DbServer:Database  ({0})", db_name);
            Console.WriteLine("DbServer:User      ({0})", db_user);
            Console.WriteLine("DbServer:Password  ({0})", db_password);
            Console.WriteLine("DbServer:Retention ({0})", string.Join("|", retention));
        }

        public void SaveTelemetry(TelemetryData telemetry_data)
        {
            string conn_str_fmt = "Host={0};Username={1};Password={2};Database={3}";

            //string conn_string = "Host=localhost;Username=postgres;Password=admin;Database=postgres";
            string conn_string = String.Format(conn_str_fmt, db_server, db_user, db_password, db_name);

            using (NpgsqlConnection conn = new NpgsqlConnection(conn_string))
            {
                conn.Open();
                NpgsqlBatch batch = new NpgsqlBatch(conn);

                foreach (string table_name in telemetry_data.Keys)
                {
                    CreateTable(table_name, conn);
                    DeleteOld(table_name, conn);

                    string sql = "INSERT INTO " + table_name + 
                        " (event_date, data_type, data) VALUES (@event_date, @data_type, @data)";
                    
                    List<TelemetryItem> telem_items = telemetry_data[table_name];

                    foreach(TelemetryItem telem in telem_items)
                    {
                        NpgsqlBatchCommand batch_cmd = new NpgsqlBatchCommand(sql);

                        DateTime log_date = DateTime.Parse(telem.event_date);
                        batch_cmd.Parameters.AddWithValue("event_date", log_date);
                        batch_cmd.Parameters.AddWithValue("data_type", telem.event_type);
                        batch_cmd.Parameters.AddWithValue("data", NpgsqlDbType.Jsonb, telem.event_data);

                        batch.BatchCommands.Add(batch_cmd);
                    }
                }

                batch.Prepare();
                batch.ExecuteNonQuery();
            }
        }

        private void CreateTable(string table_name, NpgsqlConnection conn)
        {
            string sql_create = "CREATE TABLE IF NOT EXISTS ";
            sql_create += "public." + table_name + " (";
            sql_create += "event_date timestamp with time zone NOT NULL, ";
            sql_create += "data_type character varying(256) COLLATE pg_catalog.default NOT NULL, ";
            sql_create += "data jsonb, ";
            sql_create += "CONSTRAINT " + table_name + "_pkey PRIMARY KEY (event_date, data_type)";
            sql_create += ")";
            using(NpgsqlCommand cmd = new NpgsqlCommand(sql_create, conn))
            {
                cmd.ExecuteNonQuery();
            }
        }

        private void DeleteOld(string table_name, NpgsqlConnection conn)
        {
            if(!retention.ContainsKey(table_name))
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
            Console.WriteLine("Deleting old telemetry for : " + table_name);          

            string sql_delete = "DELETE FROM public." + table_name + 
                " WHERE event_date < now() - INTERVAL '" + keep_days + " DAY'";
            Console.WriteLine(sql_delete);
            using (NpgsqlCommand cmd = new NpgsqlCommand(sql_delete, conn))
            {
                cmd.ExecuteNonQuery();
            }
        }

    }
}
