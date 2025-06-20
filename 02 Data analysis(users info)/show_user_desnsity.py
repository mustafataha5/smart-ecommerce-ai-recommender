import pandas as pd
 
import matplotlib.pyplot as plt
from get_user_profile import get_user_profile




def show_user_desnsity(): 
    df = get_user_profile()
    # df['age'] = pd.to_numeric(df['age'], errors='coerce')
    df_age = df['age']

    df_age.plot(kind='density')
    plt.xlabel('Age')
    plt.ylabel("Density")

    plt.title("Users Age Density")
    plt.show()




if __name__ == '__main__':
    show_user_desnsity()
	