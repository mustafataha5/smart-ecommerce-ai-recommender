
from get_categories_sales import get_categories_sales
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns
import arabic_reshaper 
from bidi.algorithm import get_display 

def show_categories_sales_bar():
    df =get_categories_sales() 

    df['category_name'] =  df['category_name'].apply(lambda x : get_display(arabic_reshaper.reshape(x)))
    
    x =  df['category_name']
    y = df['sales'] 
    plt.figure(figsize=(10,7))
    plt.bar(x,y)
    plt.xlabel('Cateegory Name')
    plt.ylabel('Sales')
    plt.title("Sales per Category")

    colors = [np.random.rand(3,) for _ in range(len(x))] 
    bars = plt.bar(x,y,color=colors) 
    for bar in bars :
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2, # X-position: center of the bar
            height + 5, # Y-position: slightly above the bar
            f'{int(height)}', # The text to display
            ha='center', # Horizontal alignment: center
            va='bottom', # Vertical alignment: bottom
            fontsize=10
        )
       
       
    plt.tight_layout() # Adjust layout to prevent labels from overlapping
    plt.show()

if __name__ == '__main__':
        show_categories_sales_bar()

