import unittest
import meta_info
import io
import json

class TestMetaInfo(unittest.TestCase):
	abstractMin="""{
	"meta_name": "test",
	"meta_type": "type-abstract",
	"meta_description": "test description"
}"""
	abstractFull="""{
	"meta_name": "test2",
	"meta_type": "type-abstract",
	"meta_description": "test description",
	"meta_deprecated": false,
	"meta_abstract_types": ["test"]
}"""
	dimMin="""{
	"meta_name": "test",
	"meta_type": "type-dimension",
	"meta_description": "test description",
	"meta_parent_section": "base_sect"
}"""
	dimFull="""{
	"meta_name": "test",
	"meta_type": "type-dimension",
	"meta_description": "test description",
	"meta_deprecated": false,
	"meta_abstract_types": ["test"],
	"meta_data_type": "int",
	"meta_parent_section": "base_sect"
}"""
	valueMin="""{
  "meta_name":"metadict_require_version",
  "meta_description":[
    "Expected version of the dictionary that should be loaded to undestand this ",
    "dictionary and is very long and should be a description split on multiple lines."],
  "meta_parent_section":"metadict_require",
  "meta_data_type":"string"
}"""
	valueFull="""{
  "meta_name":"metadict_require_version",
  "meta_type":"type-value",
  "meta_description":[
    "Expected version of the dictionary that should be loaded to undestand this ",
    "dictionary."],
  "meta_parent_section":"metadict_require",
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
	sectionMin="""{
	"meta_name": "test",
	"meta_type": "type-section",
	"meta_description": "test description"
}"""
	sectionFull="""{
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

	def doTests(self, dumpedStr,expectedClass):
		try:
			d=json.loads(dumpedStr)
		except:
			raise Exception(f"got invalid json: {dumpedStr}")
		e=meta_info.MetaInfoBase.fromDict(d)
		self.assertTrue(isinstance(e,expectedClass))
		outF = io.StringIO()
		e.write(outF)
		s1=outF.getvalue()
		try:
			d2=json.loads(s1)
		except:
			raise Exception(f"write, wrote invalid json: {s1}")
		e2=meta_info.MetaInfoBase.fromDict(d2)
		outF = io.StringIO()
		e2.write(outF)
		s2=outF.getvalue()
		self.assertEqual(s1,s2)
		self.assertEqual(e, e2)
		e2.standardize()
		outF = io.StringIO()
		e2.write(outF)
		s3=outF.getvalue()
		try:
			d3=json.loads(s3)
		except:
			raise Exception(f"write, wrote invalid json after standardization: {s3}")
		e3=meta_info.MetaInfoBase.fromDict(d3)
		e3.standardize(compact=True)
		outF = io.StringIO()
		e3.write(outF)
		s4=outF.getvalue()
		try:
			d4=json.loads(s4)
		except:
			raise Exception(f"write, wrote invalid json after compact standardization: {s4}")
		e4=meta_info.MetaInfoBase.fromDict(d4)
		e4.standardize()
		outF = io.StringIO()
		e4.write(outF)
		s5=outF.getvalue()
		self.assertEqual(s3,s5)
		self.assertEqual(e2,e4)


	def test_abstract(self):
		self.doTests(self.abstractMin, meta_info.MetaAbstract)
		self.doTests(self.abstractFull, meta_info.MetaAbstract)


	def test_value(self):
		self.doTests(self.valueMin, meta_info.MetaValue)
		self.doTests(self.valueFull, meta_info.MetaValue)


	def test_dim(self):
		self.doTests(self.dimMin, meta_info.MetaDimensionValue)
		self.doTests(self.dimFull, meta_info.MetaDimensionValue)
		

	def test_section(self):
		self.doTests(self.sectionMin, meta_info.MetaSection)
		self.doTests(self.sectionFull, meta_info.MetaSection)

if __name__ == '__main__':
	unittest.main()
