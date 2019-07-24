#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Generate companion files for experimentA of the idr0064 study. This script
# assumes the following layout for the original data:
#
#  <microscopic_slide>/        All data associated with a microscopic slide
#    pheno/                    Phenotypic acquisition
#      metadata.txt            Metadata for the phenotyping acquisition
#      Pos101/                 Position on a microscopyic slide
#        fluor/                Fluorescence timelapse images
#        phase/                Phase timelapse images
#    geno/                     Genotypic acqusition
#      Pos101/                 Position on the microscopyic slide
#        1_cy5_fluor/          Fluorescence acquisition (11 cycles)
#        2_cy3_fluor/          Fluorescence acquisition (11 cycles)
#        3_TxR_fluor/          Fluorescence acquisition (11 cycles)
#        4_fam_flour/          Fluorescence acquisition (11 cycles)
#        phase/                Phase acquisition (11 cycles)

import argparse
import json
import logging

from ome_model.experimental import Image, create_companion
import os
from os.path import basename, join
import subprocess

DEBUG = int(os.environ.get("DEBUG", logging.INFO))
logger = logging.basicConfig(level=DEBUG)


def read_phenotypic_positions(directory):
    """Parse positions of timelapse phenotypic data"""
    with open(join(directory, 'metadata.txt')) as f:
        metadata_lines = f.readlines()

    positions = {}
    for line in metadata_lines:
        d = json.loads(line)
        filename_split = d[u'filename'].split("\\")
        timepoint = int(filename_split[-1][-10:-5])
        channel = (0 if filename_split[-2] == 'phase' else 1)
        plane = {(channel, timepoint): {
            'filename': "%s/%s" % (filename_split[-2], filename_split[-1]),
            'exposure_time': d['exposure_time'],
            'timestamp': d['acquire_time'],
            }
        }
        if d[u'position'] in positions:
            positions[d[u'position']].update(plane)
        else:
            positions[d[u'position']] = plane
    return positions


def write_companion(image, folder):
    # Generate companion OME-XML file
    companion_file = join(
        folder, basename(folder) + '.companion.ome')
    create_companion(images=[image], out=companion_file)

    # Indent XML for readability
    proc = subprocess.Popen(
        ['xmllint', '--format', '-o', companion_file, companion_file],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    (output, error_output) = proc.communicate()
    logging.info("Created %s" % companion_file)


def create_phenotypic_companions(directory):
    # Genotypic metadata generation
    pheno_directory = join(directory, 'pheno')
    pheno_folders = [
        join(pheno_directory, x) for x in os.listdir(pheno_directory)]
    pheno_folders = sorted(filter(os.path.isdir, pheno_folders))
    logging.info(
        "Found %g folders under %s" % (len(pheno_folders), pheno_directory))

    positions = read_phenotypic_positions(pheno_directory)
    for folder in pheno_folders:
        image = Image(
            basename(folder), 2048, 879, 1, 2, 481,
            order="XYZCT", type="uint16")
        image.add_channel("phase", -1)
        image.add_channel("fluor", 16711935)

        planes = positions[basename(folder)]
        # import datetime
        # acquisition_date = datetime.datetime.utcfromtimestamp(
        #     planes[(0, 0)]['timestamp']/1000.0).isoformat()

        for t in range(481):
            image.add_tiff(planes[(0, t)]["filename"], c=0, z=0, t=t)

        for t in range(240):
            image.add_tiff(planes[(1, t)]["filename"], c=1, z=0, t=2 * t)
            image.add_tiff(planes[(1, t)]["filename"], c=1, z=0, t=2 * t + 1)
        image.add_tiff(planes[(1, 240)]["filename"], c=1, z=0, t=480)

        write_companion(image, folder)


def create_genotypic_companions(directory):
    GENO_CYCLES = 11

    # Genotypic metadata generation
    geno_directory = join(directory, 'geno')
    geno_folders = [
        join(geno_directory, x) for x in os.listdir(geno_directory)]
    geno_folders = sorted(filter(os.path.isdir, geno_folders))
    logging.info(
        "Found %g folders under %s" % (len(geno_folders), geno_directory))

    for folder in geno_folders:
        image = Image(
            basename(folder), 2048, 879, 1, 5 * GENO_CYCLES, 1,
            order="XYZCT", type="uint16")

        for i in range(GENO_CYCLES):
            image.add_channel("phase", -1)
            image.add_channel("cy5", 0)
            image.add_channel("cy3", 0)
            image.add_channel("TxR", 0)
            image.add_channel("fam", 0)

            index = str(i + 1).zfill(2)
            image.add_tiff("phase/%s.tiff" % index, c=5 * i, z=0, t=0)
            image.add_tiff(
                "1_cy5_fluor/%s.tiff" % index, c=5 * i + 1, z=0, t=0)
            image.add_tiff(
                "2_cy3_fluor/%s.tiff" % index, c=5 * i + 2, z=0, t=0)
            image.add_tiff(
                "3_TxR_fluor/%s.tiff" % index, c=5 * i + 3, z=0, t=0)
            image.add_tiff(
                "4_fam_flour/%s.tiff" % index, c=5 * i + 4, z=0, t=0)

        write_companion(image, folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', type=str, help='Path to the microscopic slide folder')
    args = parser.parse_args()

    create_phenotypic_companions(args.path)
    create_genotypic_companions(args.path)
