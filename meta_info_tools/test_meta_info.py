import unittest
from .meta_info import *
import io
import json

metaDictJson = r"""{
  "metadict_name": "meta",
  "metadict_description": [
    "dictionary describing the meta info itself" ],
  "metadict_version": "2.0.0",
  "metadict_required": [  ],
  "meta_info_entry": [ {
      "meta_name": "meta_abstract_types",
      "meta_type": "type-value",
      "meta_description": [
        "A list of all Meta Info of type *type-abstract* of this value" ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": true,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_chosen_key",
      "meta_type": "type-value",
      "meta_description": [
        "The meta_name of a *type-value* (that should be with meta_data_type = *string*) ",
        "that can be used as main unique key for the sections contained in a ",
        "meta_parent_section." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_constraint_expected_meta_info",
      "meta_type": "type-value",
      "meta_description": [
        "Either a meta_name or a '!' and a meta_name.If the meta_info_entry ",
        "corresponding to it has meta_type type-value or type-section then the ",
        "corrsponding value must be either present or absent in all values corresponding ",
        "to the meta_parent_section selectioned.\n",
        "Besides the meta values and sections listed explicitly also all those that are ",
        "sub sections or sub values of meta_parent_section and have all the type-",
        "abstract without '!' of this list in their meta abstract_types must be present. ",
        "Of the remaining sub sections and values all those that have any of the ",
        "abstract types with '!' shound be exclued.\n",
        "Thus the precedence is explicitly named meta_names, then those with abstract ",
        "types without !, and finally those with !.\n",
        "This allows one to check for subtypes by giving an abstract type to the ",
        "attributes belonging to that subtypes." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": true,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_constraint_required_query",
      "meta_type": "type-value",
      "meta_description": [
        "This query if given must be true for all selected values. This is for meta_type=",
        "meta-constraint" ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_constraint_select_query",
      "meta_type": "type-value",
      "meta_description": [
        "Query that must be true for the values that have to satisfy this constraint. ",
        "Typically this is for example a field having a given value." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_contains",
      "meta_type": "type-value",
      "meta_description": [
        "The meta_name of a top level section (meta_type=type-section, ",
        "meta_parent_section=null)  that should be injected into this section" ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": true,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_context_identifier",
      "meta_type": "type-value",
      "meta_description": [
        "The value should be the meta_name of a value (meta_info_entry with meta_type = *",
        "type-value*) contained in this meta_info_entry. I.e. its meta_parent_section ",
        "should be equal to the meta_name of the current meta_info_entry (which should ",
        "be of *type-section*).That value should uniquely and globally identifies every ",
        "section value, even if one does not know the type of the current section. In ",
        "NOMAD we always used the a gid for this purpose." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_data_type",
      "meta_type": "type-value",
      "meta_description": [
        "The basic type of the data corresponding to this meta_info_entry.\n",
        "Formally also *binary* and *json* could be used, but they were avoided until ",
        "now because opaque, and more difficult to document." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_default_value",
      "meta_type": "type-value",
      "meta_description": [
        "String giving the default value that should be assumed if no value is given" ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_description",
      "meta_type": "type-value",
      "meta_description": [
        "Contains a text meant for the users of the meta info, using [mark down format](",
        "https://daringfireball.net/markdown) with the following extensions:\n",
        "\n",
        "* $$ is used to introduce mathematical notation using the latex format,\n",
        "* names containing an ``\\_'' are assumed to refer to other meta info.The ",
        "dictionary is versioned using semantic $a=\\frac{a}{b}$ dollar$$ versioning." ],
      "meta_deprecated": true,
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": true,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_dictionary",
      "meta_type": "type-section",
      "meta_description": [
        "A dictionary collection some meta_info_entry entries, their dependencies.\n",
        "The dictionary is versioned using semantic versioning." ],
      "meta_parent_section": null,
      "meta_repeats": true,
      "meta_required": false,
      "meta_contains": ["meta_info_entry"]
    }, {
      "meta_name": "meta_dimension",
      "meta_type": "type-section",
      "meta_description": [
        "The shape of the multidimensional array used to store the data corrsponding to ",
        "this meta info, either meta_dimension_fixed or meta_dimension_symbolic.\n",
        "Example: [{ ``meta_dimension_symbolic'': ``number_of_atoms''}, {",
        "``meta_dimension_fixed'': 3 }].\n",
        "If no meta_dimension are given the data is a scalar." ],
      "meta_parent_section": "meta_info_entry",
      "meta_repeats": true,
      "meta_required": false
    }, {
      "meta_name": "meta_dimension_fixed",
      "meta_type": "type-value",
      "meta_description": [
        "A fixed dimension of exactly the given size." ],
      "meta_parent_section": "meta_dimension",
      "meta_data_type": "int64",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_dimension_symbolic",
      "meta_type": "type-value",
      "meta_description": [
        "A symbolic (variable) dimension, contains the name of a meta_info_entry with ",
        "meta_type *type-dimension* that represents this dimension." ],
      "meta_parent_section": "meta_dimension",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_enum",
      "meta_type": "type-section",
      "meta_description": [
        "Describes each of the possible values of an enumeration meta_info_entry" ],
      "meta_parent_section": "meta_info_entry",
      "meta_repeats": true,
      "meta_required": false
    }, {
      "meta_name": "meta_enum_description",
      "meta_type": "type-value",
      "meta_description": [
        "The description of the meaning of the meta_enum_value." ],
      "meta_parent_section": "meta_enum",
      "meta_data_type": "string",
      "meta_repeats": true,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_enum_from",
      "meta_type": "type-value",
      "meta_description": [
        "The meta_name of a meta_info_entry from which to take the meta_enum to easily ",
        "share enumeration values across several meta_info_entry" ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_enum_value",
      "meta_type": "type-value",
      "meta_description": [
        "One of the possible values of an enumeration." ],
      "meta_parent_section": "meta_enum",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_example",
      "meta_type": "type-value",
      "meta_description": [
        "Either a serialized json that is a valid example for this value or '!' and a ",
        "serialized json of an invalid value for this" ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": true,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_info_entry",
      "meta_type": "type-section",
      "meta_description": [
        "A dictionary collection some meta_info_entry entries, their dependencies.\n",
        "The dictionary is versioned using sematic versioning." ],
      "meta_parent_section": null,
      "meta_repeats": true,
      "meta_required": false,
      "meta_inject": [{
        "meta_inject_if_section_regexp": "direct.include"
        } ]
    }, {
      "meta_name": "meta_inject",
      "meta_type": "type-section",
      "meta_description": [
        "A set of triteria that will make this section (meta_type=type-section) inject ",
        "in another section (but never into itself, circular dependencies are not ",
        "allowed). This section must be a top level section (without mata_parent_section)",
        " to be injectable." ],
      "meta_parent_section": "meta_info_entry",
      "meta_repeats": true,
      "meta_required": false
    }, {
      "meta_name": "meta_inject_if_abstract_type",
      "meta_type": "type-value",
      "meta_description": [
        "Either the name of an abstract type that is required by all sections this is ",
        "injected in, or '!' and the name of an abstract type that should not be parent ",
        "of any of the sections that this section should be injected in. This further ",
        "refines the selection done by meta_inject_if_section_regexp" ],
      "meta_parent_section": "meta_inject",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_inject_if_section_regexp",
      "meta_type": "type-value",
      "meta_description": [
        "A regular expression (or meta name) that the sections this is injected in need ",
        "to satisfy. Can be defined only in top level sections.\n",
        "Together with meta_inject_if_abstract_type it can be used to define the ",
        "sections in which all the values and sections contained in this section are ",
        "added (injected).\n",
        "If empty this is injected in *no* section." ],
      "meta_parent_section": "meta_inject",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_name",
      "meta_type": "type-value",
      "meta_description": [
        "This is one of the most important properties of a Meta Info as it is used to ",
        "identify it.\n",
        "Only lowercase roman letters, numbers and underscore are allowed.\n",
        "The prefixes t\\_, u\\_, \\_, x\\_ are reserved for temporary, user defined, non ",
        "standard, and code specific Meta Info respectively.\n",
        "Explicit names are preferred to abbreviations, and the name should always ",
        "contain at least an `\\_'.\n",
        "The name can uniquely identify the meta_info_entry in a meta_dictionary or in ",
        "its context section." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_parent_section",
      "meta_type": "type-value",
      "meta_description": [
        "The name of the meta_info_entry with meta_type *type-section*. It is required, ",
        "for *type-value* and optional for type-section. It is what structures the data." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_query_description",
      "meta_type": "type-value",
      "meta_description": [
        "Description of the field to be shown instead of meta_description when this ",
        "field is used for querying" ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": true,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_query_enum",
      "meta_type": "type-section",
      "meta_description": [
        "Describes possible values that can be used to query this field, but are not ",
        "really stored in it." ],
      "meta_parent_section": "meta_info_entry",
      "meta_repeats": true,
      "meta_required": false
    }, {
      "meta_name": "meta_query_expansion",
      "meta_type": "type-value",
      "meta_description": [
        "The query this entry is equivalent to." ],
      "meta_parent_section": "meta_query_enum",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_query_regex",
      "meta_type": "type-value",
      "meta_description": [
        "a regular expression to use instead of the meta_query_values to identify this ",
        "entry" ],
      "meta_parent_section": "meta_query_enum",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_query_values",
      "meta_type": "type-value",
      "meta_description": [
        "The equivalent values that can be sugested for autocompletion" ],
      "meta_parent_section": "meta_query_enum",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_range_expected",
      "meta_type": "type-section",
      "meta_description": [
        "Gives the expected range for the values corresponding to this meta_info_entry" ],
      "meta_parent_section": "meta_info_entry",
      "meta_repeats": true,
      "meta_required": false
    }, {
      "meta_name": "meta_range_kind",
      "meta_type": "type-value",
      "meta_description": [
        "Defines the quantity the range is about." ],
      "meta_parent_section": "meta_range_expected",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_range_maximum",
      "meta_type": "type-value",
      "meta_description": [
        "The maximum expected value" ],
      "meta_parent_section": "meta_range_expected",
      "meta_data_type": "float",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_range_minimum",
      "meta_type": "type-value",
      "meta_description": [
        "The minimum expected value" ],
      "meta_parent_section": "meta_range_expected",
      "meta_data_type": "float",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_range_units",
      "meta_type": "type-value",
      "meta_description": [
        "The units used for the range" ],
      "meta_parent_section": "meta_range_expected",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_referenced_section",
      "meta_type": "type-value",
      "meta_description": [
        "If the datatype is a reference this attribute must give the name of the ",
        "sections that is referenced." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_repeats",
      "meta_type": "type-value",
      "meta_description": [
        "If the value (section) can be repeated several times within a ",
        "meta_parent_section.\n",
        "The default is true for *type-section* and false for *type-value*." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "boolean",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_required",
      "meta_type": "type-value",
      "meta_description": [
        "If each meta_parent_section requires at least a value of this type.\n",
        "Defaults to false." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "boolean",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_type",
      "meta_type": "type-value",
      "meta_description": [
        "Defines the type of meta_info_entry" ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_units",
      "meta_type": "type-value",
      "meta_description": [
        "String giving the units used by default for the data of this Meta Info. They ",
        "should be SI units, or combination of them using ``*'' and ``^$exponent$''." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_value_validate",
      "meta_type": "type-value",
      "meta_description": [
        "Either a regexp or ')uri' or ')uri-reference'." ],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "metadict_description",
      "meta_type": "type-value",
      "meta_description": [
        "A string describing the group of Meta Info contained in the dictionary." ],
      "meta_parent_section": "meta_dictionary",
      "meta_data_type": "string",
      "meta_repeats": true,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "metadict_gid",
      "meta_type": "type-value",
      "meta_description": [
        "A Gid uniquely identifying the dictionary and recursively all its dependencies" ],
      "meta_parent_section": "meta_dictionary",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "metadict_name",
      "meta_type": "type-value",
      "meta_description": [
        "The name of the dictionary." ],
      "meta_parent_section": "meta_dictionary",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "metadict_required",
      "meta_type": "type-section",
      "meta_description": [
        "Describes a dictionary that should be loaded to undestand the current ",
        "dictionary." ],
      "meta_parent_section": "meta_dictionary",
      "meta_repeats": true,
      "meta_required": false
    }, {
      "meta_name": "metadict_required_name",
      "meta_type": "type-value",
      "meta_description": [
        "A list of other dictionaries that should be loaded to undestand this dictionary." ],
      "meta_parent_section": "metadict_required",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "metadict_required_version",
      "meta_type": "type-value",
      "meta_description": [
        "Expected version of the dictionary that should be loaded to undestand this ",
        "dictionary." ],
      "meta_parent_section": "metadict_required",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "metadict_source",
      "meta_type": "type-value",
      "meta_description": [
        "A string identfying the source of this dictionary (for example an url or path)" ],
      "meta_parent_section": "meta_dictionary",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    }, {
      "meta_name": "meta_deprecated",
      "meta_type": "type-value",
      "meta_description": [
        "If the current meta_info_entry is deprecated and should not be used in the future, and might be removed in future versions"],
      "meta_parent_section": "meta_info_entry",
      "meta_data_type": "boolean",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ],
      "meta_default_value": "false"
    }, {
      "meta_name": "metadict_version",
      "meta_type": "type-value",
      "meta_description": [
        "A string containing the version of the dictionary using [Semantic Versioning 2.",
        "0.0](http://semver.org/spec/v2.0.0.html)" ],
      "meta_parent_section": "meta_dictionary",
      "meta_data_type": "string",
      "meta_repeats": false,
      "meta_required": false,
      "meta_dimension": [  ]
    } ]
}"""


