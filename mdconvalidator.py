#!/usr/bin/env python3

import sys
import argparse
import logging
import tempfile
import shutil
from pathlib import Path

import pypandoc
from lxml import etree


DATAPATH = Path('.')
TEMPLATES = {
    'tei': DATAPATH / 'template' / 'mdconvalidator_tei.xml',
    'html': DATAPATH / 'template' / 'mdconvalidator.html',
}
CSL = DATAPATH / 'csl' / 'digital_humanities_abstracts.csl'
SCHEMAS = {
    'tei': DATAPATH / 'schema' / 'dhconvalidator.xsd'
}
EXT = {
    'tei': '.xml',
    'html': '.html',
}
# TODO: Validation fails w/o publisher. Make this configurable.
PUBLISHER = 'Frederik Elwert, Ruhr University Bochum'


class MDConvalidator:
    """
    Main class that handles conversion and validation of a Markdown document
    to TEI.

    """
    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile
        self.tempdir = tempfile.TemporaryDirectory()

    def _get_file_path(self, ext=None):
        file_path = Path(self.tempdir.name) / Path(self.outfile).name
        if ext:
            file_path = file_path.with_suffix(ext)
        return file_path

    def convalidate(self, formats=['tei', 'html'], validate=['tei']):
        # Convert into all given formats
        outfiles = {}
        for format_ in formats:
            outfiles[format_] = self.convert(format_)
        # Validate given formats
        for format_ in validate:
            self.validate(outfiles[format_], format_)
        # Copy infile
        # TODO: This uses different media paths than the extracted ones.
        # Maybe we should revise media handling to keep original file names.
        shutil.copy(self.infile, self.tempdir.name)
        # Pack as .dhc
        archive_tempdir = tempfile.TemporaryDirectory()
        archive_base = Path(archive_tempdir.name) / Path(self.outfile).stem
        archive = shutil.make_archive(archive_base,
                                      'zip',
                                      self.tempdir.name)
        shutil.copyfile(archive, self.outfile)

    def convert(self, format_):
        # Use infile directory as base for image paths and other resources
        basedir = Path(self.infile).parent
        # We want relative paths for the media.
        # Hence, we have to pass a relative path to pandoc, and not a 
        # child of self.tempdir.
        # This means it creates the media folder inside the current directory.
        # We make sure this does not override any existing directories.
        mediadir = mediadirbase = 'Pictures'
        mediadircounter = 1
        while Path(mediadir).exists():
            mediadir = f'{mediadirbase}{mediadircounter}'
            mediadircounter += 1
        # Common pipeline
        pandoc_filters = [
            'pandoc-citeproc',
        ]
        pandoc_args = [
            '--standalone',
            f'--extract-media={mediadir}',
            f'--csl={CSL}',
            f'--variable=publisher:"{PUBLISHER}"',
            f'--resource-path={basedir}',
        ]
        # Check if a custom template is configured
        if format_ in TEMPLATES:
            template = TEMPLATES[format_]
            pandoc_args.append(f'--template={template}')
        # Get file name
        outfile = self._get_file_path(EXT[format_])
        # Do the conversion
        output = pypandoc.convert_file(self.infile,
                                       to=format_,
                                       extra_args=pandoc_args,
                                       filters=pandoc_filters,
                                       outputfile=str(outfile))
        logging.info(f'Converted {self.infile} to {outfile}.')
        # Move the media dir to tempdir.
        if Path(mediadir).exists():
            dst = Path(self.tempdir.name) / mediadir
            # Check if dst exsits, might already be present from
            # previous conversion.
            if not dst.exists():
                shutil.copytree(mediadir, dst)
            shutil.rmtree(mediadir)
        return outfile

    def validate(self, file_, format_):
        doctree = etree.parse(str(file_))
        schematree = etree.parse(str(SCHEMAS[format_]))
        schema = etree.XMLSchema(schematree)

        schema.assertValid(doctree)
        logging.info(f'Generated {format_} document is valid.')


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
