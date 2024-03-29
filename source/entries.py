import re

from lxml import etree as ET
import os
import sys


class BaseEntry(object):
    def __init__(self, search, replace, ID=None, created_by=None, ped_effect=None, desc=None,
                 s_lid=None, t_lid=None, source_filter=None):

        self.ID = ID
        self.search = search
        self.replace = replace
        self.created_by = created_by
        self.ped_effect = ped_effect
        self.desc = desc
        self.t_lid = t_lid
        self.s_lid = s_lid
        self.source_filter = source_filter
        self.NAMESPACES = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
                           'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
                           }

    def replace_target(self, element, replace=None):

        replace = self.replace if replace is None else replace

        target = element.find("xliff:target", self.NAMESPACES).iter()

        # If the segment contains inline tags, run search and replace on each each substring
        for substring in target:
            if substring.text:
                substring.text = re.sub(self.search, replace, substring.text)

            elif substring.tail:
                substring.tail = re.sub(self.search, replace, substring.tail)

    def mask_match(self, df):
        """Reset virtual score if MT string matches search expression."""

        p = re.compile(r'{}'.format(self.search))

        return df["virtual"].mask(df.mt.str.contains(p) == True)


class SearchMTEntry(BaseEntry):
    def __init__(self, kwargs):
        BaseEntry.__init__(self, **kwargs)

    def search_and_replace(self, obj):

        if obj.__class__.__name__ == "DataFrame":

            obj['virtual'] = self.mask_match(obj.copy())

            obj.mt = obj.mt.str.replace(self.search, self.replace)

        elif obj.__class__.__name__ == "list":
            obj = [self.replace_target(element) for element in obj]

        return obj


class SearchSourceEntry(BaseEntry):
    def __init__(self, kwargs):
        BaseEntry.__init__(self, **kwargs)
        # Entry validation
        assert self.source_filter

    def search_and_replace(self, obj):

        p = re.compile(r'{}'.format(self.source_filter))

        if obj.__class__.__name__ == "DataFrame":
            # Create filter based on source expression
            source_filter = obj.source.str.contains(p)
            # Copy filtered values to update table
            update = obj[source_filter].copy()
            # Reset virtual scores if row matches source filter and search expression matches MT string
            obj['virtual'] = obj['virtual'].mask(source_filter, self.mask_match(obj.copy()))
            # Apply search and replace to update table
            update = update.mt.str.replace(self.search, self.replace)
            # Overwrite values in original table with update values
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
    def __init__(self, kwargs):
        # Entry validation
        kwargs['search'] = int(kwargs['search'])
        kwargs['replace'] = kwargs['replace'].lower()
        BaseEntry.__init__(self, **kwargs)

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

        function_dict = {'upper': [str.isupper, str.upper, 'isupper'],
                         'lower': [str.islower, str.lower, 'islower'],
                         'title': [str.istitle, str.title, 'istitle']
                         }

        if obj.__class__.__name__ == "DataFrame":
            # Get source check variable from function dictionary using the replace attribute as key.
            source_check = function_dict.get(self.replace)[2]
            # Transform the string source variable to a Series string method by passing it to getattr.
            # We use the method to filter for rows in which the first n source characters match the required case.
            source_filter = getattr(obj.source.str[0:search_length].str, source_check)()
            update = obj[source_filter].copy()
            # Reset virtual scores if row matches source filter and search expression matches MT string
            obj['virtual'] = obj['virtual'].mask(source_filter, self.mask_match(obj.copy()))
            # Convert the first n MT characters to the required case and create Series
            update = getattr(update.mt.str[0:search_length].str, self.replace)()

            # Extract MT strings that have not been changed and create Pandas Series
            if search_length is not None:
                rest = obj[source_filter].mt.str[search_length:]
                # Concatenate strings and update MT column
                obj.mt.update(update + rest)

            else:
                obj.mt.update(update)

        elif obj.__class__.__name__ == "list":

            # Get source check and action function from function dictionary using the replace attribute as key.
            source_check = function_dict.get(self.replace)[0]
            action = function_dict.get(self.replace)[1]

            def update_substring(string, search_len, act):

                end = min(len(string), search_len)
                upd = act(string[:end])
                string = upd + string[end:]
                search_len -= end
                return string, search_len

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


