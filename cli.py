import argparse
import json
from .conflator import OsmConflator

def main():
    args = argparse.ArgumentParser()
    args.add_argument("--geojson", "-j", help="GeoJSON source file", type=str, default=None)
    args.add_argument("--osm", "-o", help="OSM source file", type=str, default=None)
    args.add_argument("--out-geojson", "-g", help="Output GeoJSON", default=False, action='store_true')
    args.add_argument("--config", "-c", help="Config file", type=str, default="config.json")
    args = args.parse_args()
    if args.geojson and args.osm:
        with open(args.geojson, 'r') as data:
            json_data = json.load(data)
            conflator = OsmConflator()
            with open(args.config, 'r') as config:
                conflator.config = json.load(config)
                properties = conflator.processor(json_data["features"])
                if not args.out_geojson:
                    print(conflator.conflate_osm(properties, args.osm))
                else:
                    print(conflator.ouput_geojson(json_data, properties))
    else:
        print("Usage: osm-conflator --json <filename.geojson> --osm <filename.osm>")
        print("       osm-conflator --json <filename.geojson> --osm <filename.osm> --out-geojson")

if __name__ == "__main__":
    main()
