import pandas as pd
import numpy as np
import mysql.connector
import logging
import sys
sys.stdout.reconfigure(encoding='utf-8')
# Set up error logging
# Errors will be written to 'export_errors.log' with a timestamp, level, and message.
logging.basicConfig(
    filename='export_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def make_connection_with_db():
    """
    Establishes a connection to the MySQL database.

    Returns:
        tuple: A tuple containing the connection object and cursor object,
               or (None, None) if the connection fails.
    """
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host="localhost",       # Database host (e.g., 'localhost' or an IP address)
            user="root",            # Database username
            password="",            # Database password (leave empty if no password)
            database="wp_ecommerce" # Name of the database to connect to
        )
        # Use dictionary=True to fetch results as dictionaries (column_name: value)
        cursor = connection.cursor(dictionary=True)
        return connection, cursor
    except mysql.connector.Error as err:
        logging.error(f"Error connecting to database: {err}", exc_info=True)
        print(f"Error connecting to database: {err}")
        return None, None


def get_product_name_from_id(product_id):
    """
    Retrieves the product title from the 'wp_posts' table given a product ID.

    Args:
        product_id (int): The ID of the product.

    Returns:
        str: The title of the product, or 'Not Found' if not found or an error occurs.
    """
    product_name = 'Not Found' # Initialize with default value
    connection = None
    cursor = None

    try:
        connection, cursor = make_connection_with_db()

        # Check if database connection was successful
        if connection is None or cursor is None:
            print("Database connection failed for get_product_name_from_id.")
            return product_name

        # SQL query to select the post_title (product title) from wp_posts
        # %s is used as a placeholder for secure parameter binding
        sql = 'SELECT wp_posts.post_title as product_title FROM wp_posts WHERE wp_posts.ID = %s;'

        # Execute the query with the product_id passed as a tuple
        cursor.execute(sql, (product_id,))
        results = cursor.fetchall()

        if results: # If results are found (list is not empty)
            product_name = results[0]['product_title'] # Extract the product title

    except mysql.connector.Error as err:
        logging.error(f"Database error in get_product_name_from_id for ID {product_id}: {err}", exc_info=True)
        print(f"Database error: {err}. Could not retrieve product name for ID: {product_id}")
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_product_name_from_id for ID {product_id}: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}. Could not retrieve product name for ID: {product_id}")
    finally:
        # Ensure cursor and connection are closed in all cases to release resources
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return product_name

