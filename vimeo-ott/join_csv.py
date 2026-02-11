import pandas as pd

master_df = pd.read_csv('sheets/Caravan Wellness Master Video List - INTERNAL - German Video List.csv')
lyra_df = pd.read_csv('sheets/Lyra Health Videos List.csv')

# print(master_df[['URL','Vimeo Link']])

output_df = pd.merge(lyra_df, master_df[['URL', 'Vimeo Link']], on='URL', how='left')
output_df.to_csv('sheets/Lyra Health Videos List.csv', index=False)

