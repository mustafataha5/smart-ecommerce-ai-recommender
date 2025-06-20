import logging
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import mysql.connector
from collections import defaultdict
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import RandomOverSampler
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import CategoricalNB
from sklearn.neighbors import KNeighborsClassifier
import pickle
import m2cgen as m2c
import arabic_reshaper
from bidi.algorithm import get_display

# Configure logging
# Create a file handler
file_handler = logging.FileHandler("model_training.log", encoding='utf-8')
file_handler.setLevel(logging.INFO) # Set level for file output

# Create a stream handler (for console output)
# Set its encoding to 'utf-8'
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO) # Set level for console output
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Basic configuration for the root logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[file_handler, stream_handler])

# --- Your existing functions go here, with logging integrated ---

def make_connection_with_db():
    try:
        connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="wp_ecommerce")
        cursor = connection.cursor(dictionary=True)
        logging.info("✅ Database connection established.") # This emoji was causing issues
        return connection, cursor
    except mysql.connector.Error as err:
        logging.error(f"❌ Database connection failed: {err}") # This emoji was causing issues
        return None, None

def get_product_categories(product_id):
    connection, cursor = None, None
    trem_ids = []
    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            logging.error("Database connection failed in get_product_categories.")
            return [] # Return an empty list if connection fails

        sql = """
        SELECT wp_term_relationships.object_id ,wp_term_taxonomy.term_id
        FROM `wp_term_relationships`
        JOIN wp_term_taxonomy on wp_term_taxonomy.term_taxonomy_id = wp_term_relationships.term_taxonomy_id
        WHERE wp_term_taxonomy.taxonomy='product_cat' and wp_term_relationships.object_id=(%s)
        ORDER BY `wp_term_taxonomy`.`term_id` ASC
        """
        cursor.execute(sql, (product_id,))
        results = cursor.fetchall()

        if results:
            trem_ids = [row['term_id'] for row in results]
            logging.debug(f"Retrieved categories for product ID {product_id}: {trem_ids}")
        else:
            logging.info(f"No categories found for product ID {product_id}.")

    except mysql.connector.Error as err:
        logging.error(f"Database error in get_product_categories: {err}. Could not retrieve categories for product ID: {product_id}")
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_product_categories: {e}. Could not retrieve categories for product ID: {product_id}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return trem_ids

def get_category_by_id(category_id):
    connection, cursor = None, None
    category_name = "Not Found"
    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            logging.error("Database connection failed in get_category_by_id.")
            return category_name # Return default if connection fails

        sql = """
        SELECT name
        FROM `wp_terms`
        JOIN wp_term_taxonomy on wp_term_taxonomy.term_id = wp_terms.term_id
        WHERE wp_term_taxonomy.taxonomy='product_cat' and wp_terms.term_id =(%s)
        """
        cursor.execute(sql, (category_id,))
        results = cursor.fetchall()

        if results:
            category_name = results[0]['name']
            logging.debug(f"Retrieved category name for ID {category_id}: {category_name}")
        else:
            logging.info(f"No category name found for ID {category_id}.")

    except mysql.connector.Error as err:
        logging.error(f"Database error in get_category_by_id: {err}. Could not retrieve category name for ID: {category_id}")
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_category_by_id: {e}. Could not retrieve category name for ID: {category_id}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return category_name