def build_dataframe_associated_products():
    """
    Builds a DataFrame where each row represents an order and contains a list
    of product IDs purchased in that order.

    This function iterates through all orders and for each order,
    queries the associated products. This can be inefficient for large datasets
    (N+1 query problem).

    Returns:
        pd.DataFrame: A DataFrame of product IDs per order. Columns are
                      dynamically numbered (0, 1, 2, ...).
                      Returns an empty DataFrame if no data or connection fails.
    """
    # Initialize an empty DataFrame. Columns are pre-defined, assuming max 10 products.
    # If an order has fewer than 10 products, the remaining columns will be NaN.
    df = pd.DataFrame(columns=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    connection = None # Initialize connection variable
    cursor = None     # Initialize cursor variable

    try:
        connection, cursor = make_connection_with_db()

        # Check if database connection was successful
        if connection is None or cursor is None:
            print("Database connection failed for build_dataframe_associated_products.")
            return df # Return the empty DataFrame on failure

        # Select all order statistics, ordered by order_id
        sql = 'SELECT * FROM `wp_wc_order_stats` order by order_id ;'
        cursor.execute(sql)
        orders_results = cursor.fetchall() # Fetch all orders

        if orders_results: # If orders are found
            # Loop through each order
            for order in orders_results:
                order_id = order['order_id']
                # Query for products associated with the current order_id
                sql_products = 'SELECT product_id FROM `wp_wc_order_product_lookup` where order_id=%s ;'
                cursor.execute(sql_products, (order_id,))
                results_products = cursor.fetchall() # Fetch products for this order

                products_ids = []
                # Extract product_ids for the current order
                for product in results_products:
                    product_id = product['product_id']
                    if product_id > 0: # Ensure valid product IDs (e.g., exclude variations if necessary)
                        products_ids.append(product_id)

                if len(products_ids) > 0:
                    # Create a temporary DataFrame from the current order's products_ids
                    # and concatenate it to the main DataFrame.
                    # This approach can be inefficient for many small concatenations.
                    df = pd.concat([df, pd.DataFrame([products_ids])], ignore_index=True)

    except mysql.connector.Error as err:
        logging.error(f"Database error in build_dataframe_associated_products: {err}", exc_info=True)
        print(f"Database error: {err}. Could not retrieve product associations.")
    except Exception as e:
        logging.error(f"An unexpected error occurred in build_dataframe_associated_products: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}. Could not retrieve product associations.")
    finally:
        # Ensure cursor and connection are closed in all cases
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return df


def prepare_transactoins(df):
    """
    Prepares the DataFrame of associated products into a one-hot encoded
    transactional DataFrame suitable for association rule mining (e.g., Apriori).

    Args:
        df (pd.DataFrame): A DataFrame where each row is an order and columns
                           contain product IDs (can have NaNs).

    Returns:
        pd.DataFrame: A one-hot encoded DataFrame where columns are unique
                      product IDs and rows are transactions (orders).
                      Values are True if the product was in the order, False otherwise.
    """
    # Transpose the DataFrame: rows become columns and columns become rows.
    # This aligns the data for TransactionEncoder.
    df = df.T
    # Apply a lambda function to each column (original order) to drop NaNs
    # and convert to a list of product IDs.
    transactions = df.apply(lambda x : x.dropna().tolist())
    # Convert the pandas Series of lists into a list of lists,
    # which is the format required by TransactionEncoder.
    transactions_list = transactions.values.tolist()

    # Import TransactionEncoder from mlxtend for one-hot encoding of transactions
    from mlxtend.preprocessing import TransactionEncoder

    te = TransactionEncoder()
    # Fit the TransactionEncoder to learn all unique items (product IDs)
    te_model = te.fit(transactions_list)
    # Transform the transactions list into a one-hot encoded numpy array
    rows = te_model.transform(transactions_list)

    # Convert the numpy array back to a Pandas DataFrame
    # Columns are named after the unique product IDs found by TransactionEncoder.
    df_transactions = pd.DataFrame(rows, columns=te_model.columns_)
    return df_transactions

def generate_association_rules(df_transaction, support, confidence):
    """
    Generates association rules from a one-hot encoded transactional DataFrame
    using the Apriori algorithm.

    Args:
        df_transaction (pd.DataFrame): One-hot encoded DataFrame of transactions.
        support (float): The minimum support threshold for frequent itemsets (e.g., 0.01).
        confidence (float): The minimum confidence threshold for association rules (e.g., 0.5).

    Returns:
        pd.DataFrame: A DataFrame containing the generated association rules,
                      with columns like 'antecedents', 'consequents', 'confidence', etc.
    """
    # Import Apriori algorithm for finding frequent itemsets
    from mlxtend.frequent_patterns import apriori
    # Import association_rules for generating rules from frequent itemsets
    from mlxtend.frequent_patterns import association_rules

    # Find frequent itemsets using the Apriori algorithm
    # min_support filters out itemsets that appear less frequently than the threshold.
    # use_colnames=True means output uses actual item names (product IDs) instead of indices.
    frequent_itemsets = apriori(df_transaction, min_support=support, use_colnames=True)

    # Generate association rules from the frequent itemsets
    # metric='confidence' uses confidence as the primary metric.
    # min_threshold filters out rules with confidence below the threshold.
    rules = association_rules(frequent_itemsets, metric='confidence', min_threshold=confidence)

    return rules

def predict(rules, items, max_results=6):
    """
    Predicts consequent items based on given antecedent items using association rules.

    Args:
        rules (pd.DataFrame): A DataFrame containing association rules.
                              Expected columns: 'antecedents', 'consequents', 'confidence'.
                              'antecedents' and 'consequents' columns should contain frozensets.
        items (set): A set of items (antecedents) for which to find predictions.
        max_results (int): The maximum number of top predictions to return,
                           sorted by confidence in descending order.

    Returns:
        pd.DataFrame: A DataFrame of predicted consequents and their confidence,
                      sorted by confidence, up to max_results.
                      Returns an empty DataFrame if no rules match.
    """
    # Ensure 'items' is a frozenset for correct comparison with rule antecedents.
    # Association rule libraries typically store antecedents/consequents as frozensets.
    items_frozenset = frozenset(items)

    # Filter rules where the antecedents exactly match the given items.
    preds = rules[rules['antecedents'] == items_frozenset]

    # Select only the relevant columns: 'consequents' and 'confidence'.
    preds = preds[['consequents', 'confidence']]

    # Sort the predictions by 'confidence' in descending order.
    # .sort_values() returns a *new* DataFrame, so re-assign the result.
    preds = preds.sort_values('confidence', ascending=False)

    # Return the top 'max_results' predictions.
    return preds.head(max_results)

def export_to_db_with_logging(rules: pd.DataFrame):
    """
    Exports association rules to a MySQL database table named 'custom_products_association'.
    The table is dropped and recreated on each run, ensuring a clean export.
    Includes logic to prevent inserting weaker associations if stronger ones already exist
    for the same antecedent-consequent pair.

    Args:
        rules (pd.DataFrame): A DataFrame containing association rules,
                              expected to have 'antecedents', 'consequents', and 'confidence' columns.
                              'antecedents' and 'consequents' should be frozensets of product IDs.
    """
    connection = None
    cursor = None
    try:
        print("🔌 Connecting to the database...")
        connection, cursor = make_connection_with_db()

        if connection is None or cursor is None:
            print("❌ Failed to establish database connection. Aborting export.")
            logging.error("Failed to establish database connection for export.")
            return

        print("🧹 Dropping existing table if it exists...")
        cursor.execute("DROP TABLE IF EXISTS custom_products_association")
        connection.commit() # Commit the DDL (Data Definition Language) statement

        print("🛠️ Creating the table...")
        create_sql = """
            CREATE TABLE custom_products_association (
                ID INT(11) NOT NULL AUTO_INCREMENT,
                product_id_in INT(11) NOT NULL,    -- ID of the antecedent product
                post_title_in TEXT NOT NULL,       -- Title of the antecedent product
                product_id_out INT(11) NOT NULL,   -- ID of the consequent product
                post_title_out TEXT NOT NULL,      -- Title of the consequent product
                confidence DOUBLE NOT NULL,        -- Confidence of the association rule
                PRIMARY KEY(ID)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_sql)
        connection.commit() # Commit the table creation

        print(f"🚀 Exporting {len(rules)} rules to the database...")
        # Iterate through DataFrame rows using .iterrows() to get index and row data
        for index, row_data in rules.iterrows():
            print(f"📦 Processing rule {index + 1} of {len(rules)}...")
            # Extract antecedents, consequents (frozensets), and confidence from the row
            antecedents = row_data['antecedents']
            consequents = row_data['consequents']
            confidence = row_data['confidence'] * 100 # Convert confidence to percentage

            # Loop through each antecedent in the frozenset
            for product_in in antecedents:
                # Get the product title for the antecedent
                post_title_in = get_product_name_from_id(product_in)
                # Loop through each consequent in the frozenset
                for product_out in consequents:
                    # Get the product title for the consequent
                    post_title_out = get_product_name_from_id(product_out)

                    print(f"🔁 Checking association: {product_in} ({post_title_in}) ➡ {product_out} ({post_title_out}) (Confidence: {confidence:.2f}%)")

                    # Delete weaker relationships for the same product_in/product_out pair
                    delete_sql = """
                        DELETE FROM custom_products_association
                        WHERE product_id_in = %s AND product_id_out = %s AND confidence <= %s
                    """
                    try:
                        cursor.execute(delete_sql, (product_in, product_out, confidence))
                    except Exception as e:
                        logging.error(f"Error deleting old association for ({product_in}, {product_out}): {e}", exc_info=True)
                        print(f"❗ Error deleting: {e}")

                    # Check if a stronger or equal association already exists
                    select_sql = """
                        SELECT * FROM custom_products_association
                        WHERE product_id_in = %s AND product_id_out = %s AND confidence >= %s
                    """
                    try:
                        cursor.execute(select_sql, (product_in, product_out, confidence))
                        results = cursor.fetchall()
                    except Exception as e:
                        logging.error(f"Error selecting existing association for ({product_in}, {product_out}): {e}", exc_info=True)
                        print(f"❗ Error selecting: {e}")
                        results = [] # Assume no results on error to attempt insert

                    if not results: # If no stronger association exists
                        # Insert the new or updated association
                        insert_sql = """
                            INSERT INTO custom_products_association
                            (product_id_in, post_title_in, product_id_out, post_title_out, confidence)
                            VALUES (%s, %s, %s, %s, %s)
                        """
                        try:
                            cursor.execute(insert_sql, (product_in, post_title_in, product_out, post_title_out, confidence))
                            print("✅ Inserted new association.")
                        except Exception as e:
                            logging.error(f"Error inserting new association for ({product_in}, {product_out}): {e}", exc_info=True)
                            print(f"❗ Error inserting: {e}")
                    else:
                        print("⏩ Skipped (stronger association exists).")
            connection.commit() # Commit changes after processing each rule (or a batch of rules)

        print("✅ Export completed successfully.")

    except Exception as e:
        logging.error("An error occurred during export_to_db_with_logging", exc_info=True)
        if connection:
            connection.rollback() # Rollback all changes if an error occurs
        print("❌ An error occurred. Check 'export_errors.log' for details. Changes rolled back.")

    finally:
        # Ensure cursor and connection are always closed
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        print("🔒 Connection closed.")

def start_generate_association():
    """
    Orchestrates the entire process of building transactions, generating
    association rules, and exporting them to the database.
    """
    min_support = 0.001    # Minimum support threshold for frequent itemsets
    min_confidence = 0.001 # Minimum confidence threshold for association rules

    print("\n--- Starting Association Rule Generation ---")
    print("1. Building DataFrame of associated products...")
    df = build_dataframe_associated_products()
    if df.empty:
        print("No associated products data found. Aborting rule generation.")
        return

    print("2. Preparing transactions for mining...")
    transactions_df = prepare_transactoins(df)
    if transactions_df.empty:
        print("No transactions prepared. Aborting rule generation.")
        return

    print(f"3. Generating association rules with min_support={min_support} and min_confidence={min_confidence}...")
    rules = generate_association_rules(transactions_df, min_support, min_confidence)
    if rules.empty:
        print("No association rules generated. Aborting export.")
        return
    print(f"Found {len(rules)} association rules.")

    print("4. Exporting rules to database...")
    export_to_db_with_logging(rules)
    print("--- Association Rule Generation Completed ---")

def get_recommandation_products_ids(product_id):
    """
    Retrieves recommended products for a given product ID from the
    'custom_products_association' table in the database.

    Args:
        product_id (int): The ID of the product for which to get recommendations.

    Returns:
        pd.DataFrame: A DataFrame of recommended products with their ID, title,
                      and confidence, sorted by confidence in descending order.
                      Returns an empty DataFrame if no recommendations or an error occurs.
    """
    connection = None
    cursor = None
    # Initialize an empty DataFrame to store recommendations
    products_recommandations = pd.DataFrame(columns=['product_id', 'post_title', 'confidence'])

    try:
        connection, cursor = make_connection_with_db()
        if connection is None or cursor is None:
            print("Database connection failed for get_recommandation_products_ids.")
            return products_recommandations

        # SQL query to select associations where product_id_in matches the given product_id,
        # ordered by confidence in descending order.
        sql = """
            SELECT product_id_out, post_title_out, confidence
            FROM custom_products_association
            WHERE product_id_in = %s
            ORDER BY confidence DESC;
        """
        params = (product_id,) # Parameter as a tuple
        cursor.execute(sql, params)
        results = cursor.fetchall() # Fetch all matching recommendations

        if results:
            # Efficiently create DataFrame from list of dictionaries
            products_recommandations = pd.DataFrame(results)
            # Rename columns to match expected output names
            products_recommandations.rename(columns={
                'product_id_out': 'product_id',
                'post_title_out': 'post_title'
            }, inplace=True)

    except mysql.connector.Error as err:
        logging.error(f"Database error in get_recommandation_products_ids for ID {product_id}: {err}", exc_info=True)
        print(f"Database error: {err}. Could not retrieve recommendations for ID: {product_id}")
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_recommandation_products_ids for ID {product_id}: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}. Could not retrieve recommendations for ID: {product_id}")
    finally:
        # Ensure cursor and connection are closed
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return products_recommandations