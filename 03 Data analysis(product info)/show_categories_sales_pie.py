

from get_categories_sales import get_categories_sales
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns
import arabic_reshaper 
from bidi.algorithm import get_display 

def show_categories_sales_pie():
    df =get_categories_sales() 
    import arabic_reshaper 
    from bidi.algorithm import get_display 

    df['category_name'] =  df['category_name'].apply(lambda x : get_display(arabic_reshaper.reshape(x)))
   
    plt.figure(figsize=(10,7))
    # Create the pie chart
    # autopct='%%0.1f%%' correctly displays the percentage with one decimal place and a '%' sign
    plt.pie(df['sales'], labels=df['category_name'], autopct='%%%.1f%%', startangle=90)

    # Add a title to the pie chart
    plt.title("Sales Distribution per Category")
       
    plt.tight_layout() # Adjust layout to prevent labels from overlapping
    plt.show()

    

if __name__ == '__main__':
	show_categories_sales_pie()