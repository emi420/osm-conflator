import xml.etree.ElementTree as ET
import json

class OsmConflator:

    config = {}

    def get_value(self, tag, props, config):
        if tag in self.config["invalid_values"]:
            if props[tag].lower().strip() in self.config["invalid_values"][tag]:
                return None

        if "$or" in config:
            valid = False
            for value in config["$or"]:
                k = list(value.keys())[0]
                v = list(value.values())[0]
                if k in props and props[k] == v:
                    valid = True
            if not valid:
                return None

        if "prop" in config:
            value = props[config["prop"]]
            if tag in self.config["transform"]:
                if "strip" in self.config["transform"][tag]:
                    value = value.strip()
                if "title" in self.config["transform"][tag]:
                    value = value.title()
            return value

        elif "value" in config:
            return config["value"]

    def processor(self, features):
        result = {}
        for feature in features:
            props = feature["properties"]
            skip_feature = False

            # Features to skip
            for skip in self.config["skip"]:
                if skip in props and props[skip]:
                    skip_obj = self.config["skip"][skip]
                    skip_type = type(skip_obj)
                    if skip_type == list:
                        for v in self.config["skip"][skip]:
                            if props[skip].lower() == v:
                                skip_feature = True
                    elif skip_type == dict:
                        if "$not" in skip_obj:
                            if props[skip] != skip_obj["$not"]:
                                skip_feature = True

            if not skip_feature:

                properties = {}

                # Tags

                for tag in self.config["tags"]:
                    if tag in props and props[tag]:
                        value = self.get_value(tag, props, self.config["tags"][tag])
                        if value:
                            properties[tag] = value

                # Categories

                for category in self.config["categories"]:
                    if props["category"] == category:
                        for tag in self.config["categories"][category]:
                            value = self.get_value(tag, props, self.config["categories"][category][tag])
                            if value:
                                properties[tag] = value

                result[props["xid"]] = properties

        return result

    def conflate_osm(self, source, dest):

        tree = ET.parse(dest)
        root = tree.getroot()

        osmXML = ET.Element("osm")
        osmXML.set('version', root.attrib['version'])
        osmXML.set('generator', root.attrib['generator'])

        ways = root.findall('.//way')
        refNodes = []

        for way in ways:
            way_id = way.attrib['id']
            if way_id in source:
                for property in source[way_id]:
                    if way.find('tag[@k="{key}"]'.format(key=property)) is None:
                        child = ET.Element("tag")
                        child.set('k',  property)
                        child.set('v', source[way_id][property])
                        way.append(child)

                nodes = way.findall('.//nd')
                for nd in nodes:
                    refNodes.append(nd.attrib['ref'])

                attrs_to_remove = []
                for attrName, attrValue in way.attrib.items():
                    if attrName not in ["id", "version"]:
                        attrs_to_remove.append(attrName)
                for attrName in attrs_to_remove:
                    way.attrib.pop(attrName, None)
                way.set('action', 'modify')
                way.set('visible', 'true')
                osmXML.append(way)

        nodes = root.findall('.//node')
        for node in nodes:
            if node.attrib["id"] in refNodes:
                osmXML.append(node)

        ET.indent(osmXML, '  ')
        return ET.tostring(osmXML, encoding='utf8', xml_declaration=True).decode('utf-8')

    def ouput_geojson(self, json_data, properties):
        for feature in json_data["features"]:
            if feature["properties"]["xid"]:
                featureId = feature["properties"]["xid"]
                feature["properties"] = properties[featureId]
                feature["properties"]["id"] = featureId
        return json.dumps(json_data)

