
import os
import pandas as pd

# Utility script used to convert WMT16 crp files to CSV files with source and target columns


top_directory = "bilingual"


def iter_documents(top_directory):
    for root, dirs, files in os.walk(top_directory):
        
        if len(dirs) == 1:
            
            df = create_df(os.path.join(root, dirs[0]))
            df = clean_df(df)
            df_to_csv(df, os.path.join(root, dirs[0]))

def create_df(root):
    dir_list = os.listdir(root)
    
    title = pd.Series()
    source = pd.Series()
    target = pd.Series()
    df = pd.DataFrame()

    for file in dir_list:
        fp = os.path.join(root, file)
        try:
            new_data = pd.read_csv(fp, header=None, 
                                   sep='\t', 
                                   index_col=False, 
                                   skip_blank_lines=False # If blank lines are not skipped
                                  )                       # 

            target = new_data[0][new_data.index % 3 == 1]
            source = new_data[0][new_data.index % 3 == 2]
            title = new_data[0][new_data.index % 3 == 0]

            new_df = pd.DataFrame([title.values, source.values, target.values]).transpose()

            df = df.append(new_df)
            
        except EmptyDataError:      
            print(fp)
        
    return df
        
def clean_df(df):
    df.columns = ['title', 'source', 'target']
    df = df[df['title'].str.len() == 28].copy()
    df['title'] = df["title"].str.replace('-.+?$','', regex=True).copy()    
    return df
    
def df_to_csv(df, root):
    for idx in df.title.unique():
        df[df.title == idx].to_csv(os.path.join(root, '{}.csv'.format(idx)))
    
if __name__ == '__main__':
    iter_documents(top_directory)
    print("Done!")
    
