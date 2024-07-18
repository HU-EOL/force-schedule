import os
import glob
import datetime
from osgeo import ogr, osr

def read_config(path_config):

    s = ""


def create_geopackage(gpkg_path):
    # Create the GeoPackage
    driver = ogr.GetDriverByName('GPKG')
    if os.path.exists(gpkg_path):
        driver.DeleteDataSource(gpkg_path)
    gpkg = driver.CreateDataSource(gpkg_path)
    return gpkg

def create_polygon_layer(gpkg, layer_name):
    # Create spatial reference
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # WGS84

    # Create the polygon layer
    layer = gpkg.CreateLayer(layer_name, srs, ogr.wkbPolygon)

    # Add the tileid field
    field_tileid = ogr.FieldDefn('tileid', ogr.OFTString)
    layer.CreateField(field_tileid)

    return layer

def create_table_layer(gpkg, layer_name):
    # Create the table layer (non-spatial)
    layer = gpkg.CreateLayer(layer_name, geom_type=ogr.wkbNone)

    # Define the fields
    fields = [
        ogr.FieldDefn('tileid', ogr.OFTString),
        ogr.FieldDefn('filename', ogr.OFTString),
        ogr.FieldDefn('filepath', ogr.OFTString),
        ogr.FieldDefn('date_obs', ogr.OFTDate),
        ogr.FieldDefn('date_created', ogr.OFTDate),
        ogr.FieldDefn('qai_exists', ogr.OFTInteger)
    ]

    for field in fields:
        layer.CreateField(field)

    return layer

def collect_tile_data(base_path):
    tiles = []
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            if os.path.isdir(os.path.join(root, dir_name)):
                tiles.append(dir_name)
    return tiles

def add_polygon_feature(layer, tileid):
    # Create a polygon feature for each tileid
    feature_defn = layer.GetLayerDefn()
    feature = ogr.Feature(feature_defn)

    # Here, you should add the geometry of the tile. 
    # As a placeholder, we'll create a simple square polygon.
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(0, 0)
    ring.AddPoint(1, 0)
    ring.AddPoint(1, 1)
    ring.AddPoint(0, 1)
    ring.AddPoint(0, 0)

    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(ring)

    feature.SetGeometry(polygon)
    feature.SetField('tileid', tileid)

    layer.CreateFeature(feature)
    feature = None

def collect_image_data(base_path):
    images = []
    for root, _, files in os.walk(base_path):
        for file_name in files:
            if file_name.endswith('.BOA'):
                tileid = os.path.basename(root)
                filepath = os.path.join(root, file_name)
                date_obs = datetime.datetime.strptime(file_name.split('_')[2], '%Y%m%d').date()
                date_created = datetime.date.fromtimestamp(os.path.getctime(filepath))
                qai_exists = os.path.exists(filepath.replace('.BOA', '.QAI'))

                images.append({
                    'tileid': tileid,
                    'filename': file_name,
                    'filepath': filepath,
                    'date_obs': date_obs,
                    'date_created': date_created,
                    'qai_exists': 1 if qai_exists else 0
                })
    return images

def add_table_features(layer, images):
    for image in images:
        feature_defn = layer.GetLayerDefn()
        feature = ogr.Feature(feature_defn)

        feature.SetField('tileid', image['tileid'])
        feature.SetField('filename', image['filename'])
        feature.SetField('filepath', image['filepath'])
        feature.SetField('date_obs', image['date_obs'].strftime('%Y-%m-%d'))
        feature.SetField('date_created', image['date_created'].strftime('%Y-%m-%d'))
        feature.SetField('qai_exists', image['qai_exists'])

        layer.CreateFeature(feature)
        feature = None

def main(base_path, gpkg_path):
    # Create the GeoPackage
    gpkg = create_geopackage(gpkg_path)

    # Create layers
    polygon_layer = create_polygon_layer(gpkg, 'tile_polygons')
    table_layer = create_table_layer(gpkg, 'image_metadata')

    # Collect and add tile data
    tiles = collect_tile_data(base_path)
    for tileid in tiles:
        add_polygon_feature(polygon_layer, tileid)

    # Collect and add image data
    images = collect_image_data(base_path)
    add_table_features(table_layer, images)

    # Clean up
    gpkg = None

# Base path to the directory generated by FORCE software
base_path = '/path/to/force/output'
# Path to the GeoPackage
gpkg_path = '/path/to/output.gpkg'

main(base_path, gpkg_path)