def metaMetaDict():
    "returns the embedded meta dictionary (instantiating it anew from json)"
    try:
        d = json.loads(metaDictJson)
    except:
        raise Exception(f"The embedded meta.meta_dictionary.json has invalid json")
    return MetaDictionary.fromDict(d)


def metaMetaInfo():
    "returns a MetaInfo containing the embedded meta dictionary (instantiating it anew)"
    metaI = MetaInfo.empty()
    metaI.addMetaDict(metaMetaDict())
    return metaI


class TestMetaInfo(unittest.TestCase):
    abstractMin = """{
	"meta_name": "test",
	"meta_type": "type-abstract",
	"meta_description": "test description"
}"""
    abstractFull = """{
	"meta_name": "test2",
	"meta_type": "type-abstract",
	"meta_description": "test description",
	"meta_deprecated": false,
	"meta_abstract_types": ["test"]
}"""
    dimMin = """{
	"meta_name": "test",
	"meta_type": "type-dimension",
	"meta_description": "test description",
	"meta_parent_section": "base_sect"
}"""
    dimFull = """{
	"meta_name": "test",
	"meta_type": "type-dimension",
	"meta_description": "test description",
	"meta_deprecated": false,
	"meta_abstract_types": ["test"],
	"meta_data_type": "int",
	"meta_parent_section": "base_sect"
}"""
    constraintMin = """{
	"meta_name": "test",
	"meta_type": "type-constraint",
	"meta_description": "test constraint description",
	"meta_parent_section": "base_sect"
}"""
    constraintFull = """{
	"meta_name": "test",
	"meta_type": "type-constraint",
	"meta_description": "test description",
	"meta_deprecated": false,
	"meta_abstract_types": ["test"],
	"meta_parent_section": "base_sect",
	"meta_constraint_select_query": "test_val1",
	"meta_constraint_required_query": "test_val1=5",
	"meta_constraint_expected_meta_info": [ "meta"]
}"""
    valueMin = """{
  "meta_name":"metadict_required_version",
  "meta_description":[
    "Expected version of the dictionary that should be loaded to undestand this ",
    "dictionary and is very long and should be a description split on multiple lines."],
  "meta_parent_section":"metadict_required",
  "meta_data_type":"string"
}"""
    valueFull = """{
  "meta_name":"metadict_required_version",
  "meta_type":"type-value",
  "meta_description":[
    "Expected version of the dictionary that should be loaded to undestand this ",
    "dictionary."],
  "meta_parent_section":"metadict_required",
  "meta_data_type":"reference",
  "meta_deprecated": false,
	"meta_abstract_types": ["test"],
	"meta_repeats": false,
	"meta_required": false,
	"meta_referenced_section": "sect2",
	"meta_dimension": [
		{ "meta_dimension_fixed": 3
		}, {"meta_dimension_symbolic": "natom"}],
	"meta_default_value": "[0,0,0]",
	"meta_enum": [{
		"meta_enum_value": "value",
		"meta_enum_description": "the base value"}, {
			"meta_enum_value": "alt-value",
			"meta_enum_description": ["the alternate\\n", "value"]}],
	"meta_query_enum": [{
		"meta_query_values": ["pippo1", "pippo2"],
		"meta_query_regexp": "bob.*",
		"meta_query_expansion": "pippo"}],
	"meta_range_expected": [{
		"meta_range_minimum": 45,
		"meta_range_maximum": 0,
		"meta_range_kind": "abs-value",
		"meta_range_units": "m"
	}, {
		"meta_range_minimum": 45,
		"meta_range_kind": "abs-value"
	}], 
	"meta_units": "mm"
}"""
    sectionMin = """{
	"meta_name": "test",
	"meta_type": "type-section",
	"meta_description": "test description"
}"""
    sectionFull = """{
	"meta_name": "test2",
	"meta_type": "type-section",
	"meta_description": "test description",
	"meta_deprecated": false,
	"meta_abstract_types": ["test"],
	"meta_parent_section": "super_section",
	"meta_repeats": true,
	"meta_required": false,
	"meta_chosen_key": ["key_val"],
	"meta_context_identifier": ["key_val"],
	"meta_contains": ["section_x","value_y"],
	"meta_inject":[{"meta_inject_if_section_regexp": "manual\\\\.inject"}]
}"""

    def doTests(self, dumpedStr, expectedClass):
        try:
            d = json.loads(dumpedStr)
        except:
            raise Exception(f"got invalid json: {dumpedStr}")
        e = MetaInfoBase.fromDict(d)
        self.assertTrue(isinstance(e, expectedClass))
        outF = io.StringIO()
        e.write(outF)
        s1 = outF.getvalue()
        try:
            d2 = json.loads(s1)
        except:
            raise Exception(f"write, wrote invalid json: {s1}")
        e2 = MetaInfoBase.fromDict(d2)
        outF = io.StringIO()
        e2.write(outF)
        s2 = outF.getvalue()
        self.assertEqual(s1, s2)
        self.assertEqual(e, e2)
        e2.standardize()
        outF = io.StringIO()
        e2.write(outF)
        s3 = outF.getvalue()
        try:
            d3 = json.loads(s3)
        except:
            raise Exception(f"write, wrote invalid json after standardization: {s3}")
        e3 = MetaInfoBase.fromDict(d3)
        e3.standardize(compact=True)
        outF = io.StringIO()
        e3.write(outF)
        s4 = outF.getvalue()
        try:
            d4 = json.loads(s4)
        except:
            raise Exception(
                f"write, wrote invalid json after compact standardization: {s4}"
            )
        e4 = MetaInfoBase.fromDict(d4)
        e4.standardize()
        outF = io.StringIO()
        e4.write(outF)
        s5 = outF.getvalue()
        self.assertEqual(s3, s5)
        self.assertEqual(e2, e4)

    def test_abstract(self):
        self.doTests(self.abstractMin, MetaAbstract)
        self.doTests(self.abstractFull, MetaAbstract)

    def test_value(self):
        self.doTests(self.valueMin, MetaValue)
        self.doTests(self.valueFull, MetaValue)

    def test_dim(self):
        self.doTests(self.dimMin, MetaDimensionValue)
        self.doTests(self.dimFull, MetaDimensionValue)

    def test_constraints(self):
        self.doTests(self.constraintMin, MetaConstraint)
        self.doTests(self.constraintFull, MetaConstraint)

    def test_section(self):
        self.doTests(self.sectionMin, MetaSection)
        self.doTests(self.sectionFull, MetaSection)

    def test_meta_dictionary(self):
        mDict = metaMetaDict()

    def test_meta_info(self):
        mInfo = metaMetaInfo()


if __name__ == "__main__":
    unittest.main()
