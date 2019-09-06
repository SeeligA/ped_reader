import numpy as np
import matplotlib.pyplot as plt
import seaborn as sb
import os

from zipfile import ZipFile
import sys


def plot(df, cat_column=None, kde=True, save=False, color=None, ped=None, linewidth=5, fontsize=20):
    """Plot PED score data as histogram.
    
    Arguments:
        df -- DataFrame; containing ped analysis data. 
              Columns = ["Project", "Relation", "Document", "s_lid", "t_lid", "score", "source", "target", "mt"]
        cat_column -- String; categorical variable for displaying 
                      differential distributions (e.g. "t_lid", "s_lid", "Relation")
        kde -- Boolean; controls kernel density estimation and ticks on y axis
        save -- String specifying path to save file
        color -- String specifying the line color ("r", "b", "g", etc.)
    """
    if len(df) == 0:
        return print("Not enough data.")
    step = 0.05
    bin_edges = np.arange(0.00, df['score'].max()+step, step)
    # Create grid to accommodate subplots
    
    sb.set(font_scale=2, style="white")
    g = sb.FacetGrid(data=df, hue=cat_column, height=10, xlim=(0, 1), palette="husl")
       
    g.map(sb.distplot, "score", bins=bin_edges, kde=kde, color=color,
          kde_kws={"alpha": 1, "lw": linewidth, "label": cat_column},
          hist_kws={"alpha": 1, "histtype": "step", "linewidth": linewidth})
    
    # Get labels from distplot 
    if kde:
        locs, labels = plt.yticks()    
        # Replace density under the curve labels with proportion per bin
        # Density values depend on bin sizes which is less intuitive
        labels = [round(step*label.get_position()[1], 2) for label in labels]
        plt.yticks(locs, labels)
        
        g.set_ylabels("Bin share ({} seg. total)".format(len(df)), fontsize=fontsize)
    else:
        g.set_ylabels("# of segments ({} seg. total)".format(len(df)), fontsize=fontsize)
    
    # Note that the aggregated score does not account for different segment length
    if ped:
        g.set_xlabels('Post-edit density (Agg. score: {:.3f})'.format(round(ped, 3)), fontsize=fontsize)
    g.fig.suptitle("Distribution of PED segment scores", fontsize=fontsize)
    g.add_legend(fontsize=fontsize)
    
    if save:
        g.savefig(save, pad_inches=0.1)

        
def dict_to_obj(obj_dict):
    """
    Function that takes in a dict and returns a custom object associated with the dict.
    This function makes use of the "__module__" and "__class__" metadata in the dictionary
    to know which object type to create.
    
    Source: https://medium.com/python-pandemonium/json-the-python-way-91aac95d4041
    """
    if "__class__" in obj_dict:
        # Pop ensures we remove metadata from the dict to leave only the instance arguments
        class_name = obj_dict.pop("__class__")
        
        # Get the module name from the dict and import it
        module_name = obj_dict.pop("__module__")
        
        # We use the built in __import__ function since the module name is not yet known at runtime
        module = __import__(module_name)

        # Get the class from the module. The control flow is to help find modules from the "source" folder
        if module_name == "source.entries":
            class_ = getattr(module.entries, class_name)
        elif module_name == "source.subs":
            class_ = getattr(module.subs, class_name)
        else:
            class_ = getattr(module, class_name)

        # Use dictionary unpacking to initialize the object
        obj = class_(**obj_dict)
    else:
        obj = obj_dict
    return obj


def obj_to_dict(obj):
    """
    A function takes in a custom object and returns a dictionary representation of the object.
    This dict representation includes meta data such as the object's module and class names.

    Source: https://medium.com/python-pandemonium/json-the-python-way-91aac95d4041
    """

    #  Populate the dictionary with object meta data 
    obj_dict = {
                "__class__": obj.__class__.__name__,
                "__module__": obj.__module__
                }

    #  Populate the dictionary with object properties
    obj_dict.update(obj.__dict__)

    _ = obj_dict.pop("NAMESPACES", None)

    return obj_dict


def create_backup(dir_name, fps):

    zip_file = ZipFile(os.path.join(dir_name, 'Backup_SDLXLIFF.zip'), 'w')
    with zip_file:
        [zip_file.write(fp) for fp in fps]

    print('Backup containing {} files created here: {}'.format(len(fps), dir_name))


def unzip_sample(dir_name, fn="sample_files.zip"):
    """Extract file(s) from zip and return path(s) to file(s)."""

    fps = list()
    with ZipFile(os.path.join(dir_name, fn)) as zip_file:
        for file in zip_file.namelist():
            fps.append(os.path.join(dir_name, file))
        zip_file.extractall(dir_name)
        print(f'Sample extracted here: {dir_name}')

    return fps


def retrieve_file_paths(dir_name):
    # setup file paths variable
    fps = []
    # Read all directory, subdirectories and file lists
    for root, dirs, files in os.walk(dir_name):
        for filename in filter(lambda file: file.endswith('.sdlxliff'), files):
            fps.append(os.path.join(root, filename))

    if len(fps) > 0:
        create_backup(dir_name, fps)
        return fps

    else:
        print("No valid files found in path.")
        sys.exit(1)
