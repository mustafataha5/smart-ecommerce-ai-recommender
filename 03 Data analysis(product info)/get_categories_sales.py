import pandas as pd 
import numpy as np 
import mysql.connector


def make_connection_with_db():
    connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="wp_ecommerce")
    cursor = connection.cursor(dictionary=True)
    return connection,cursor 

def get_categories_sales(): 
    connection,cursor  = make_connection_with_db()
   
    try:
        connection, cursor = make_connection_with_db()

        # Step 1: Get all prodcut sumsales [term_id,name,sumsales]
        sql = """ 
            select wp_term_taxonomy.term_id as category_id ,wp_terms.name as category_name, sum(wp_wc_order_product_lookup.product_qty) as sales
            from wp_wc_order_product_lookup 
            join wp_term_relationships on wp_wc_order_product_lookup.product_id = wp_term_relationships.object_id 
            join wp_term_taxonomy on wp_term_taxonomy.term_taxonomy_id = wp_term_relationships.term_taxonomy_id
            join wp_terms on wp_term_taxonomy.term_id = wp_terms.term_id 
            where wp_term_taxonomy.taxonomy = 'product_cat'
            GROUP By wp_term_taxonomy.term_id
        """
        cursor.execute(sql)
        categories_data = cursor.fetchall()
        # print(categories_data)
        if not categories_data:
            print("No Category found .")
            return df # Return empty DataFrame

        df = pd.DataFrame(columns=['category_id', 'category_name', 'sales'])
        categoies_info = [ row for row in categories_data ]      
        df = pd.DataFrame(categoies_info)
        # Ensure data types are correct if not already handled by cursor(dictionary=True)
        df['category_id'] = df['category_id'].astype(int)
        df['sales'] = df['sales'].astype(int)
        # for row in categories_data:
        #     category_id = int(row['category_id'])
        #     category_name= row['category_name']
        #     sales = int(row['sales'])

        #     category_obj = {'category_id':category_id, 'category_name':category_name, 'sales':sales}
        #     category - pd.DataFrame(category_obj)
        #     df=pd.concat([df,category],ignore_index=True)
           
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
