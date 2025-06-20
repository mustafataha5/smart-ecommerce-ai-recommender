import pandas as pd 
import seaborn as sns 
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

def custemer_by_country():
    _,cursor = make_connection_with_db() 
    sel = ''' 
        SELECT c.country ,COUNT(c.customer_id) as num_of_customer
        FROM `wp_wc_customer_lookup` as c 
        GROUP By c.country
    '''
    cursor.execute(sel)
    result =cursor.fetchall() 

    df  = pd.DataFrame(result,columns=['country','num_of_customer'])
    return df 



def show_customer_by_countries_bar():
    df =custemer_by_country() 
    x= df['country']
    y= df['num_of_customer']
    plt.figure(figsize=(10,7))
    colors = [] 
    # Generate a random color for each bar
    colors = []
    for _ in range(len(x)): # Use '_' as the loop variable if 'i' is not used
        colors.append(np.random.rand(3,)) # Generates an array of 3 random floats for RGB
    
    # Plot the bars with the generated colors
    bars = plt.bar(x, y, color=colors) # Corrected parameter name to 'color'
    
    # Add annotations (numbers on top of bars)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2, # Position the text slightly above the bar
                 round(yval), ha='center', va='bottom', fontsize=9, color='black') # Format text
    plt.title('Number of Customers by Country')
    plt.xlabel('Country')
    plt.ylabel('Number of Customers')
    plt.xticks(rotation=45, ha='right') # Rotate x-axis labels for better readability if many countries
    plt.tight_layout() # Adjust layout to prevent labels from overlapping
    plt.show()



show_customer_by_countries_bar()



