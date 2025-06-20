import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
import mysql.connector


def make_connection_with_db():
    connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="wp_ecommerce")
    cursor = connection.cursor(dictionary=True)
    return connection,cursor 


def get_user_profile():
    """
    Retrieves user profile data (country, age, gender) from wp_users and wp_usermeta tables
    and returns it as a Pandas DataFrame.
    """
    connection = None
    cursor = None
    df = pd.DataFrame(columns=['user_id', 'country', 'age', 'gender'])

    try:
        connection, cursor = make_connection_with_db()

        # Step 1: Get all user IDs from wp_users
        sql_users = "SELECT ID FROM wp_users"
        cursor.execute(sql_users)
        # Fetchall returns a list of dictionaries if dictionary=True is set for cursor
        user_ids_data = cursor.fetchall()

        if not user_ids_data:
            print("No users found in wp_users table.")
            return df # Return empty DataFrame

        # Extract just the IDs into a list
        user_ids = [user['ID'] for user in user_ids_data]

        # Step 2: Get all relevant user metadata in a single query
        # Using a parameterized query for safety and efficiency with IN clause
        placeholders = ', '.join(['%s'] * len(user_ids))
        sql_usermeta = f"""
            SELECT user_id, meta_key, meta_value
            FROM wp_usermeta
            WHERE user_id IN ({placeholders})
            AND meta_key IN ('country', 'age', 'gender');
        """
        cursor.execute(sql_usermeta, tuple(user_ids))
        all_usermeta = cursor.fetchall() # Returns list of dictionaries

        # Step 3: Process the fetched data into a structured format
        # Initialize a dictionary for each user with default None values
        user_profiles = {user_id: {'user_id': user_id, 'country': None, 'age': None, 'gender': None}
                         for user_id in user_ids}

        # Populate the user_profiles dictionary with fetched meta_values
        for row in all_usermeta:
            user_id = row['user_id']
            meta_key = row['meta_key']
            meta_value = row['meta_value']

            if meta_key in user_profiles[user_id]: # Ensure we only store expected keys
                if meta_key == 'age':
                    user_profiles[user_id][meta_key] = int(meta_value)
                else:    
                    user_profiles[user_id][meta_key] = meta_value

        # Step 4: Convert the structured data into a Pandas DataFrame
        df = pd.DataFrame(list(user_profiles.values()))

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        # Optionally, log the error for debugging
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Optionally, log the error for debugging
    finally:
        # Ensure cursor and connection are closed
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return df

if __name__ == '__main__':	
    print(str(get_user_profile()))