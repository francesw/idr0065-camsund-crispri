#! /usr/bin/env python

import csv
import re

PATTERN = re.compile(r'^(.*)_genotyping_round-(\d+)$')

assays_file = 'experimentA/phenotyping_assay_file.txt'
with open(assays_file, 'r') as input_file:

    source_csv = csv.reader(input_file, delimiter='\t')
    source_headers = next(source_csv)

    # Create index
    index = {key: source_headers.index(key) for key in source_headers}

    annotation_file = 'experimentA/idr0065-experimentA-annotation.csv'
    with open(annotation_file, 'w') as output_file:
        target_csv = csv.writer(
            output_file, delimiter=',', lineterminator='\n')

        del source_headers[index["Dataset Name"]]
        target_headers = ['Dataset Name', 'Image Name'] + source_headers
        target_csv.writerow(target_headers)

        for row in source_csv:
            dataset = row[index['Dataset Name']].strip('_phenotyping')
            image = "%s [%s]" % (
                row[index['Assay Name']], row[index['Position']])
            del row[index["Dataset Name"]]
            target_csv.writerow([dataset, image] + [x.rstrip() for x in row])

assays_file = 'experimentB/genotyping_assay_file.txt'
with open(assays_file, 'r') as input_file:
    source_csv = csv.reader(input_file, delimiter='\t')
    source_headers = next(source_csv)

    # Create index
    index = {key: source_headers.index(key) for key in source_headers}

    annotation_file = 'experimentB/idr0065-experimentB-annotation.csv'
    with open(annotation_file, 'w') as output_file:
        target_csv = csv.writer(
            output_file, delimiter=',', lineterminator='\n')

        del source_headers[index["Dataset Name"]]
        target_headers = ['Dataset Name', 'Image Name'] + source_headers
        target_csv.writerow(target_headers)

        for row in source_csv:
            r = PATTERN.match(row[index['Dataset Name']])
            dataset = "%s_round-%02g" % (r.group(1), int(r.group(2)))
            image = "%s [%s]" % (
                row[index['Assay Name']], row[index['Position']])
            del row[index["Dataset Name"]]
            target_csv.writerow([dataset, image] + [x.rstrip() for x in row])
