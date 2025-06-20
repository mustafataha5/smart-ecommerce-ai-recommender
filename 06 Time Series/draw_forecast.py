import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt # Import matplotlib for plotting
from datetime import datetime # Ensure datetime is imported for date operations
import sys


# Assume make_connection_with_db is defined elsewhere or above this function
def make_connection_with_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="wp_ecommerce"
        )
        cursor = connection.cursor(dictionary=True) # Ensure this is dictionary=True
        # print("Database connection established.") # Keep or remove, depending on verbosity needs
        return connection, cursor
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        return None, None





def draw_forecast_from_db() -> pd.DataFrame:
    """
    Retrieves the forecast data from 'custom_forecast_ts' table in the database,
    plots it, and returns the data as a DataFrame.

    Returns:
        pd.DataFrame: DataFrame with 'date' (as index) and 'total' columns.
                      Returns empty DataFrame if data is unavailable or an error occurs.
    """
    connection, cursor = None, None
    forecast_df = pd.DataFrame(columns=['date', 'total'])

    try:
        print("🔗 Connecting to the database...")
        connection, cursor = make_connection_with_db()
        if not connection or not cursor:
            print("❌ Failed to connect to the database.")
            return forecast_df

        print("📥 Fetching forecast data from 'custom_forecast_ts' table...")
        sql_query = "SELECT date, total FROM custom_forecast_ts ORDER BY date;"
        cursor.execute(sql_query)
        results = cursor.fetchall()

        if not results:
            print("⚠️ No forecast data found.")
            return forecast_df

        print(f"✅ Retrieved {len(results)} records.")
        forecast_df = pd.DataFrame(results, columns=['date', 'total'])

        # Convert and clean data
        forecast_df['date'] = pd.to_datetime(forecast_df['date'], errors='coerce')
        forecast_df['total'] = pd.to_numeric(forecast_df['total'], errors='coerce')
        forecast_df.dropna(subset=['date', 'total'], inplace=True)
        forecast_df.set_index('date', inplace=True)

        # Plotting
        if forecast_df.empty:
            print("⚠️ No valid data to plot after cleaning.")
        else:
            plt.figure(figsize=(10, 7))
            plt.plot(forecast_df['total'], marker='o', linestyle='-', label="Forecasted Total")
            plt.title('📈 Forecast from Database')
            plt.xlabel('Date')
            plt.ylabel('Total')
            plt.legend(loc='best')
            plt.grid(True)
            plt.tight_layout()
            plt.show()
            print("📊 Forecast plot displayed successfully.")

    except mysql.connector.Error as err:
        print(f"❌ MySQL error: {err}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        # print("🔒 Database connection closed.")

    return #forecast_df
    
if __name__ == '__main__' : 
    sys.stdout.reconfigure(encoding='utf-8')
    draw_forecast_from_db() 
    