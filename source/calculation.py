
def levenshtein(s1, s2):
    """Calculate Levenshtein distance based on string1 and string2

    Arguments:
        s1 and s2 as str() where s1 corresponds to the target segment and s2 to the mt segment

    Returns:
        Levenshtein distance as int()

    Source: Wikibooks
    """
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[
                             j + 1] + 1  # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1  # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def virtual_pe_density(df):
    """Calculate post edit density for MT strings.

    Arguments:
        df -- 


    Returns:
        ped -- tuple containing Post-Edit density results on document level (as int()) and string level (as dict())
                 updated cache with ped result
    """
    
    # Write the maximum length for each target-mt pair to a new column. We need this value to avoid dividing by zero.
    df["max_char"] = df.apply(lambda x: max(len(x.target), len(x.mt)), axis=1)
    # Calculate Levenshtein distance for each target-mt pair.
    df["lev"] = df.apply(lambda x: levenshtein(x.target, x.mt), axis=1)
    # Normalize Levenshtein distance by maximum segment length.
    df['virtual'] = df['lev'].copy().div(df['max_char'])

    return df


def pe_density(df):
    """Calculate the aggregated Post-Edit Distance score for all rows in a DataFrame."""

    # If PED has not been computed yet, insert the scores in the virtual column.
    col_names = {"virtual": df.score,
                 "max_char": df.apply(lambda x: max(len(x.target), len(x.mt)), axis=1),
                 "lev": None
                 }

    for name, value in col_names.items():
        if name not in df.columns:
            if name == 'lev':
                # Calculate the maximum string length and derive
                # the Levenshtein distance from the two other columns.
                # Note that this only works if the two named columns have been inserted before.
                value = df['virtual'].mul(df['max_char'])
            df.insert(loc=len(df.columns), column=name, value=value)

    # Only strings that have been altered need to be recomputed,
    # When replacing a string in the MT column, we reset the virtual value to NaN.
    if df['virtual'].isna().any():
        # Slice the table and recompute the virtual score.
        df_update = virtual_pe_density(df[df['virtual'].isna()].copy())
        # Update the table with the table slice.
        df.update(df_update)

    ped = df['lev'].sum() / df['max_char'].sum()

    return ped, df
