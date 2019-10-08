import copy
import json

from source.utils import dict_to_obj, obj_to_dict
from source.calculation import pe_density
from source.xliff import create_tree
from source.utils import retrieve_file_paths


class PreprocSub(object):
    """Create a wrapper object for sets of substitution entries."""
    
    def __init__(self, version=0.1, fp=None, created_by=None, desc=None, ped_effect=None, entries=None):
        if fp:
            self.version = version
            self.load_from_json(fp)
        else:
            self.version = version
            self.created_by = created_by
            self.desc = desc
            self.ped_effect = ped_effect
            self.entries = entries

    def apply_to_table(self, df, verbose=False):
        """
        Apply substitutions to data and log effect on PED.
        
        Arguments:
            df -- DataFrame object with "source" and "mt" columns.
                  Any data in the "virtual" column will be overwritten.
            verbose -- Boolean flag to control whether PED update will be written to sdtout or not.
                  
        The method handles search and replace calls and stores the statistical 
        effect in the entries "ped_effect" attribute.
            
        Returns:
            None
        """
        if self.entries:
            # Create list and store current PED as a baseline.
            subs_ped = list()            
            ped, df = pe_density(df)
            subs_ped.append(ped)
            if verbose:
                print("Original PED:\t{:f}".format(subs_ped[0]))
            
            # Iterate through entries and run search & replace on MT data
            for entry in self.entries:
                # Apply search and replace to MT data
                df = entry.search_and_replace(df)
                # Compute new PED score and update "virtual" column in DataFrame
                new_ped, df = pe_density(df)
                if verbose:
                    print("Updated PED:\t{:f}\t{}".format(new_ped, entry.desc))
                # Calculate difference against old PED and store in entry object
                entry.ped_effect = subs_ped[len(subs_ped)-1] - new_ped
                
                subs_ped.append(new_ped)
            
            # Calculate total difference against original ped and store in self
            self.ped_effect = ped - subs_ped[-1]
            # Re-index entries based on PED effect
            self.reindex_and_sort_entries()

        return df

    def apply_to_working_files(self, fps, write=True):
        """"""

        if fps == str():
            fps = retrieve_file_paths(fps)
        cache = dict()

        for fp in fps:
            tree, tus = create_tree(fp)

            # Iterate through entries and run search & replace on MT data
            for entry in self.entries:

                entry.search_and_replace(tus)

            cache[fp] = tus
            if write:
                tree.write(fp, encoding="utf-8")

        return cache

    def reindex_and_sort_entries(self):

        for idx, entry in enumerate(sorted(self.entries, key=lambda x: x.ped_effect, reverse=True)):
            entry.ID = idx
        self.entries = sorted(self.entries, key=lambda entry: entry.ID)
    
    def load_from_json(self, fp):

        with open(fp, 'r', encoding="utf-8") as f:
            data = json.load(f)

        if data["entries"]:
            data["entries"] = list(map(dict_to_obj, data["entries"]))

        obj = dict_to_obj(data)
        self.__dict__.update(obj.__dict__)

    def convert_to_json(self, fp=None):

        obj = copy.copy(self)

        if obj.entries:
            obj.entries = list(map(obj_to_dict, obj.entries))
        
        data = obj_to_dict(obj)
       
        if fp:
            with open(fp, 'w', encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        return data
