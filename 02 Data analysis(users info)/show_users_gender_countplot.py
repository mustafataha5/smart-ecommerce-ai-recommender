
import pandas as pd
import matplotlib.pyplot as plt
from get_user_profile import get_user_profile
import seaborn as sns
import arabic_reshaper 
from bidi.algorithm import get_display 


def show_users_gender_countplot():
    df = get_user_profile() 
    if df.empty:
        print("No user data available to generate gender pie chart.")
        return
    df['gender'] = df['gender'].apply(lambda x: get_display(arabic_reshaper.reshape(x)))
    X = df['gender'].value_counts()
 
    plt.figure(figsize=(10,7))
    plt.title('User Gender Count')
    ax = sns.countplot(data=df,x='gender', hue='gender',palette='viridis')
    for container in ax.containers:
        ax.bar_label(container)
    plt.show()
    
if __name__ == '__main__':
        show_users_gender_countplot()