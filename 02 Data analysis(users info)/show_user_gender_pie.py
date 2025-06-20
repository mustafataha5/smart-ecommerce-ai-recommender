import pandas as pd
import matplotlib.pyplot as plt
from get_user_profile import get_user_profile


def show_user_gender_pie(): 
    df = get_user_profile() 
    if df.empty:
        print("No user data available to generate gender pie chart.")
        return

    # # Standardize gender values (e.g., to lowercase) and map common variations
    # # This helps ensure consistency if gender data isn't perfectly clean
    # df['gender'] = df['gender'].astype(str).str.lower().replace({
    #     'ذكر': 'male',
    #     'انثى': 'female',
    #     'm': 'male',
    #     'f': 'female',
    #     'ذكر ': 'male', # Handle extra spaces
    #     'انثى ': 'female'
    # })
    # X = df[['gender','user_id']].groupby('gender').count()
    
    import arabic_reshaper 
    from bidi.algorithm import get_display 
    df['gender'] = df['gender'].apply(lambda x: get_display(arabic_reshaper.reshape(x)))
    X = df['gender'].value_counts()
 
    plt.figure(figsize=(10,7))
    plt.pie(X.values,labels=X.index,autopct='%0.1f%%')
    
    plt.show()

def show_user_gender_pie_en(): 
    df = get_user_profile() 
    if df.empty:
        print("No user data available to generate gender pie chart.")
        return

    # # Standardize gender values (e.g., to lowercase) and map common variations
    # # This helps ensure consistency if gender data isn't perfectly clean
    df['gender'] = df['gender'].astype(str).str.lower().replace({
        'ذكر': 'male',
        'انثى': 'female',
        'm': 'male',
        'f': 'female',
        'ذكر ': 'male', # Handle extra spaces
        'انثى ': 'female'
    })
    X = df['gender'].value_counts()
    # print(X)
    # print(X.index)
    # print(X.values)
 
    plt.figure(figsize=(10,7))
    plt.pie(X.values,labels=X.index,autopct='%0.1f%%')
    
    plt.show()    

    
if __name__ == '__main__':
    i = input("Arabic (y)")
    if i == 'y':
        show_user_gender_pie()
    else: 
        show_user_gender_pie_en()
	