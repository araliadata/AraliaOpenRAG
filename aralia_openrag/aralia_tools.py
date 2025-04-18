import requests
import os, json, base64
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import ast
import numpy as np
from typing import List
from config import setting

plt.rcParams['font.sans-serif'] = ['Noto Sans CJK JP']  # 設定字型
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题




class AraliaTools:
    # https://k-star.araliadata.io/api, https://tw-air.araliadata.io/api
    official_url = 'https://tw-air.araliadata.io/api'  # official

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = self.login()

    def login(self):
        return requests.post(
            "https://xwckbycddv4zlzeslemvhoh6sa0xoxcc.lambda-url.ap-southeast-1.on.aws/",
            json={
                "username": self.username,
                "password": self.password
            }
        ).json().get("data")['accessToken']

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
            self.official_url + "/galaxy/dataset", {
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
                if setting['debug'] == 3:
                    print("# get data", end = "\n\n")
                response = self.post(
                    item['sourceURL'] + "/exploration/" + item['id'] + '?start=' + str(start) + '&pageSize=1000', item)
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

            if "wkt" in x_cols:
                df = df.drop(columns=['value1'])

                # 解析 WKT 座標
                df['coords'] = df['wkt'].apply(lambda x: json.loads(x)['coordinates'])
                df['longitude'] = df['coords'].apply(lambda x: x[0])
                df['latitude'] = df['coords'].apply(lambda x: x[1])

                # 讀取台灣地圖
                taiwan = gpd.read_file('wkt/gadm41_TWN_2.shp')
                
                # 繪製地圖
                fig, ax = plt.subplots(figsize=(10, 12))
                
                # 修正 aspect 錯誤，不使用自動計算 aspect ratio
                taiwan.plot(ax=ax, color='lightgray', edgecolor='black', aspect='equal')

                # 繪製散點，不使用 value1 作為顏色強度
                scatter = ax.scatter(
                    df['longitude'], df['latitude'], 
                    s=50,  # 點的大小
                    c='red', alpha=0.7, edgecolors='black'
                )
                
                # 設定圖表標題和標籤
                plt.title(f"{item['name']}地理分布圖")
                plt.xlabel("經度")
                plt.ylabel("緯度")

                file_name = item['name'] + ".png"
                file_name = file_name.replace("/", "_")
                file_path = os.path.join(folder, file_name)
                plt.savefig(file_path)  # 儲存為圖片檔案               
                plt.close()

                with open(file_path, "rb") as image_file:
                    base64_string = base64.b64encode(image_file.read()).decode('utf-8')  

                item["json_data"] = df.head(400).to_json(force_ascii=False)
                item["image"] = base64_string

            else :
                # png
                df = df.head(30)

                # 根據 x_cols 和 y_cols 的數量選擇適合的圖表類型
                if len(x_cols) == 0:
                    # 沒有 x 軸的情況：直接繪製 y 值的條形圖
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # 使用索引作為 x 軸
                    index = np.arange(len(df))
                    
                    if len(y_cols) == 1:
                        # 單一 y 軸：簡單條形圖
                        ax.bar(index, df[y_cols[0]], width=0.75, label=y_cols[0])
                        ax.set_xticks(index)
                        ax.set_xticklabels(df.index, rotation=45, ha='right')
                    else:
                        # 多個 y 軸：分組條形圖
                        # 防止 y_cols 為空列表導致除以零錯誤
                        if len(y_cols) > 0:
                            width = 0.75 / len(y_cols)  # 調整寬度以適應多個 y 值
                            
                            for i, y_col in enumerate(y_cols):
                                ax.bar(index + (i - len(y_cols) / 2 + 0.5) * width,
                                    df[y_cols[i]], width, label=y_cols[i])
                            
                            # 設置 x 軸刻度
                            ax.set_xticks(index)
                            ax.set_xticklabels(df.index, rotation=45, ha='right')
                        else:
                            # 如果 y_cols 為空，顯示空圖表
                            ax.text(0.5, 0.5, '沒有可用的 Y 軸數據', 
                                   horizontalalignment='center', verticalalignment='center',
                                   transform=ax.transAxes)
                    
                    ax.set_xlabel('索引')
                    ax.set_ylabel(','.join(y_cols))
                    
                elif len(x_cols) == 1:
                    # 單一 x 軸情況
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    if len(y_cols) == 1:
                        # 單一 x 軸和單一 y 軸：簡單條形圖
                        # 檢查 x 軸數據是否為數值型，如果不是則使用索引
                        try:
                            # 嘗試將 x 軸數據轉換為數值型
                            x_values = pd.to_numeric(df[x_cols[0]])
                            ax.bar(x_values, df[y_cols[0]], width=0.75, label=y_cols[0])
                        except (ValueError, TypeError):
                            # 如果轉換失敗（例如字符串數據），使用索引作為 x 軸位置
                            x = np.arange(len(df))
                            ax.bar(x, df[y_cols[0]], width=0.75, label=y_cols[0])
                            ax.set_xticks(x)
                            ax.set_xticklabels(df[x_cols[0]], rotation=45, ha='right')
                    else:
                        # 單一 x 軸和多個 y 軸：分組條形圖
                        x = np.arange(len(df))
                        # 防止 y_cols 為空列表導致除以零錯誤
                        if len(y_cols) > 0:
                            # 確保 y_cols 長度不為零，避免除以零錯誤
                            width = 0.75 / max(1, len(y_cols))  # 使用 max 確保分母至少為 1
                            
                            for i, y_col in enumerate(y_cols):
                                # 計算偏移量時也防止除以零
                                offset = 0 if len(y_cols) <= 1 else (i - len(y_cols) / 2 + 0.5) * width
                                ax.bar(x + offset, df[y_cols[i]], width, label=y_cols[i])
                            
                            # 設置 x 軸刻度
                            ax.set_xticks(x)
                            ax.set_xticklabels(df[x_cols[0]], rotation=45, ha='right')
                        else:
                            # 如果 y_cols 為空，顯示空圖表
                            ax.text(0.5, 0.5, '沒有可用的 Y 軸數據', 
                                   horizontalalignment='center', verticalalignment='center',
                                   transform=ax.transAxes)
                elif len(x_cols) == 2:
                    # 雙 x 軸情況：散點圖
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # 確保有 y_cols 數據
                    if len(y_cols) > 0:
                        for y_col in y_cols:
                            scatter = ax.scatter(df[x_cols[0]], df[x_cols[1]], 
                                                c=df[y_col], cmap='viridis', 
                                                s=50, alpha=0.7, label=y_col)
                            plt.colorbar(scatter, label=y_col)
                    else:
                        # 如果沒有 y_cols，使用默認顏色
                        scatter = ax.scatter(df[x_cols[0]], df[x_cols[1]], 
                                            s=50, alpha=0.7)
                    
                    ax.set_xlabel(x_cols[0])
                    ax.set_ylabel(x_cols[1])
                
                else:  # len(x_cols) == 3
                    # 三 x 軸情況：3D 散點圖
                    fig = plt.figure(figsize=(10, 8))
                    ax = fig.add_subplot(111, projection='3d')
                    
                    # 確保有 y_cols 數據
                    if len(y_cols) > 0:
                        for y_col in y_cols:
                            scatter = ax.scatter(df[x_cols[0]], df[x_cols[1]], df[x_cols[2]],
                                               c=df[y_col], cmap='plasma', 
                                               s=50, alpha=0.7, label=y_col)
                            plt.colorbar(scatter, label=y_col)
                    else:
                        # 如果沒有 y_cols，使用默認顏色
                        scatter = ax.scatter(df[x_cols[0]], df[x_cols[1]], df[x_cols[2]],
                                           s=50, alpha=0.7)
                    
                    ax.set_xlabel(x_cols[0])
                    ax.set_ylabel(x_cols[1])
                    ax.set_zlabel(x_cols[2])
                
                # 設定標題與標籤
                ax.set_title(item['name'])
                if len(x_cols) == 1:
                    ax.set_xlabel(x_cols[0])
                    ax.set_ylabel(','.join(y_cols))
                
                # 顯示圖例（只有在有標籤時才顯示）
                if len(y_cols) > 0:
                    ax.legend()
                # 顯示圖表
                plt.tight_layout()
                file_name = item['name'] + ".png"
                file_name = file_name.replace("/", "_")
                file_path = os.path.join(folder, file_name)
                plt.savefig(file_path)  # 儲存為圖片檔案
                plt.close()  # 關閉圖表以釋放記憶體

                with open(file_path, "rb") as image_file:
                    base64_string = base64.b64encode(image_file.read()).decode('utf-8')  

                item["json_data"] = df.to_json(force_ascii=False)
                item["image"] = base64_string

            if setting['debug'] == 3:
                print("已生成圖片與表格", end = "\n\n")

            