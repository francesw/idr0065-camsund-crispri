import omero.clients
import omero.cli

project_id = 952
NAMESPACE = 'openmicroscopy.org/idr/analysis/original'

def main(conn):
  project = conn.getObject("Project", project_id)
  for ds in project.listChildren():
    ds.removeAnnotations(NAMESPACE)
    ds = conn.getObject("Dataset", ds.getId())
    for img in ds.listChildren():
      img.removeAnnotations(NAMESPACE)

if __name__ == '__main__':
  with omero.cli.cli_login() as c:
    conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
    main(conn)