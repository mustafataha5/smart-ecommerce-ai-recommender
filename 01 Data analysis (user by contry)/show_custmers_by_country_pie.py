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

def show_customer_by_countries_pie():
        df =custemer_by_country() 
        x= df['country']
        y= df['num_of_customer']
        plt.figure(figsize=(10,7))
        plt.pie(y,labels=x,autopct='%0.1f%%' )   
        plt.show()
show_customer_by_countries_pie()