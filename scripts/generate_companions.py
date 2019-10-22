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

import logging

from ome_model.experimental import Image, create_companion
import os
from os.path import basename, join, dirname, abspath
import subprocess
import sys

BASE_DIRECTORY = "/uod/idr/filesets/idr0065-camsund-crispri/"
TIMESTAMPS_FILE = join(BASE_DIRECTORY, "20190823-ftp", "acq_time.txt")
MAPPINGS_FILE = join(BASE_DIRECTORY, "20190823-ftp", "fluor_phase_link.txt")
EXPERIMENTA_DIRECTORY = join(
    dirname(abspath(dirname(sys.argv[0]))), 'experimentA', 'companions')
EXPERIMENTB_DIRECTORY = join(
    dirname(abspath(dirname(sys.argv[0]))), 'experimentB', 'companion')

DEBUG = int(os.environ.get("DEBUG", logging.INFO))
logger = logging.basicConfig(level=DEBUG)


def read_phenotypic_time_indexes():
    time_indexes = {}
    with open(MAPPINGS_FILE, 'r') as f:
        for l in f.readlines():
            a = l.split(' ')
            time_indexes[a[0]] = int(a[1].rstrip()[-8:-5])
    return time_indexes


def read_phenotypic_timestamps():
    timestamps = {}
    with open(TIMESTAMPS_FILE, 'r') as f:
        for l in f.readlines():
            a = l.split(' ')
            timestamps[a[0]] = float(a[1].rstrip())
    return timestamps


def parse_phenotypic_filenames(timestamps):
    """Parse filenames of timelapse phenotypic data"""

    files = {}
    for filename in timestamps:
        slide = filename.split('/')[0]
        position = filename.split('/')[2]
        files.setdefault(slide, {})
        files[slide].setdefault(position, [])
        files[slide][position].append(filename)

    for slide in files:
        assert len(files[slide]) == 90  # 90 positions per slide
        for x in range(101, 146):
            assert "Pos%s" % x in files[slide]
        for x in range(201, 246):
            assert "Pos%s" % x in files[slide]
        for p in files[slide]:
            for t in range(481):
                filename = get_phenotypic_filename(p, "phase", t, slide=slide)
                assert filename in files[slide][p]
            for t in range(241):
                filename = get_phenotypic_filename(p, "fluor", t, slide=slide)
                assert filename in files[slide][p]
    return files


def get_phenotypic_filename(p, c, t, slide=None):
    name = "%s/%s/img_000000%03g.tiff" % (p, c, t)
    if slide is not None:
        return "%s/pheno/%s" % (slide, name)
    else:
        return name


def write_companion(images, file_path):
    # Generate companion OME-XML file
    if not os.path.exists(dirname(file_path)):
        os.makedirs(dirname(file_path))
        logging.info("Created %s" % dirname(file_path))
    create_companion(images=images, out=file_path)

    # Indent XML for readability
    proc = subprocess.Popen(
        ['xmllint', '--format', '-o', file_path, file_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    (output, error_output) = proc.communicate()
    logging.info("Created %s" % file_path)


def create_phenotypic_companions():
    """Phenotypic metadata files"""

    time_indexes = read_phenotypic_time_indexes()
    timestamps = read_phenotypic_timestamps()
    files = parse_phenotypic_filenames(timestamps)
    for slide in files:
        images = []
        # Genotypic metadata generation
        for position in files[slide].keys():
            image = Image(
                position, 2048, 879, 1, 2, 481, order="XYZCT", type="uint16")
            image.add_channel("Phase", -1)
            image.add_channel("Fluorescence", 16711935)

            # Phase images
            for t in range(481):
                relative_path = get_phenotypic_filename(position, "phase", t)
                full_path = get_phenotypic_filename(position, "phase", t,
                                                    slide=slide)
                image.add_tiff(relative_path, c=0, z=0, t=t, planeCount=1)
                plane_options = {
                    "DeltaT": timestamps[full_path],
                    "DeltaTUnit": "s",
                    "ExposureTime": "20",
                    "ExposureTimeUnit": "ms",
                }
                image.add_plane(c=0, z=0, t=t, options=plane_options)

            # Fluorescence images
            for i in range(241):
                relative_path = get_phenotypic_filename(position, "fluor", i)
                full_path = get_phenotypic_filename(position, "fluor", i,
                                                    slide=slide)
                t = time_indexes[full_path]
                plane_options = {
                    "DeltaT": timestamps[full_path],
                    "DeltaTUnit": "s",
                    "ExposureTime": "300",
                    "ExposureTimeUnit": "ms",
                }
                if t == 2 * i:
                    image.add_tiff(relative_path, c=1, z=0, t=t, planeCount=1)
                    if i != 240:
                        image.add_tiff(None, c=1, z=0, t=(2 * i) + 1)
                elif t == (2 * i) + 1:
                    image.add_tiff(None, c=1, z=0, t=2 * i)
                    if t != 481:
                        image.add_tiff(relative_path, c=1, z=0, t=t,
                                       planeCount=1)
                else:
                    raise Exception("Invalid mapping")
                image.add_plane(c=1, z=0, t=t, options=plane_options)
            images.append(image)

        if len(images) == 0:
            continue
        companion_file = join(
            EXPERIMENTA_DIRECTORY, slide, "pheno", slide + '.companion.ome')
        write_companion(images, companion_file)


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
        for i in range(GENO_CYCLES):
            image = Image(
                basename(folder), 2048, 879, 1, 5, 1,
                order="XYZCT", type="uint16")

            image.add_channel("Cy5", -16776961)
            image.add_channel("Cy3", 16711935)
            image.add_channel("TxR", 65535)
            image.add_channel("Fam", -65281)
            image.add_channel("Phase", -1)

            index = str(i + 1).zfill(2)

            image.add_tiff(
                "%s/1_cy5_fluor/%s.tiff" % (basename(folder), index),
                c=0, z=0, t=0)
            image.add_tiff(
                "%s/2_cy3_fluor/%s.tiff" % (basename(folder), index),
                c=1, z=0, t=0)
            image.add_tiff(
                "%s/3_TxR_fluor/%s.tiff" % (basename(folder), index),
                c=2, z=0, t=0)
            image.add_tiff(
                "%s/4_fam_flour/%s.tiff" % (basename(folder), index),
                c=3, z=0, t=0)
            image.add_tiff(
                "%s/phase/%s.tiff" % (basename(folder), index),
                c=4, z=0, t=0)

            companion_file = join(
                geno_directory, basename(folder) + '_round' + index +
                '.companion.ome')
            write_companion(image, companion_file)


if __name__ == "__main__":
    create_phenotypic_companions()
