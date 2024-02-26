from django.shortcuts import render
import psycopg2
import json 
import leafmap.kepler as leafmap
import os


# Create your views here.

DBNAME = os.environ.get('DBNAME')
DBPASSWORD = os.environ.get('DBPASSWORD')

def index(request):
       
        m = leafmap.Map(center=[40, -100], zoom=2, height=600, widescreen=True)
        m.load_config('./config.json')
        def get_db_connection():
            return psycopg2.connect(
                dbname=DBNAME,
                user= 'keplerkenya',
                password=DBPASSWORD,
                host='postgresql-keplerkenya.alwaysdata.net',
                port='5432'
            )
        conn = get_db_connection()
        
        # cursor.execute("SELECT * FROM your_table")
        # results = cursor.fetchall()


        def get_polygons_geojson(tableName,layername,propertyName,*args):
            cursor = conn.cursor()
            table_name = tableName
            geometry_column = 'geom'
            # Create a cursor to execute SQL queries
            with cursor:
                print(args)
                # Join all the columns specified in *args into a comma-separated string
                columns_str = ', '.join(args)
                
                # Query to fetch all features and transform the geometry to GeoJSON
                sql_query = f"SELECT ST_AsGeoJSON(ST_ForcePolygonCCW(ST_Transform(ST_SetSRID({geometry_column},4326),4326))) AS geometry, {columns_str} FROM {table_name};"
                cursor.execute("ROLLBACK")
                conn.commit()
                cursor.execute(sql_query)

                # Fetch all rows
                rows = cursor.fetchall()
                print(rows)
            # Create a GeoJSON FeatureCollection
            geojson_data = {
                "type": "FeatureCollection",
                "features": []
            }

            for row in rows:
                try:
                    # row[0] contains the GeoJSON string, apply json.loads to it
                    feature = {
                        "type": "Feature",
                        "geometry": json.loads(row[0]),
                        "properties": {
                            f"{propertyName}": row[1], 
                            f"condition":row[2],  # Add the CAW value
                            "lineWidth": 1.5,
                        }
                    }
                    geojson_data["features"].append(feature)
                except (json.JSONDecodeError, TypeError) as e:
                    # Handle the error, e.g., print a warning or skip the feature
                    print(f"Error decoding JSON for row: {row}. Error: {e}")
            visConfig = {"visConfig" : {
              "strokeWidth": 1, 
              "strokeColor": [130, 154, 227], 
              "filled": True,
              "opacity": 0.8
            }
            }
            
            # st.write(geojson_data)
            m.add_geojson(geojson_data, layer_name=f"{layername}")
            return geojson_data

        get_polygons_geojson('\"nairobi-roads-real\"','roads','ROAD NO','roadno','condition')
        get_polygons_geojson('\"nairobi_roads\"','roads_all','Type','highway','smoothness')
        # m = leafmap.Map(center=[20, 0], zoom=1)
        in_shp = "C:/Users/hp/Documents/Qgis/Data/Kenya_Census_2019/Kenya_Census_2019/Kenya_Census_2019.shp"
        m.add_shp(in_shp, "County Population")
        # get_polygons_geojson(cursor,'wards_arc60')
        context = {
            'map':m.to_html()
        }
        
        return render(request, 'map.html', context)