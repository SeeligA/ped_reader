from lxml import etree as ET

NAMESPACES = {'xliff': 'urn:oasis:names:tc:xliff:document:1.2',
              'sdl': 'http://sdl.com/FileTypes/SdlXliff/1.0'
              }


def create_tree(fp):
    tree = ET.parse(fp)
    root = tree.getroot()

    # Parse all trans-unit elements for which the origin attribute is set to "mt"
    tus = root.findall('xliff:file/xliff:body/xliff:trans-unit//*[@origin="mt"]/../..', NAMESPACES)
    return tree, tus
