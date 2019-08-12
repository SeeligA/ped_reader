import pandas as pd


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


def pe_density(df):
    """Calculate post edit density for MT strings

    Arguments:
        df -- 


    Returns:
        ped -- tuple containing Post-Edit density results on document level (as int()) and string level (as dict())
                 updated cache with ped result
    """
    
    lev_count = float()
    char_count = int()
    virtual_scores = []

    # Run through dataframe and calculate Levenshtein distance and
    # max length for each pair of strings
    for i in df.index:
        s1 = df.loc[i, "target"]
        s2 = df.loc[i, "mt"]
                
        if len(s1) == len(s2):
            max_char = len(s1)        
        
        else:
            max_char = max(len(s1), len(s2))

        lev = levenshtein(s1, s2)
        virtual_scores.append(lev/max_char)

        char_count += max_char
        lev_count += lev        

    ped = lev_count / char_count    
    
    return ped, virtual_scores
    

def virtual_pe_density(df):
    
    #  TODO: Make sure that PED is only re-calculated for strings that have been changed
    ped, virtual_scores = pe_density(df)
    df['virtual'] = pd.Series(virtual_scores, index=df.index)
    
    return ped