class ApplyTagEntry(BaseEntry):
    def __init__(self, kwargs):
        BaseEntry.__init__(self, **kwargs)

    def search_and_replace(self, obj):

        if obj.__class__.__name__ == "DataFrame":
            return obj

        p = re.compile(r'{}'.format(self.source_filter))

        for element in obj:

            source_matches = self.get_existing_tags_source(element, p)

            # For each matched tag in the source, create a new replacement element.
            # If the same tag is missing from the target, we replace the first match
            # with the corresponding element.
            for i in range(len(source_matches)):

                replace = ET.fromstring(source_matches[i][0])
                if self.replace is not None:
                    replace.text = self.replace

                # We iterate over the target segment child elements
                # in case it contained subsegments/external/inline tags.
                target = element.find("xliff:target", self.NAMESPACES).iter()
                for substring in target:

                    # Check for any existing elements that match the
                    # replacement element and go to next match if True
                    check = self.check_existing_tags_target(substring, replace)
                    if check is True:
                        break

                    elif substring.text == replace.text:
                        match = append_element(substring, replace, attrs=['tail'])

                    else:
                        match = append_element(substring, replace, attrs=['text', 'tail'])

                    if match:
                        break

    def get_existing_tags_source(self, element, p):
        """Search for matching tags in source element.
        Arguments:
            element -- Trans-unit element parsed from tree
            p -- Regex pattern compiled from the object's source attribute

        Note that we search through the seg-source element NOT the source element. The former is a tokenized version of
        the latter based on sentence-based or paragraph-based segmentation.

        Returns:
            m -- List of matches ([('match_1 group_1', ...'match_1 group_n'), ('match_n group_1', ...'match2 group_n')]
        """

        # Convert source segment from element to a searchable string
        sub_element = element.find("xliff:seg-source", self.NAMESPACES)
        sub_element = ET.tostring(sub_element, encoding='utf-8').decode('utf-8')
        m = re.findall(p, sub_element)

        return m

    def check_existing_tags_target(self, element, replace):
        """Check if the target segment already contains the replacement candidate."""

        sub_element = element.find(".//xliff:{}[@{}='{}']".
                                   format(replace.tag, replace.attrib.keys()[0],
                                          replace.attrib.values()[0]), self.NAMESPACES)
        # True if a match was found or if element string and replacement string are identical
        match = sub_element is not None
        return match


def append_element(element, replace, attrs):
    """Replace match in substring with child element with text

    Arguments:
        element -- Subelement from target segment
        replace -- Replacement element based on matching tags in source segment
        attrs -- List of relevant element attributes as strings "text" and/or "tails

    Returns:
        None -- Matching strings in element are modified in place
    """
    attrs = [x for x in attrs if getattr(element, x) is not None]
    # Note that the lookahead allows us to use %#!? etc in the replacement regex
    p = re.compile(r'\b{}(?=\W|$)'.format(replace.text))

    for attr in attrs:

        # Get string index in element for replacement match using the search method
        m = p.search(getattr(element, attr))
        if m:
            idx = m.start()

            if attr == "text":
                # Add existing string in search match as tail to the replace element
                replace.tail = element.text[idx + len(replace.text):]
                # Insert new element after the substring's text,
                # but before the next child element, if any.
                element.insert(0, replace)
                # Shorten substring text
                element.text = element.text[:idx]

            else:
                # Add replace element after the current element's closing tag.
                element.addnext(replace)
                # Since the tail of the current element becomes the tail of the
                # replace element, we need to extract part of the replace tail
                # and reintroduce it as the element tail.
                element.tail = replace.tail[:idx]
                replace.tail = replace.tail[idx + len(replace.text):]

            return True


if __name__ == '__main__':
    os.chdir("..")

    sys.exit(0)
