import pandas as pd


def main():
    # Load the two Excel files
    main_df = pd.read_excel('assets/Caravan English Video RAG List.xlsx')
    tags_df = pd.read_excel('assets/Caravan English Videos List (1-7-2026) Tags.xlsx')

    sub_tags_df = tags_df[['Vimeo Link', 'Series', 'Transcripts', 'Tag_01', 'Tag_02', 'Tag_03', 'Tag_04', 'Tag_05', 'Tag_06', 'Tag_07', 'Tag_08', 'Tag_09', 'Tag_10']]



    main_df_filtered = main_df[pd.notnull(main_df['Vimeo Link'])]
    sub_tags_filtered = sub_tags_df[pd.notnull(sub_tags_df['Vimeo Link'])]
    # Diagnostic: check for duplicates
    print(f"main_df rows: {len(main_df_filtered)}")
    print(f"main_df unique Vimeo Links: {main_df_filtered['Vimeo Link'].nunique()}")
    print(f"main_df duplicates: {main_df_filtered['Vimeo Link'].duplicated().sum()}")
    print()
    print(f"sub_tags_df rows: {len(sub_tags_filtered)}")
    print(f"sub_tags_df unique Vimeo Links: {sub_tags_filtered['Vimeo Link'].nunique()}")
    print(f"sub_tags_df duplicates: {sub_tags_filtered['Vimeo Link'].duplicated().sum()}")


    print(main_df_filtered['Vimeo Link'])
    print(main_df_filtered['Vimeo Link'].unique())
    print(main_df_filtered['Vimeo Link'].duplicated())

    main_df_filtered.to_excel('assets/joins/test.xlsx', index=False)

    print(sub_tags_df['Vimeo Link'].duplicated())
    # Merge the dataframes on the 'Vimeo ID' column
    merged_df = pd.merge(main_df, sub_tags_filtered, on='Vimeo Link', how='left', indicator=True)


    # matched_rows = merged_df[merged_df['_merge'] == 'both']
    # unmatched_rows_main = merged_df[merged_df['_merge'] != 'both']
    

    # # Save the merged dataframe to CSV files
    merged_df.to_csv('assets/joins/Merged Caravan English Videos List.csv', index=False)
    # unmatched_rows_main.to_csv('assets/joins/Unmerged Caravan English Videos List.csv', index=False)
    print("Merged CSV files created successfully")

if __name__ == '__main__':
    main()
