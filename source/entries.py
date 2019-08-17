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
        self.NAMESPACES = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
                           'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
                           }

    def replace_target(self, element):

        target = element.find("xliff:target", self.NAMESPACES).iter()
        # If the segment contains inline tags, run search and replace on each each substring
        for substring in target:
            if substring.text:
                substring.text = re.sub(self.search, self.replace, substring.text)
            elif substring.tail:
                substring.tail = re.sub(self.search, self.replace, substring.tail)
    

class SearchMTEntry(BaseEntry):
    def __init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, source=None, condition="MT_only"):
        BaseEntry.__init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, None, "MT_only")
        
    def search_and_replace(self, obj):

        if obj.__class__.__name__ == "DataFrame":
            obj.mt = obj.mt.str.replace(self.search, self.replace)

        elif obj.__class__.__name__ == "list":\
            obj = [self.replace_target(element) for element in obj]

        return obj


class SearchSourceEntry(BaseEntry):
    def __init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, source, condition="Source+MT"):
        BaseEntry.__init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, source, "Source+MT")
        
    def search_and_replace(self, obj):
        
        p = re.compile(r'{}'.format(self.source))

        if obj.__class__.__name__ == "DataFrame":
            source_filter = obj.source.str.contains(p, regex=True)
            update = obj[source_filter].mt.str.replace(self.search, self.replace)

            obj.mt.update(update)

        elif obj.__class__.__name__ == "list":
            for element in obj:
                # Parse string data in source segment
                seg_source = ''.join(element.find("xliff:seg-source", self.NAMESPACES).itertext())
                # Parse target segment if expression is in source
                if re.search(p, seg_source):
                    self.replace_target(element)

        return obj

    
class ToggleCaseEntry(BaseEntry):
    def __init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, source=None, condition="Toggle Case"):
        BaseEntry.__init__(self, ID, created_by, ped_effect, desc, t_lid, s_lid, search, replace, None, "Toggle Case")

    def search_and_replace(self, obj):
        """Change case of the target string.

        Arguments:
            obj -- Either a DataFrame object or a list of XML Elements parsed from an XLIFF tree.

            This method looks at the first n characters in a source string and matches it against the
            replacement check method. If there is a match, it applies the replacement action method to
            the first n character of the target string.

        Returns
            Updated object with the case changed
        """

        search_length = self.search

        if obj.__class__.__name__ == "DataFrame":
            #  TODO: Check which type is required for the Series data in order to call string methods from function dict
            if self.replace == 'upper':
                # Filter for rows in which the first n source characters are uppercase
                source_filter = obj.source.str[0:search_length].str.isupper()
                # Convert the first n MT characters to uppercase and create Series
                update = obj[source_filter].mt.str[0:search_length].str.upper()

            elif self.replace == 'istitle':
                # Filter for rows in which the first n source characters are in title case
                source_filter = obj.source.str[0:search_length].str.istitle()
                # Convert the first n MT characters to title case and create Series
                update = obj[source_filter].mt.str[0:search_length].str.title()

            elif self.replace == 'lower':
                # Filter for rows in which the first n source characters are in title case
                source_filter = obj.source.str[0:search_length].str.islower()
                # Convert the first n MT characters to title case and create Series
                update = obj[source_filter].mt.str[0:search_length].str.lower()

            # Extract MT strings that have not been changed and create Pandas Series
            if search_length is not None:
                rest = obj[source_filter].mt.str[search_length:]
                # Concatenate strings and update MT column
                obj.mt.update(update+rest)

            else:
                obj.mt.update(update)

        elif obj.__class__.__name__ == "list":

            function_dict = {'upper': [str.isupper, str.upper],
                             'lower': [str.islower, str.lower],
                             'title': [str.istitle, str.title]
                             }

            # Map replace string parameter against check and action in function dictionary.
            source_check = function_dict.get(self.replace)[0]
            action = function_dict.get(self.replace)[1]

            def update_substring(string, search_length, action):

                end = min(len(string), search_length)
                update = action(string[:end])
                string = update + string[end:]
                search_length -= end
                return string, search_length

            # Iterate over trans-units to parse source and target segments
            for element in obj:

                seg_source = ''.join(element.find("xliff:seg-source", self.NAMESPACES).itertext())
                # Call the check method from the function dict
                if source_check(seg_source[0:min(len(seg_source), self.search)]):

                    target = element.find("xliff:target", self.NAMESPACES).iter()
                    # Set length of replacement string for each target segment
                    search_length = self.search
                    running = True
                    while running:
                        # If the segment contains inline tags, run search and replace on each each substring
                        for substring in target:
                            if search_length <= 0:
                                running = False
                            elif substring.text is not None:
                                substring.text, search_length = update_substring(substring.text, search_length, action)
                            elif substring.tail is not None:
                                substring.tail, search_length = update_substring(substring.tail, search_length, action)
                            else:
                                running = False

        return obj
