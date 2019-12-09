#!/usr/bin/env python

# This has to run as user omero-server.
# sudo su omero-server
# cd /tmp
# virtualenv -p /usr/bin/python3 py3
# source py3/bin/activate
# pip install https://github.com/ome/zeroc-ice-py-centos7/\
# releases/download/0.2.1/zeroc_ice-3.6.5-cp36-cp36m-linux_x86_64.whl
# git clone https://github.com/ome/omero-upload.git
# pip install omero-upload/
# cp xyz/upload_attachments.py .
# cp xyz/attachments.txt .
# py3/bin/omero login
# python upload_attachments.poy


import omero.clients
import omero.cli
from omero_upload import upload_ln_s

project_id = 954    # 952
attachment_file = "/tmp/attachments_geno.txt"    # "/tmp/attachments.txt"
link_to_image = False    # True

OMERO_DATA_DIR = '/data/OMERO'
NAMESPACE = 'openmicroscopy.org/idr/analysis/original'
MIMETYPE = 'application/octet-stream'

print("Project id: %d, \
      attachment file: %s, \
      link_to_image: %s, \
      data dir: %s, \
      namespace: %s, \
      mimetype: %s" %
      (project_id, attachment_file, str(link_to_image),
       OMERO_DATA_DIR, NAMESPACE, MIMETYPE))

input("Press key to continue")


def link(conn, target, attachment, is_image):
    fo = upload_ln_s(conn.c, attachment, OMERO_DATA_DIR, MIMETYPE)
    fa = omero.model.FileAnnotationI()
    fa.setFile(fo._obj)
    fa.setNs(omero.rtypes.rstring(NAMESPACE))
    fa = conn.getUpdateService().saveAndReturnObject(fa)
    fa = omero.gateway.FileAnnotationWrapper(conn, fa)
    if is_image:
        tg = conn.getObject("Image", target.getId().getValue())
        tg.linkAnnotation(fa)
    else:
        for d in target:
            tg = conn.getObject("Dataset", d.getId().getValue())
            tg.linkAnnotation(fa)


def process_line(conn, project, line, link_image):
    # /uod/idr/filesets/idr0065-camsund-crispri/20190930-ftp/subpool-6_run-2_EXP-18-BQ3521/analysis/pheno/Pos141/trackedCells.mat
    # /uod/idr/filesets/idr0065-camsund-crispri/20190930-ftp/subpool-6_run-2_EXP-18-BQ3521/analysis/geno/genotypeData.mat
    parts = line.split('/')
    dataset_name = parts[6]

    if link_image:
        pos = parts[9]

    datasets = []
    for dataset in project.linkedDatasetList():
        if link_image:
            if dataset.getName().getValue() == dataset_name:
                for image in dataset.linkedImageList():
                    if image.getName().getValue().endswith("%s]" % pos):
                        link(conn, image, line, link_image)
                        print("Linked attachment %s to image %s" %
                              (line, image.getName().getValue()))
        elif dataset.getName().getValue().startswith(dataset_name):
            datasets.append(dataset)

    if len(datasets) > 0:
        link(conn, datasets, line, link_image)
        print("Linked attachment %s to %d datasets" % (line, len(datasets)))


def main(conn):
    with open(attachment_file) as fp:
        cs = conn.getContainerService()
        param = omero.sys.ParametersI().leaves()
        project = cs.loadContainerHierarchy("Project", [project_id], param)[0]

        line = fp.readline().strip()
        count = 0
        while line and len(line) > 0:
            count += 1
            print("Line %d" % count)
            process_line(conn, project, line, link_to_image)
            line = fp.readline().strip()


if __name__ == '__main__':
    with omero.cli.cli_login() as c:
        conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
        main(conn)
