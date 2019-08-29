from lxml import etree as ET
import pprint

NAMESPACES = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
              'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
              }


def create_tree(fp):
    tree = ET.parse(fp)
    root = tree.getroot()
    # Parse all trans-unit subelements with attribute "origin" and value "mt"
    tus = root.findall('.//xliff:trans-unit//*[@origin="mt"]/../..', NAMESPACES)
    return tree, tus


def print_sample_from_file(fp, tu_id):
    _, tus = create_tree(fp)
    print_sample(tus, tu_id)


def print_sample(tus, tu_id):
    sample = ET.tostring(tus[tu_id], encoding='utf-8', pretty_print=True).decode('utf-8')
    pp = pprint.PrettyPrinter(indent=4, width=120)
    pp.pprint(sample)