def build_customer_data_v2():
    """
    Builds a DataFrame containing customer demographic data and their most purchased product category.
    The function is optimized for performance by querying and processing data in bulk.
    """
    connection, cursor = None, None
    try:
        connection, cursor = make_connection_with_db()
        if not connection or not cursor:
            logging.error("❌ Failed to connect to the database in build_customer_data_v2.")
            return pd.DataFrame()

        logging.info("Starting to fetch user demographics.")
        cursor.execute("""
            SELECT user_id, meta_key, meta_value
            FROM wp_usermeta
            WHERE meta_key IN ('country', 'gender', 'age');
        """)
        user_meta_rows = cursor.fetchall()
        demographics = defaultdict(dict)
        for row in user_meta_rows:
            demographics[row['user_id']][row['meta_key']] = row['meta_value']
        logging.info(f"Fetched {len(demographics)} user demographics.")

        logging.info("Starting to map user_id to customer_id.")
        cursor.execute("SELECT user_id, customer_id FROM wp_wc_customer_lookup;")
        customer_rows = cursor.fetchall()
        user_to_customer = {row['user_id']: row['customer_id'] for row in customer_rows}
        logging.info(f"Mapped {len(user_to_customer)} user_ids to customer_ids.")

        logging.info("Starting to fetch product category purchase counts per customer.")
        cursor.execute("""
            SELECT
                wccl.user_id,
                wccl.customer_id,
                wt.term_id,
                wt.name AS term_name,
                COUNT(wt.term_id) AS count_term_id
            FROM wp_wc_order_product_lookup wwopl
            JOIN wp_posts wp ON wwopl.order_id = wp.ID
            JOIN wp_postmeta wpm ON wp.ID = wpm.post_id
            JOIN wp_wc_customer_lookup wccl ON wpm.meta_value = wccl.user_id AND wpm.meta_key = '_customer_user'
            JOIN wp_term_relationships wtr ON wwopl.product_id = wtr.object_id
            JOIN wp_term_taxonomy wtt ON wtr.term_taxonomy_id = wtt.term_taxonomy_id
            JOIN wp_terms wt ON wtt.term_id = wt.term_id
            WHERE wtt.taxonomy = 'product_cat'
            GROUP BY wccl.user_id, wccl.customer_id, wt.term_id, wt.name
            ORDER BY wccl.customer_id, count_term_id DESC;
        """)
        term_rows = cursor.fetchall()
        logging.info(f"Fetched {len(term_rows)} product category purchase records.")

        logging.info("Determining top category per user.")
        user_top_category = {}
        for row in term_rows:
            user_id = int(row['user_id'])
            customer_id = int(row['customer_id'])
            current_top = user_top_category.get(user_id, {})
            if row['count_term_id'] > current_top.get('count_term_id', -1):
                user_top_category[user_id] = {
                    'customer_id': customer_id,
                    'term_id': row['term_id'],
                    'term_name': row['term_name'],
                    'count_term_id': row['count_term_id']
                }
        logging.info(f"Identified top categories for {len(user_top_category)} users.")

        logging.info("Combining all data into final DataFrame.")
        all_user_ids = set(demographics.keys()) | set(user_to_customer.keys()) | set(user_top_category.keys())
        final_data = []
        for user_id in sorted(all_user_ids):
            user_obj = {
                'user_id': user_id,
                'customer_id': user_to_customer.get(user_id),
                'country': demographics.get(user_id, {}).get('country'),
                'age': demographics.get(user_id, {}).get('age'),
                'gender': demographics.get(user_id, {}).get('gender'),
                'term_id': None,
                'term_name': "",
                'count_term_id': 0
            }
            if user_id in user_top_category:
                top = user_top_category[user_id]
                if top.get('customer_id') is not None:
                    user_obj['customer_id'] = top['customer_id']
                user_obj['term_id'] = top['term_id']
                user_obj['term_name'] = top['term_name']
                user_obj['count_term_id'] = top['count_term_id']

            final_data.append(user_obj)

        df = pd.DataFrame(final_data)
        df['customer_id'] = pd.to_numeric(df['customer_id'], errors='coerce').astype('Int64')
        df['age'] = pd.to_numeric(df['age'], errors='coerce').astype('Int64')
        df['term_id'] = pd.to_numeric(df['term_id'], errors='coerce').astype('Int64')
        df['count_term_id'] = pd.to_numeric(df['count_term_id'], errors='coerce').astype('Int64')
        logging.info(f"Customer data DataFrame built with {len(df)} rows.")
        return df

    except mysql.connector.Error as err:
        logging.error(f"❌ Database error in build_customer_data_v2: {err}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ Unexpected error in build_customer_data_v2: {e}", exc_info=True) # exc_info to log traceback
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_category_code(filename, country, age, gender):
    try:
        loaded_model = pickle.load(open(filename, 'rb'))
        input_df = pd.DataFrame([{
            'country': country,
            'age': age,
            'gender': gender
        }])
        res = loaded_model.predict(input_df)
        logging.info(f"Predicted category code for country={country}, age={age}, gender={gender}: {res[0]}")
        return res[0]
    except FileNotFoundError:
        logging.error(f"❌ Model file not found at {filename}.")
        return None
    except Exception as e:
        logging.error(f"❌ Error during prediction in get_category_code: {e}", exc_info=True)
        return None

