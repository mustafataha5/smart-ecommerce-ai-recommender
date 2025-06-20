import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import seaborn as sns

import plotly.express as px 
from statsmodels.tsa.seasonal import seasonal_decompose
from autots import AutoTS
import time 
from datetime import datetime 
from datetime import timedelta 

def make_connection_with_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="wp_ecommerce"
        )
        cursor = connection.cursor(dictionary=True)
        print("Database connection established.")
        return connection, cursor
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        return None, None

def get_daily_sales_between_2_dates(start_date, end_date):
    connection, cursor = None, None
    df = pd.DataFrame(columns=['date', 'total']) # Initialize with desired columns

    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            print("Database connection failed. Cannot proceed.")
            return df

        sql = """
            SELECT
                LEFT(order_t.date_created, 10) AS date,
                SUM(order_t.product_net_revenue) AS total  -- Give an alias to the sum column
            FROM `wp_wc_order_product_lookup` order_t
            WHERE order_t.date_created BETWEEN %s AND %s
            GROUP BY date
            ORDER BY `date` ASC
        """
        cursor.execute(sql, (start_date, end_date,))
        results = cursor.fetchall()

        if results:
            # Directly create a DataFrame from the list of dictionaries
            df = pd.DataFrame(results)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return df        
        
        
def get_sales_of_last_date(): 
    from datetime import datetime 
    connection, cursor = None, None
    last_date = datetime.today() 
    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            print("Database connection failed. Cannot proceed.")
            return df

        sql = """
            SELECT LEFT(max(order_t.date_created), 10) AS last_date
            FROM `wp_wc_order_product_lookup` order_t
        """
        cursor.execute(sql, )
        results = cursor.fetchall()

        if results:
            # Directly create a DataFrame from the list of dictionaries
            date = results[0]['last_date']
            last_date = datetime.strptime(date,'%Y-%m-%d')

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return last_date        
        
def save_forecast_in_db(forecast):
    connection, cursor = None, None
    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            print("Database connection failed. Cannot proceed with saving forecast.")
            return False # Return False to indicate failure

        # --- Drop and Create Table ---
        # Corrected table name and DATETIME type
        print("Dropping existing table (if any) and creating new table...")
        cursor.execute("DROP TABLE IF EXISTS custom_forecast_ts;")
        connection.commit()

        create_table_sql = """
        CREATE TABLE custom_forecast_ts (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            date DATETIME NOT NULL,
            total FLOAT NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_table_sql)
        connection.commit()
        print("Table 'custom_forecast_ts' created successfully.")

        # --- Prepare data for executemany ---
        # forecast DataFrame has date as index, 'total' as column
        # Use iterrows() to get (index (date), row_series)
        data_to_insert = []
        for date_index, row_series in forecast.iterrows():
            # date_index is already a Timestamp object (datetime-like)
            # You can directly use it or format it
            formatted_date = date_index.strftime('%Y-%m-%d %H:%M:%S') # Or just '%Y-%m-%d' if no time needed
            total_value = float(row_series['total'])
            data_to_insert.append((formatted_date, total_value))

        # --- Insert data using executemany for efficiency ---
        if data_to_insert:
            print(f"Inserting {len(data_to_insert)} forecast records...")
            insert_sql = "INSERT INTO custom_forecast_ts (date, total) VALUES (%s, %s);"
            cursor.executemany(insert_sql, data_to_insert)
            connection.commit()
            print("Forecast data saved successfully.")
        else:
            print("No forecast data to insert.")

        return True # Return True to indicate success

    except mysql.connector.Error as err:
        print(f"Database error while saving forecast: {err}")
        return False
    except Exception as e:
        print(f"Unexpected error while saving forecast: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        