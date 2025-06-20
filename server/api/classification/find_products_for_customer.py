import pandas as pd
import mysql.connector
import logging
import pickle
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============ Logging Setup ============
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ============ Database Connection ============
def make_connection_with_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="wp_ecommerce"
        )
        cursor = connection.cursor(dictionary=True)
        logging.info("Database connection established.")
        return connection, cursor
    except mysql.connector.Error as err:
        logging.error(f"Database connection failed: {err}")
        return None, None

# ============ Helper Functions ============

def category_best_seller_produtcts(category_id, n=3):
    connection, cursor = None, None
    products_ids = "Not Found"
    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            logging.error("Database connection failed. Cannot proceed.")
            return products_ids

        sql = """
        SELECT wt.term_id, wwopl.product_id, SUM(wwopl.product_qty) as sumsales 
        FROM wp_wc_order_product_lookup wwopl
        JOIN wp_term_relationships wtr ON wtr.object_id = wwopl.product_id 
        JOIN wp_term_taxonomy wtt ON wtt.term_taxonomy_id = wtr.term_taxonomy_id 
        JOIN wp_terms wt ON wt.term_id = wtt.term_id 
        WHERE wtt.taxonomy = 'product_cat' AND wtt.term_id = %s
        GROUP BY wt.term_id, wwopl.product_id 
        ORDER BY sumsales DESC;
        """
        cursor.execute(sql, (category_id,))
        results = cursor.fetchall()
        if results:
            products_ids = pd.DataFrame(results[:n])

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return products_ids

def get_product_name_from_id(product_id):
    product_name = 'Not Found'
    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            logging.error("Database connection failed.")
            return product_name

        sql = 'SELECT post_title as product_title FROM wp_posts WHERE ID = %s;'
        cursor.execute(sql, (product_id,))
        results = cursor.fetchall()
        if results:
            product_name = results[0]['product_title']

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}. Product ID: {product_id}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}. Product ID: {product_id}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return product_name

def get_gender_code(gender):
    gender_code = 'Not Found'
    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            logging.error("Database connection failed.")
            return gender_code

        gender = gender.lower()
        if gender == 'male':
            gender = 'ذكر'
        elif gender == 'female':
            gender = 'انثى'

        sql = 'SELECT code FROM custom_gender_code WHERE gender = %s;'
        cursor.execute(sql, (gender,))
        results = cursor.fetchall()
        if results:
            gender_code = results[0]['code']

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}. Gender: {gender}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}. Gender: {gender}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return gender_code

def get_country_code(country):
    country_code = 'Not Found'
    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            logging.error("Database connection failed.")
            return country_code

        country = country.upper()
        sql = 'SELECT code FROM custom_country_code WHERE country = %s;'
        cursor.execute(sql, (country,))
        results = cursor.fetchall()
        if results:
            country_code = results[0]['code']

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}. Country: {country}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}. Country: {country}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return country_code

def get_category_code(filename, country, age, gender): 
    
    

    try:
        # Load the pickled model
        with open(filename, 'rb') as file:
            loaded_model = pickle.load(file)

        # Create input DataFrame with expected feature names
        input_df = pd.DataFrame([{
            'country': country,
            'age': age,
            'gender': gender
        }])

        # Predict category
        prediction = loaded_model.predict(input_df)

        return prediction[0]

    except FileNotFoundError:
        print(f"❌ Model file '{filename}' not found.")
        return 'Not Found'
    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        return 'Not Found'
    

# ============ Main Recommendation Function ============

def get_customer_products(customer_id, n=3):
    products = []
    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            logging.error("Database connection failed.")
            return products

        # Get user_id and country
        sql = 'SELECT user_id, country FROM wp_wc_customer_lookup WHERE customer_id = %s;'
        cursor.execute(sql, (customer_id,))
        results = cursor.fetchall()

        if not results:
            logging.warning(f"No customer found with ID: {customer_id}")
            return products

        user_id = results[0]['user_id']
        country = results[0]['country']
        country_code = get_country_code(country)

        # Get age
        sql = 'SELECT meta_value FROM wp_usermeta WHERE user_id = %s AND meta_key = "age";'
        cursor.execute(sql, (user_id,))
        age_result = cursor.fetchall()
        age = int(age_result[0]['meta_value']) if age_result else 0

        # Get gender
        sql = 'SELECT meta_value FROM wp_usermeta WHERE user_id = %s AND meta_key = "gender";'
        cursor.execute(sql, (user_id,))
        gender_result = cursor.fetchall()
        gender = gender_result[0]['meta_value'] if gender_result else ""

        gender_code = get_gender_code(gender)
        category_code = get_category_code('classification_model', country_code, age, gender_code)

        products_df = category_best_seller_produtcts(category_code, n=n)
        if isinstance(products_df, pd.DataFrame):
            for product_id in products_df['product_id']:
                products.append(get_product_name_from_id(product_id))
        else:
            logging.warning("No products found for given category.")

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return products

# ============ Main Entry ============

if __name__ == '__main__':
    try:
        scan = int(input("Enter Customer ID to get recommended products: "))
        n = int(input("Enter Num of recommended products: "))
        recommended = get_customer_products(scan,n)
        print("\n🎁 Recommended Products:")
        if recommended:
            for idx, product in enumerate(recommended, start=1):
                print(f"{idx}. {product}")
        else:
            print("No product recommendations found.")
    except ValueError:
        print("❌ Invalid input. Please enter a numeric customer ID.")
