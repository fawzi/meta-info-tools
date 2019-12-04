from .meta_schema import MetaSchema
from .meta_info import MetaDataType


class JsonSchemaDumper(object):
    def __init__(self, schema, basePath, baseUri=None, suspendable=True):
        self.schema = schema
        self.basePath = basePath
        self.baseUri = baseUri
        self.suspendable = suspendable

    def arraySchema(self, baseType, dim=1, suspendable=None):
        if suspendable is None:
            suspendable = self.suspendable
        if dim == 1:
            dictType = {
                "type": "object",
                "properties": {
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
            return {"oneOf": [arrType, dictType]}
        else:
            return arrType

    def valueSchema(self, metaValue):
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
                        "oneOf": [
                            "string",
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
            description += f"\nThis reference references section {repr(metaValue.meta_referenced_section)}.\n "

        if metaValue.meta_shape:
            dim = len(metaValue.meta_shape)
            val = self.arraySchema(baseType, dim)
        else:
            val = baseType
        if metaValue.meta_repeats:
            val = self.arraySchema(val)
        val["title"] = f"Value {metaValue.meta_parent_section}.{metaValue.meta_name}"
        if metaValue.meta_default_value:
            try:
                v=json.loads(metaValue.meta_default_value)
                val['default'] = v
            except:
                logging.exception(f'Error interpreting default value of {metaValue}')
        if metaValue.meta_enum:
            description += f'\nValid values:\n'
            for enumVal in metaValue.meta_enum:
                description += f'\n* {enumVal.meta_enum_value}: {maybeJoinStr(enumVal.meta_enum_description}\n'
            val['enum']= [ enumVal.meta_enum_value for enumVal in metaValue.meta_enum ]
        if metaValue.meta_examples:
            examples = []
            for e in metaValue.meta_examples:
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
            description += f'\nunits: {metaValue.meta_units}\n'
        if metaValue.meta_query_enum
            description += f'\nmeta_query_enum: {metaValue.meta_query_enum}'
        if metaValue.meta_range_expected
            description += f'\nmeta_range_expected: {metaValue.meta_range_expected}'
        val["description"] = description
        return val

    def sectionSchema(self, section, strict=False):
        prop={}
        for vName, value in sorted(section.valueEntries.items())
            vals[vName] = self.valueSchema(value)
        required=[vName for vName, v in value.meta_required.items() if v.meta_required]
        for sName, s in sorted(section.subSections.items()):
            if strict:
                prop[sName]=self.sectionSchema(s)
            else:
                prop[sName]={ "$ref": f"#/definitions/{sName}" }
        # handle value     meta_required: bool = False
        res={
            "title": f'Section {section.name()}',
            "description": maybeJoinStr(section.section.meta_description),
            "type": "object",
            "properties": prop
        }
        if strict:
            res["additionalProperties"]=false
        else:
            for sName in section.meta_possible_inject:
                prop[sName]={ "$ref": f"#/definitions/{sName}" }
        return res

    def weakSchema(self, rootSections=None):
        'A very compact schema, that might have extra injected subsection (recursive references possible). rootSections if given are to possible root sections that should be in the schema (if not given all root sections are used)'
        if rootSections is None:
            rootSections=sorted(self.rootSections.keys())
        sections=set()
        for rSName in rootSections.keys():
            for path in self.schema.iterateDataPath([self.schema.sections[rSName]]]]):
                sections.add(path[-1].name())
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                sName: self.sectionSchema(self.sections[sName], strict=False) for sName in sorted(sections)}
            "anyOf": [
                { "$ref": f'#/definitions/{sName}' } for sName in rootSections.keys() ]
        }

    def strictSchema(self, rootSections=None):
        'A schema the does not allow recursive references and disallows extra properties'
        if rootSections is None:
            rootSections=sorted(self.rootSections.keys())
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {
                sName: self.sectionSchema(self.dataView[sName],strict=True) for sName in rootSections}
            "anyOf": [
                { "$ref": f'#/definitions/{sName}' } for sName in rootSections ]
        }

    def writeSchemas(self, basePath):
        for rName in self.schema.rootSections.keys():
            def writer(outF):
                json.dump(outF, self.weakSchema([rName]), sort_keys=True)
            
