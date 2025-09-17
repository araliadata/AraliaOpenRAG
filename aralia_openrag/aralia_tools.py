import requests
import os, json, base64
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import ast
import numpy as np
from typing import List

plt.rcParams['font.sans-serif'] = ['Noto Sans CJK JP']  # 設定字型
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题




class AraliaTools:
    # https://tw-air.araliadata.io
    
    def __init__(self, sso_url=None, client_id=None, client_secret=None, stellar_url=None):
        self.sso_url = sso_url
        self.stellar_url = stellar_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self.login()

    def login(self):
        response = requests.post(
            f"{self.sso_url.rstrip('/')}/realms/stellar/protocol/openid-connect/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def get(self, url, query={}):
        """
        Sends a GET request with an Authorization Bearer token and retrieves the response.

        Args:
            token (str): 
            url (str): Endpoint to send the GET request to, appended to the base URL.
            query (dict, optional): Query parameters to include in the GET request. Defaults to an empty dictionary.

        Returns:
            dict or list: Parsed response based on `allData` and response structure.
        """

        for attempt in range(2):
            # Define the Authorization header
            headers = {"Authorization": f"Bearer {self.token}"}

            # Send the GET request
            response = requests.get(url, headers=headers, params=query)

            if response.status_code == 200:
                break
            else:
                self.login()

        data = response.json().get("data")

        return data.get("list", data)

    def post(self, url, query={}):

        """
        Sends a POST request with an Authorization Bearer token and retrieves the response.

        Args:
            token (str): 
            url (str): Endpoint to send the GET request to, appended to the base URL.
            query (dict, optional): Query parameters to include in the GET request. Defaults to an empty dictionary.

        Returns:
            dict or list: Parsed response based on `allData` and response structure.
        """

        for attempt in range(2):
            # Define the Authorization header
            headers = {"Authorization": f"Bearer {self.token}"}

            # Send the POST request
            response = requests.post(url, headers=headers, json=query)

            if response.status_code == 200:
                break
            else:
                self.login()

        data = response.json().get("data")

        return data.get("list", data)

    def parseExploration(self, df, x_labels=None, value_labels=None):
        """
        Parses a DataFrame to flatten arrays in the `x` and `values` columns, creating new columns for each array element.

        Args:
            df (pd.DataFrame): Input DataFrame with `x` and `values` columns.
            x_labels (list, optional): Custom column names for the flattened `x` values.
            value_labels (list, optional): Custom column names for the flattened `values`.

        Returns:
            pd.DataFrame: Parsed DataFrame with flattened and renamed columns.
        """
        # Initialize lists to store parsed column data
        x_columns = []
        value_columns = []

        # Process each row of the DataFrame
        for _, row in df.iterrows():
            # Extract and flatten `x` values
            combined_x = [item[0] for item in row['x']]
            x_columns.append(combined_x)

            # Add `values` array directly
            value_columns.append(row['values'])

        # Create DataFrames for flattened `x` and `values`
        x_df = pd.DataFrame(
            x_columns,
            columns=x_labels if x_labels and len(x_labels) == len(x_columns[0]) else [
                f"x{i+1}" for i in range(len(x_columns[0]))]
        )
        values_df = pd.DataFrame(value_columns)
        values_df.columns = value_labels if value_labels and len(
            value_labels) == values_df.shape[1] else [f"value{i+1}" for i in range(values_df.shape[1])]

        # Concatenate the original and parsed DataFrames
        result_df = pd.concat([x_df, values_df], axis=1)

        return result_df

    def search_tool(self, question: str):
        response = self.get(
            self.stellar_url + "/api/galaxy/dataset", {
                "keyword": question,
                "pageSize": 50
            }
        )

        for item in response:
            item.pop("sourceType")
            item['sourceURL'], _, _ = item['sourceURL'].partition('/admin')

        return {item['id']: item for item in response}

    def column_metadata_tool(self, datasets: List[any]):
        for dataset in datasets:
            if column_metadata := self.get(
                f"{dataset['sourceURL']}/api/dataset/{dataset['id']}"
            ):
                cols_exclude = ["id", "name", "datasetID", "visible",
                                "ordinalPosition", "sortingSettingID"]
                virtual_exclude = ["id", "name", "datasetID", "visible",
                                   "setting", "sourceType", "language", "country"]

                dataset["columns"] = {
                    column['id']: {
                        **{"columnID": column["id"]},
                        **{k: v for k, v in column.items() 
                            if k not in cols_exclude}
                    }
                    for column in column_metadata["columns"]
                    if column["type"] != "undefined" and column["visible"]
                }

                if virtual_vars := self.get(
                    f"{dataset['sourceURL']}/api/dataset/{dataset['id']}/virtual-variables"
                ):
                    dataset["columns"].update({
                        var['id']: {
                            "columnID": var["id"],
                            **{k: v for k, v in var.items() 
                            if k not in virtual_exclude}
                        }
                        for var in virtual_vars
                    })

        return {dataset['id']: dataset for dataset in datasets if "columns" in dataset}

    def filter_option_tool(self, datasets: List):
        for dataset in datasets:
            for filter_column in dataset['filter']:
                response = self.post(
                    dataset['sourceURL'] + "/api/exploration/" + dataset['id'] + '/filter-options?start=0&pageSize=1000', 
                    {
                        "x":[
                            filter_column
                        ]
                    }
                )
                filter_column['values'] = [item['x'][0][0] for item in response]
                

    def explore_tool(self, charts: List):
        for item in charts:
            start = 0
            total_response = []
            while True:
                response = self.post(
                    item['sourceURL'] + "/api/exploration/" + item['id'] + '?start=' + str(start) + '&pageSize=1000', item)
                total_response.extend(response)
                break
                # if len(response) == 1000:
                #     if start > 5000:
                #         break
                #     else:
                #         start += 1000
                # else:
                #     break

            x_cols = []
            for x_axis in item['x']:
                x_cols.append(x_axis['displayName'])

            y_cols = []
            for y_axis in item['y']:
                y_cols.append(y_axis['displayName'])

            df = self.parseExploration(
                pd.DataFrame(total_response), x_cols, y_cols)

            folder = "csv_img"
            os.makedirs(folder, exist_ok=True)

            file_name = item['name'] + ".csv"
            file_name = file_name.replace("/", "_")
            file_path = os.path.join(folder, file_name)

            df.to_csv(file_path,
                      index=False, encoding="utf-8-sig")

            item["json_data"] = df.head(400).to_json(force_ascii=False)

def landmark_tool(landmark_url, secret_key):
    """
    Retrieve landmark metadata and chart data from Aralia’s Landmark API via a Landmark share-link URL.

    This function locates the “share-link” segment in the provided URL, trims it to the base API
    endpoint, and issues two GET requests: one for metadata and one for up to 300 chart data points.
    It then filters and structures the combined result into a single dictionary.

    Parameters
    ----------
    landmark_url : str
        The full Aralia Landmark share-link URL (must contain “share-link”).
    secret_key : str
        The user’s Planet API key, sent as the Authorization header.

    Returns
    -------
    dict
        A dictionary with the following keys:
        
        - name (str): The landmark’s name.
        - chart_columns (list of str): Column names from the metadata.
        - chart_data (list of dict): A list of up to 300 data points, each containing only
        the keys 'x0', 'x1', 'x2', 'y0', 'y1'.

    """
    start_index = landmark_url.rfind('share-link')

    if start_index == -1:
        raise ValueError("Invalid Share Link URL: Please copy and paste the totality of the Landmark URL share link.")

    landmark_url = landmark_url[:start_index + 33]

    headers = {
        'Authorization': secret_key
    }

    # get metadata
    response = requests.request("GET", landmark_url + "/metadata", headers=headers)

    metadata = response.json()['data']

    # get chart data
    response = requests.request("GET", landmark_url + "/chart-data?pageSize=300", headers=headers)

    chart_data = response.json()['data']['list']

    chart = {
        'name': metadata['name'],
        'chart_columns': metadata['dataColumns'],
        'chart_data': [
            {k: v for k, v in item.items() if k in {'x0', 'x1', 'x2', 'y0', 'y1'}}
            for item in chart_data
        ]
    }

    return chart