from src.analisis import df_load

if __name__ == '__main__':
    df = df_load.load_dataframe([("room", "==", "CIC-4")])
    df2 = df_load.group_dataframe(df, grouping_date="2H")
    print(df2) #print(df2.score.describe())
    min_value = df_load.feedback_min_value("date").to_dict()["date"]
    max_value = df_load.feedback_max_value("date").to_dict()["date"]
    print("min:", min_value, ", max:", max_value)
   
