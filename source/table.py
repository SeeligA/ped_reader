import os
import re
import logging
import pandas as pd

# Prevent Pandas from truncating strings that are too long.
pd.set_option('display.expand_frame_repr', False)
pd.set_option('max_colwidth', -1)


def load_json(fp):

    df = pd.read_json(fp, orient="records", encoding='utf-8')
    # Convert ped_detail dictionary to list
    df.ped_details = df.ped_details.apply(lambda x: [x['score'], x['source'], x['target'], x['mt']])
    headers = ['score', 'source', 'target', 'mt']
    df[headers] = pd.DataFrame(df.ped_details.tolist(), index=df.index)

    return df


def load_csv(fp):
    return pd.read_csv(fp, encoding="utf-8", index_col=0)


def create_df(directory):
    """Create DataFrame from archived JSON files."""

    columns = ["Project", "Relation", "Document", "s_lid", "t_lid", "score", "source", "target", "mt"]
    df = pd.DataFrame(columns=columns)

    for file in os.listdir(directory):
        logging.info("Loading: {}".format(file))

        if file.endswith(".json"):
            fp = os.path.join(directory, file)
            # Ignoring the index is optional. Set to True if consecutive index is preferred.
            df = df.append(load_json(fp), ignore_index=True, sort=False)

        elif file.endswith(".csv"):
            fp = os.path.join(directory, file)
            df = df.append(load_csv(fp), ignore_index=True, sort=False)

    if "ped" in df.columns and "ped_details" in df.columns:
        df = df.drop(["ped", "ped_details"], axis=1).reindex(columns=columns)

    return df


def build_query(filter_dict):
    """
    Arguments:
        filter_dict -- Dictionary with keys as filters and values as conditions

    returns:
        query as string:
        (Client == "foo" or Client == "bar") &
        (s_lid == "DE" or s_lid == "EN" or s_lid == "ES") &
        (t_lid == "NL")

        query in natural language:
        Filter entries for clients "Foo" and "Bar"
        with either German, English or Spanish as source language
        and Dutch as target language

    """
    query = str()
    for k, v in filter_dict.items():
        if k == "score":
            query += '({0} >= {1} & {0} <= {2}'.format(k, v[0], v[1])

        elif len(v) == 1:
            query += '({} == "{}"'.format(k, v[0])
        else:
            query += "("
            for i in v:
                query += '{} == "{}" or '.format(k, i)

            query = query.strip(" or ")

        query += ") & "
    query = query.strip(" & ")
    #print(query)
    return query


def filter_items(exp, data, col="mt"):
    """Show only rows where the expression matches the string in the selected column.

    Arguments:
        exp -- Search string (RegEx-enabled)
        data -- DataFrame object containing string and project data
        col -- String specifying the name of the search column. Defaults to "mt"

    Returns:
        Filtered view of DataFrame
    """

    p = re.compile(r'{}'.format(exp))
    
    my_filter = data[col].str.contains(p, regex=True)
    return data[my_filter]


def save_to_excel(df, fp):

    writer = pd.ExcelWriter(fp)
    df.to_excel(writer)
    writer.save()
