from .meta_schema import MetaSchema, ConcreteTypeDefiner
from .meta_info import MetaDataType, writeFile, maybeJoinStr
import os, os.path, json


class JsonSchemaDumper(object):
    def __init__(self, schema):
        self.schema = schema

    def arraySchema(self, baseType, dim=1, suspendable=True, directValue=False):
        if dim == 1:
            dictType = {
                "type": "object",
                "properties": {
                    "type": {"const": "array"},
                    "array_data": baseType,
                    "array_indexes": {"type": "array", "items": {"type": "integer"}},
                    "array_stored_length": {"type": "integer"},
                    "array_range": {"type": "array", "items": {"type": "integer"}},
                },
            }
        else:
            dictType = {
                "type": "object",
                "properties": {
                    "type": {"const": f"array_{dim}d"},
                    f"array_{dim}d_flat_data": {"type": "array", "items": baseType},
                    f"array_{dim}d_indexes": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": dim * [{"type": "integer"}],
                        },
                    },
                    f"array_{dim}d_stored_length": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                    f"array_{dim}d_range": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 2,
                            "maxItems": 3,
                        },
                        "minItems": dim,
                        "maxItems": dim,
                    },
                },
            }
        arrType = {"type": "array", "items": baseType}
        for idim in range(1, dim):
            arrType = {"type": "array", "items": arrType}
        if suspendable:
            if directValue:
                return {"anyOf": [arrType, dictType, baseType]}
            else:
                return {"anyOf": [arrType, dictType]}
        else:
            if directValue:
                return {"anyOf": [arrType, baseType]}
            else:
                return arrType

    def valueSchema(self, metaValue, suspendable=True):
        # "null", "array", "object", "integer", "string", "boolean", "number"
        description = [maybeJoinStr(metaValue.meta_description)]
        baseTypeMap = {
            MetaDataType.Int: {"type": "integer"},
            MetaDataType.Int32: {"type": "integer"},
            MetaDataType.Int64: {"type": ["integer", "string"]},
            MetaDataType.Boolean: {"type": "boolean"},
            MetaDataType.Reference: {"type": "integer"},
            MetaDataType.Float32: {"type": "number"},
            MetaDataType.Float: {"type": "number"},
            MetaDataType.Float64: {"type": "number"},
            MetaDataType.String: {"type": "string"},
            MetaDataType.Binary: {
                "type": "object",
                "properties": {
                    "binary_data_stored_size": {
                        "description": "total length in bytes of the data stored",
                        "type": "integer",
                    },
                    "binary_data_range": {
                        "type": "array",
                        "items": [
                            {
                                "type": "integer",
                                "description": "0-based offset giving the start byte index of the data returned",
                            },
                            {
                                "type": "integer",
                                "description": "0-based upper bound (not included) of the byte index of data returned",
                            },
                        ],
                        "additionalItems": False,
                    },
                    "base64_data": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                        "description": "Base 64 encoded binary data either a single string or as an array of strings",
                    },
                },
                "description": "Object storing binary data (or part of it) encoded using base 64 string",
            },
            MetaDataType.Json: {"type": "object"},
        }
        baseType = baseTypeMap[metaValue.meta_data_type]
        if metaValue.meta_referenced_section:
            description.append(
                f"\nThis reference references section {repr(metaValue.meta_referenced_section)}.\n "
            )

        if metaValue.meta_dimension:
            dim = len(metaValue.meta_dimension)
            val = self.arraySchema(baseType, dim, suspendable=suspendable)
        else:
            val = baseType
        if metaValue.meta_repeats:
            val = self.arraySchema(val, suspendable=suspendable, directValue=True)
        val["title"] = f"Value {metaValue.meta_parent_section}.{metaValue.meta_name}"
        if metaValue.meta_default_value:
            try:
                v = json.loads(metaValue.meta_default_value)
                val["default"] = v
            except:
                logging.exception(f"Error interpreting default value of {metaValue}")
        if metaValue.meta_enum:
            description.append(f"\nValid values:\n")
            for enumVal in metaValue.meta_enum:
                description.append(
                    f"\n* {enumVal.meta_enum_value}: {maybeJoinStr(enumVal.meta_enum_description)}\n"
                )
            val["enum"] = [enumVal.meta_enum_value for enumVal in metaValue.meta_enum]
        if metaValue.meta_example:
            examples = []
            for e in metaValue.meta_example:
                if not e.startswith("!"):
                    try:
                        examples.append(json.loads(e))
                    except:
                        logging.error(
                            f"Invalid json in example {repr(e)} in {metaValue}"
                        )
            if examples:
                val["examples"] = examples
        if metaValue.meta_units:
            description.append(f"\nunits: {metaValue.meta_units}\n")
        if metaValue.meta_query_enum:
            description.append(f"\nmeta_query_enum: {metaValue.meta_query_enum}")
        if metaValue.meta_range_expected:
            description.append(
                f"\nmeta_range_expected: {metaValue.meta_range_expected}"
            )
        val["description"] = "".join(description)
        if not metaValue.meta_required:
            return {"anyOf": [val, {"type": "null"}]}
        return val

    def typeDumper(self, path, typeName, superName, renames, suspendable, strict):
        section = path[-1]
        prop = {}
        for vName, value in sorted(section.valueEntries.items()):
            prop[vName] = self.valueSchema(value, suspendable=suspendable)
        required = [
            vName
            for vName, v in sorted(section.valueEntries.items())
            if v.meta_required
        ] + [
            vName
            for vName, v in sorted(section.subSections.items())
            if v.section.meta_required
        ]
        for sName, s in sorted(section.subSections.items()):
            prop[sName] = {"$ref": f"#/definitions/S_{renames.get(sName,sName)}"}
        if not strict:
            for sName in section.meta_possible_inject:
                prop[sName] = {"$ref": f"#/definitions/S_{sName}"}
        tSchema = {
            "title": f"Section {section.name()}",
            "description": maybeJoinStr(section.section.meta_description),
            "type": "object",
            "properties": prop,
        }
        if strict:
            tSchema["additionalProperties"] = False
        sSchema = {"$ref": f"#/definitions/T_{typeName}"}
        if section.section.meta_repeats:
            sSchema = self.arraySchema(
                sSchema, suspendable=suspendable, directValue=True
            )
        res = {f"T_{typeName}": tSchema, f"S_{typeName}": sSchema}
        return res

    def jsonSchema(self, rootSections=None, strict=False, suspendable=True):
        "A very compact schema, that might have extra injected subsection (recursive references possible). rootSections if given are to possible root sections that should be in the schema (if not given all root sections are used)"
        if rootSections is None:
            rootSections = sorted(self.schema.rootSections.keys())
        definitions = {}
        if strict:
            assert 0, "still buggy, to finish"
            definer = ConcreteTypeDefiner(
                self.schema,
                typeDumper=lambda path, typeName, superName, renames: definitions.update(
                    self.typeDumper(
                        path,
                        typeName,
                        superName,
                        renames,
                        suspendable=suspendable,
                        strict=strict,
                    )
                ),
                knownTypes=None,
            )
            for sName in rootSections:
                sec = self.schema.dataView[sName]
                self.schema.visitDataPath([sec], definer)
        else:
            sectsToDo = set(rootSections)
            sectsDone = set()
            while sectsToDo:
                sNow = sectsToDo.pop()
                s = self.schema.sections[sNow]
                toAdd = set(s.subSections.keys()).union(s.possibleInject)
                sectsDone.add(sNow)
                sectsToDo.update(toAdd.difference(sectsDone))
                if f"S_{sNow}" not in definitions:
                    s = self.schema.sections[sNow]
                    definitions.update(
                        self.typeDumper(
                            [s], sNow, "", {}, strict=False, suspendable=suspendable,
                        )
                    )
        res = {
            "$schema": "http://json-schema.org/draft-07/schema#",  # "http://json-schema.org/draft/2019-09/schema",
            "definitions": definitions,
            "anyOf": [{"$ref": f"#/definitions/S_{sName}"} for sName in rootSections],
        }
        return res

    def writeSchemas(
        self, basePath, strict=True, suspendable=True, writeLayout=None, baseUri=".."
    ):
        "writes a schema for each root section at basePath"
        generatedPaths = []
        body = []
        if strict:
            strictName = "Strict"
        else:
            strictName = "Recursive"
        if suspendable:
            suspendableName = "Suspendable"
        else:
            suspendableName = "Simple"
        body.append("<h1>Json Schema {strictName} {suspendableName}</h1>\n<ul>")
        for rName in self.schema.rootSections.keys():
            if basePath:
                if not os.path.exists(basePath):
                    os.makedirs(basePath)
                fName = f"{rName}.json-schema.json"
                body.append(
                    f'  <li><label><a href="{fName}">{rName}</a></label></li>\n'
                )
                p = os.path.join(basePath, fName)
                writeFile(
                    p,
                    lambda outF: json.dump(
                        self.jsonSchema(
                            [rName], strict=strict, suspendable=suspendable
                        ),
                        outF,
                        sort_keys=True,
                        indent=2,
                    ),
                )
                generatedPaths.append(p)
        body.append("</ul>\n")
        if writeLayout:
            p = os.path.join(basePath, "index.html")
            writeLayout(
                p,
                body,
                title=f"{strictName} {suspendableName} Json Schemas",
                basePath=baseUri,
            )
        return generatedPaths


def writeAllSchemas(schema, basePath, pre="", writeLayout=None, baseUri=".."):
    """writes a recursive schema, a strict schena both suspendable and not"""
    generatedPaths = []
    dumper = JsonSchemaDumper(schema)
    for strict in [False]:
        if strict:
            strictName = "strict"
        else:
            strictName = "recursive"
        for suspendable in [True, False]:
            if suspendable:
                suspendableName = "suspendable"
            else:
                suspendableName = "simple"
            p = os.path.join(basePath, f"{pre}{strictName}-{suspendableName}")
            generatedPaths += dumper.writeSchemas(
                p,
                strict=strict,
                suspendable=suspendable,
                writeLayout=writeLayout,
                baseUri=baseUri,
            )
    return generatedPaths
