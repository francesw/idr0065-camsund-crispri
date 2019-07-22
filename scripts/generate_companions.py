#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Generate companion files for experimentA of the idr0064 study. This script
# assumes the following layout for the original data:
#
#  <microscopic_slice>/        All data associated with a microscopic slide
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

import json
import logging
import datetime
from ome_model.experimental import Image, create_companion
import os
from os.path import basename, dirname, join, abspath
import sys
import subprocess

DEBUG = int(os.environ.get("DEBUG", logging.INFO))
EXPERIMENT_DIRECTORY = join(
    dirname(abspath(dirname(sys.argv[0]))), 'experimentA')
METADATA_DIRECTORY = join(EXPERIMENT_DIRECTORY, 'companions')
BASE_DIRECTORY = join(METADATA_DIRECTORY, 'subpool-1_run-1_EXP-19-BQ3550')

FILEPATHS_TSV = join(EXPERIMENT_DIRECTORY, 'idr0064-experimentA-filePaths.tsv')

PHENO_DIRECTORY = join(BASE_DIRECTORY, 'pheno')
GENO_DIRECTORY = join(BASE_DIRECTORY, 'geno')
PHENO_CYCLES = 11

logger = logging.basicConfig(level=DEBUG)


# Positions metadata parsing
metadata = {}
with open(join(PHENO_DIRECTORY, 'metadata.txt')) as f:
    metadata_lines = f.readlines()

positions = {}
for line in metadata_lines:
    planes = {}
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

# Genotypic metadata generation
pheno_folders = [join(PHENO_DIRECTORY, x) for x in os.listdir(PHENO_DIRECTORY)]
pheno_folders = sorted(filter(os.path.isdir, pheno_folders))
logging.info(
    "Found %g folders under %s" % (len(pheno_folders), PHENO_DIRECTORY))

for folder in pheno_folders:
    image = Image(
        basename(folder), 2048, 879, 1, 2, 481,
        order="XYZCT", type="uint16")
    image.add_channel("phase", 0)
    image.add_channel("fluor", 0)

    planes = positions[basename(folder)]
    acquisition_date = datetime.datetime.utcfromtimestamp(
        planes[(0, 0)]['timestamp']/1000.0).isoformat()
    # print planes
    for t in range(481):
        image.add_tiff(planes[(0, t)]["filename"], c=0, z=0, t=t)

    for t in range(240):
        image.add_tiff(planes[(1, t)]["filename"], c=1, z=0, t=2 * t)
        image.add_tiff(planes[(1, t)]["filename"], c=1, z=0, t=2 * t + 1)
    image.add_tiff(planes[(1, 240)]["filename"], c=1, z=0, t=480)

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

# Genotypic metadata generation
geno_folders = [join(GENO_DIRECTORY, x) for x in os.listdir(GENO_DIRECTORY)]
geno_folders = sorted(filter(os.path.isdir, geno_folders))
logging.info(
    "Found %g folders under %s" % (len(geno_folders), GENO_DIRECTORY))

for folder in geno_folders:
    image = Image(
        basename(folder), 2048, 879, 1, 5 * PHENO_CYCLES, 1,
        order="XYZCT", type="uint16")

    for i in range(PHENO_CYCLES):
        image.add_channel("phase", 0)
        image.add_channel("cy5", 0)
        image.add_channel("cy3", 0)
        image.add_channel("TxR", 0)
        image.add_channel("fam", 0)

        index = str(i + 1).zfill(2)
        image.add_tiff("phase/%s.tiff" % index, c=5 * i, z=0, t=0)
        image.add_tiff("1_cy5_fluor/%s.tiff" % index, c=5 * i + 1, z=0, t=0)
        image.add_tiff("2_cy3_fluor/%s.tiff" % index, c=5 * i + 2, z=0, t=0)
        image.add_tiff("3_TxR_fluor/%s.tiff" % index, c=5 * i + 3, z=0, t=0)
        image.add_tiff("4_fam_flour/%s.tiff" % index, c=5 * i + 4, z=0, t=0)

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
