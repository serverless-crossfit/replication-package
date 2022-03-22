import logging
import json
import pandas as pd
import requests
from datetime import datetime, timezone

class AzureTraceDownloader:
    """Implements get_traces(self) to download Microsoft Azure Insights traces using
    TODO(specify which library):
    TODO(Add doc links to 'best' Azure docs)
    """

    def __init__(self, spec) -> None:
        self.spec = spec

    def get_traces(self):
        """Retrieves Azure Insights traces from the last invocation.
        """

        start, end = self.spec.event_log.get_invoke_timespan()
        log_path = self.spec.logs_directory()

        trace_ids_file = log_path.joinpath('trace_ids.txt')
        trace_file = log_path.joinpath('traces.json')

        start_time = datetime.fromtimestamp(datetime.timestamp(start), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        end_time = datetime.fromtimestamp(datetime.timestamp(end), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        trace_ids = self.retrieve_trace_ids(start_time, end_time, trace_ids_file)
        self.retrieve_traces(start_time, trace_ids, trace_file)

        num_traces = len(trace_ids)

        # Inform user
        logging.info(f"Downloaded {num_traces} traces for invocations between \
{start} and {end} into {log_path}.")

    def get_query_result_json(self, ai_api_query):
        ai_api_version = 'v1'
        ai_api_app_id = self.spec['application_id']
        ai_api_key = self.spec['api_key']
        ai_api_time_span = 'P7D'
        api_url = f"https://api.applicationinsights.io/{ai_api_version}/apps/{ai_api_app_id}/query?timespan={ai_api_time_span}&query={ai_api_query}"
        headers =  { "x-api-key" : ai_api_key }
        response = requests.get(api_url, headers=headers)
        data = response.json()

        return data

    def retrieve_trace_ids(self, start, end, trace_ids_file):
        ai_api_query = f"""
            requests
                | where timestamp >= datetime({start}) and timestamp <= datetime({end}) and name == "Upload" and resultCode == "200"
                | distinct operation_Id
            """
        data = self.get_query_result_json(ai_api_query)
        rows = data['tables'][0]['rows']

        trace_ids = []
        with open(trace_ids_file, "w") as txt_file:
            for line in rows:
                trace_ids.append(line[0])
                txt_file.write(" ".join(line) + "\n")

        txt_file.close()
        return trace_ids

    def retrieve_traces(self, start_time, trace_ids, trace_file):
        # Clear traces data
        open(trace_file, 'w').close()

        for operation_Id in trace_ids:
            try:
                print(f"> Downloading traces for {operation_Id}")
                # Get CreateThumbnail and Upload requests data
                query1 = f"""
                    union requests
                    | where timestamp >= datetime({start_time}) and itemType == "request"
                        and (operation_Id == "{operation_Id}" or customDimensions contains "{operation_Id}")
                    """

                result_query1 = self.get_query_result_json(query1)
                columns_query1 = [x['name'] for x in result_query1['tables'][0]['columns']]
                rows_query1 = result_query1['tables'][0]['rows']
                df_query1 = pd.DataFrame(rows_query1, columns=columns_query1)

                # Extract CreateThumbnail and Upload timestamp
                create_thumbnail_timestamp= df_query1.loc[(df_query1["itemType"]=="request") & (df_query1["name"]=="Create-Thumbnail"), "timestamp"].values[0]
                upload_timestamp= df_query1.loc[(df_query1["itemType"]=="request") & (df_query1["name"]=="Upload"), "timestamp"].values[0]

                # Final query for all relevant data
                ai_api_query = f"""
                    union requests,dependencies,traces,customEvents
                    | where timestamp >=  datetime({start_time}) and ( operation_Id == "{operation_Id}" or customDimensions contains "{operation_Id}"
                        or (customDimensions contains "Host initialization" and timestamp >=  datetime({upload_timestamp}) and timestamp <= datetime({create_thumbnail_timestamp})) )
                    """
                data = self.get_query_result_json(ai_api_query)
                columns = [x['name'] for x in data['tables'][0]['columns']]
                rows = data['tables'][0]['rows']
                df = pd.DataFrame(rows, columns=columns)

                newjson = {}
                newjson['trace_id'] = operation_Id
                newjson['traces'] = df.to_json(orient='records')

                with open(trace_file, 'a') as f:
                    json.dump(newjson, f)
                    f.write('\n')

                f.close()
            except:
                print("Failed to download trace for " + operation_Id)
