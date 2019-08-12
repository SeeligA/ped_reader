import re


class BaseEntry(object):
    def __init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, source, condition):
        self.ID = ID
        self.created_by = created_by
        self.ped_effect = ped_effect
        self.desc = desc
        self.t_lid = t_lid
        self.s_lid = s_lid        
        self.search = search
        self.replace = replace
        self.condition = condition
        self.source = source
        
    def convert_to_dict(self):
        """
        A function takes in a custom object and returns a dictionary representation of the object.
        This dict representation includes meta data such as the object's module and class names.
        
        Source: https://medium.com/python-pandemonium/json-the-python-way-91aac95d4041
        """

        #  Populate the dictionary with object meta data 
        obj_dict = {
        "__class__": self.__class__.__name__,
        "__module__": self.__module__
        }

        #  Populate the dictionary with object properties
        obj_dict.update(self.__dict__)

        return obj_dict
    

class SearchMTEntry(BaseEntry):
    def __init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, source=None, condition="MT_only"):
        BaseEntry.__init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, None, "MT_only")
        
    def search_and_replace(self, df):                

        df.mt = df.mt.str.replace(self.search, self.replace)
        
        return df

    
class SearchSourceEntry(BaseEntry):
    def __init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, source, condition="Source+MT"):
        BaseEntry.__init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, source, "Source+MT")
        
    def search_and_replace(self, df):        
        
        p = re.compile(r'{}'.format(self.source))        
        
        source_filter = df.source.str.contains(p, regex=True)
        update = df[source_filter].mt.str.replace(self.search, self.replace)
                
        df.mt.update(update)
        
        return df
    
    
class ToggleCaseEntry(BaseEntry):
    def __init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, source=None, condition="Toggle Case"):
        BaseEntry.__init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, None, "Toggle Case")
        
    def search_and_replace(self, df):
        
        search_length = self.search
        
        if self.replace == 'upper':
            # Filter for rows in which the first n source characters are uppercase
            source_filter = df.source.str[0:search_length].str.isupper()            
            # Convert the first n MT characters to uppercase and create Series
            update = df[source_filter].mt.str[0:search_length].str.upper()
            
        elif self.replace == 'istitle':
            # Filter for rows in which the first n source characters are in title case
            source_filter = df.source.str[0:search_length].str.istitle()
            # Convert the first n MT characters to title case and create Series
            update = df[source_filter].mt.str[0:search_length].str.title()

        # Extract MT strings that have not been changed and create Pandas Series
        if search_length is not None:
            rest = df[source_filter].mt.str[search_length:]
            # Concatenate strings and update MT column
            df.mt.update(update+rest)            
        
        else:
            df.mt.update(update)
            
        return df
