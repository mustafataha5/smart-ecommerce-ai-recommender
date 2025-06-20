import pandas as pd 
import matplotlib.pyplot as plt
from get_user_profile import get_user_profile



def show_user_histgoram(): 
    df = get_user_profile()
    # df['age'] = pd.to_numeric(df['age'], errors='coerce')
    df_age = df['age']

    df_age.hist(bins=[0,10,20,30,40,50,60,70,80])
    plt.xlabel('Age')
    plt.ylabel("Count")

    plt.title("Users Age Histogram")
    plt.show()

if __name__ == '__main__':
	show_user_histgoram()    
	