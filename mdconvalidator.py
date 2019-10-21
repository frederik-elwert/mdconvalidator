#!/usr/bin/env python3

import sys
import argparse
import logging
from pathlib import Path

import pypandoc
from lxml import etree


DATAPATH = Path('.')
TEI_TEMPLATE = DATAPATH / 'template' / 'mdconvalidator_tei.xml'
CSL = DATAPATH / 'csl' / 'digital_humanities_abstracts.csl'
SCHEMA = DATAPATH / 'schema' / 'dhconvalidator.xsd'
PUBLISHER = 'Frederik Elwert, Ruhr University Bochum'


class MDConvalidator:
    """
    Main class that handles conversion and validation of a Markdown document
    to TEI.

    """
    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile

    def convalidate(self):
        self.convert()
        self.validate()

    def convert(self):
        basedir = Path(self.infile).parent
        pandoc_args = [
            f'--template={TEI_TEMPLATE}',
            f'--csl={CSL}',
            f'--variable=publisher:"{PUBLISHER}"',
            f'--resource-path={basedir}',
        ]
        pandoc_filters = [
            'pandoc-citeproc',
        ]
        output = pypandoc.convert_file(self.infile,
                                       to='tei',
                                       extra_args=pandoc_args,
                                       filters=pandoc_filters,
                                       outputfile=self.outfile)
        logging.info(f'Converted {self.infile} to {self.outfile}.')

    def validate(self):
        doctree = etree.parse(self.outfile)
        schematree = etree.parse(str(SCHEMA))
        schema = etree.XMLSchema(schematree)

        schema.assertValid(doctree)
        logging.info('Generated TEI document is valid.')


def main():
    # Parse commandline arguments
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-v', '--verbose', action='store_true')
    arg_parser.add_argument('infile')
    arg_parser.add_argument('outfile')
    args = arg_parser.parse_args()
    # Set up logging
    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.ERROR
    logging.basicConfig(level=level)
    # Return exit value
    mdc = MDConvalidator(args.infile, args.outfile)
    mdc.convalidate()
    return 0


if __name__ == '__main__':
    sys.exit(main())
