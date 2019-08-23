from lxml import etree as ET

NAMESPACES = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
              'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
              }


def create_tree(fp):
    tree = ET.parse(fp)
    root = tree.getroot()

    # Parse all trans-unit subelements with attribute "origin" and value "mt"
    tus = root.findall('.//xliff:trans-unit//*[@origin="mt"]/../..', NAMESPACES)
    #tus = root.findall('xliff:file/**/xliff:trans-unit//*[@origin="mt"]/../..', NAMESPACES)
    return tree, tus