def label_encoder_to_db(table, col_name, col_type, le):
    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            logging.error("Database connection failed.")
            return

        # Drop table if it exists
        cursor.execute(f"DROP TABLE IF EXISTS {table};")
        connection.commit()
        logging.info(f"Dropped table `{table}` if it existed.")

        # Create table
        sql = f"""
        CREATE TABLE {table} (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            code INT NOT NULL,
            {col_name} {col_type} NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(sql)
        connection.commit()
        logging.info(f"Created table `{table}`.")

        # Insert label encoder mappings
        for d in le.classes_:
            code = int(le.transform([d])[0])
            insert_sql = f"INSERT INTO {table} (code, {col_name}) VALUES (%s, %s);"
            cursor.execute(insert_sql, (code, d))
        connection.commit()
        logging.info(f"LabelEncoder mappings inserted into `{table}` successfully.")

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}", exc_info=True)

    except Exception as e:
        logging.error(f"Unexpected error during label_encoder_to_db: {e}", exc_info=True)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
            
            
            
if __name__ == '__main__':
    logging.info("--- Starting customer data analysis and model training script ---")

    customer_df = build_customer_data_v2()
    if customer_df.empty:
        logging.critical("Exiting script because customer data could not be loaded.")
        exit()

    logging.info(f"Customer Data Head:\n{customer_df.head()}")
    logging.info(f"Customer Data Info:\n{customer_df.info()}")
    logging.info(f"Missing values before dropna:\n{customer_df.isnull().sum()}")

    initial_rows = len(customer_df)
    customer_df = customer_df.dropna()
    rows_dropped = initial_rows - len(customer_df)
    if rows_dropped > 0:
        logging.warning(f"Dropped {rows_dropped} rows due to missing values.")

    duplicated_rows = customer_df.duplicated().sum()
    if duplicated_rows > 0:
        logging.warning(f"Found {duplicated_rows} duplicated rows.")

    logging.info(f"Customer Data Description:\n{customer_df.describe()}")

    # Label encoding
    country_le = LabelEncoder()
    gender_le = LabelEncoder()

    try:
        customer_df['country'] = country_le.fit_transform(customer_df['country'])
        customer_df['gender'] = gender_le.fit_transform(customer_df['gender'])
        logging.info("Label encoding successful for 'country' and 'gender'.")
    except Exception as e:
        logging.critical(f"Error during label encoding: {e}", exc_info=True)
        exit()

    # Optional Pie Chart
    try:
        x = customer_df['term_name'].value_counts()
        if not x.empty:
            reshaped_labels = [get_display(arabic_reshaper.reshape(label)) for label in x.index]
            plt.figure(figsize=(10, 7))
            plt.pie(x, labels=reshaped_labels, autopct='%1.1f%%', textprops={'fontsize': 12})
            plt.title(get_display(arabic_reshaper.reshape('أكثر الفئات شراءً من قبل العملاء')), fontsize=14)
            plt.axis('equal')
            plt.savefig('most_purchased_categories_pie_chart.png')
            plt.close()
            logging.info("Generated 'most_purchased_categories_pie_chart.png'.")
    except Exception as e:
        logging.warning(f"Failed to generate pie chart: {e}", exc_info=True)

    # Features and labels
    X = customer_df[['country', 'age', 'gender']]
    y = customer_df['term_id']

    from collections import Counter
    logging.info(f"Class distribution BEFORE oversampling: {dict(Counter(y))}")

    # Oversampling
    try:
        oversample = RandomOverSampler(random_state=42)
        X_resampled, y_resampled = oversample.fit_resample(X, y)
        logging.info(f"Class distribution AFTER oversampling: {dict(Counter(y_resampled))}")
        logging.info(f"Resampled dataset: {len(X_resampled)} samples.")
    except Exception as e:
        logging.critical(f"Error during oversampling: {e}", exc_info=True)
        exit()

    # Model selection
    from sklearn.model_selection import cross_val_score
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.naive_bayes import CategoricalNB
    from sklearn.neighbors import KNeighborsClassifier

    models = {
        "Decision Tree": DecisionTreeClassifier(),
        "Naive Bayes": CategoricalNB(),
        "KNN": KNeighborsClassifier()
    }

    best_model = None
    best_model_name = None
    best_score = 0.0

    for name, model in models.items():
        try:
            scores = cross_val_score(model, X_resampled, y_resampled, cv=10, scoring='accuracy')
            mean_score = scores.mean()
            logging.info(f"{name} Accuracy: {round(mean_score * 100):.0f}%")
            if mean_score > best_score:
                best_score = mean_score
                best_model = model
                best_model_name = name
        except Exception as e:
            logging.error(f"Error evaluating {name}: {e}", exc_info=True)

    if best_model is None:
        logging.critical("No model was successfully evaluated. Exiting.")
        exit()

    logging.info(f"✅ Best model selected: {best_model_name} with accuracy: {round(best_score * 100):.0f}%")

    # Train final model
    try:
        best_model.fit(X_resampled, y_resampled)
        filename = 'classification_model.pkl'
        with open(filename, 'wb') as f:
            pickle.dump(best_model, f)
        logging.info(f"{best_model_name} model trained and saved to '{filename}'.")
    except Exception as e:
        logging.critical(f"Error training or saving model: {e}", exc_info=True)
        exit()

    # Test prediction
    predicted_category_code = get_category_code(filename, 2, 40, 1)
    if predicted_category_code is not None:
        predicted_category_name = get_category_by_id(predicted_category_code)
        logging.info(f"Example prediction — ID: {predicted_category_code}, Name: {predicted_category_name}")
    else:
        logging.warning("Example prediction failed.")

    # Export to PHP
    try:
        model_to_php = m2c.export_to_php(best_model)
        with open('predict_category.php', 'w', encoding='utf-8') as f:
            f.write(model_to_php)
        logging.info("✅ Model exported to 'predict_category.php'.")
    except Exception as e:
        logging.error(f"Error exporting model to PHP: {e}", exc_info=True)

    # Save LabelEncoder mappings
    label_encoder_to_db('custom_country_code', 'country', 'VARCHAR(255)', country_le)
    label_encoder_to_db('custom_gender_code', 'gender', 'VARCHAR(10)', gender_le)

    logging.info("--- Script execution finished ---")
