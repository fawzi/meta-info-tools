from typing import Union, List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, ValidationError, validator
import json
import re
import os, os.path
jd = lambda x: json.dumps(x, sort_keys=True, ensure_ascii=True)

def splitStr(string, maxLen = 115):
	"""If the string has newlines or is longer than maxLen ({maxLen}) characters splits it.
	if maxLen is -1 it does not split. It always returns an array of strings""".format(maxLen=maxLen)
	toDo = string.splitlines(keepends=True)[::-1]
	if len(toDo) == 1 and len(string)<maxLen or maxLen == -1:
		return [string]
	res = []
	breakRe=re.compile(r"[\s\[\]\(\)\{\}.,<>;:!|\\/=+\-*&^%$#@?~]")
	while toDo:
		lNow = toDo.pop()
		if len(lNow) <= maxLen:
			res.append(lNow)
		else:
			rNow=lNow[maxLen-1::-1]
			done=False
			for m in breakRe.finditer(rNow):
				i = maxLen - m.start()
				if i > maxLen/2:
					res.append(lNow[:i])
					toDo.append(lNow[i:])
					done = True
				break
			if not done:
				res.append(lNow[:maxLen])
				toDo.append(lNow[maxLen:])
	return res


def maybeJoinStr(value):
	"""If a string was splitted in multiple lines joins it again"""
	t=type(value)
	if issubclass(t, str) or issubclass(t, bytes):
		return value
	return "".join(value)


def writeStrMaybeList(outF, value, indent=0, maxLen=115):
	"""Writes out a string, or a list of strings taking care of escaping it for json.
	Lists of strings are indented with a string per line."""
	t=type(value)
	if issubclass(t, str) or issubclass(t, bytes):
		json.dump(value,outF)
	else:
		newline = ",\n" + (indent+2) * " "
		first = True
		outF.write("[")
		for l in value:
			if first:
				outF.write(newline[1:])
				first=False
			else:
				outF.write(newline)
			json.dump(l, outF)
		outF.write(" ]")


class MetaType(Enum):
	"""the various valid values of meta type"""
	type_dimension="type-dimension"
	type_value="type-value"
	type_abstract="type-abstract"
	type_section="type-section"


class MetaInfoBase(BaseModel):
	"""Base values for all meta infos"""
	meta_name: str
	meta_type: MetaType
	meta_description: Union[str, List[str]]
	meta_deprecated: bool = False
	meta_abstract_types: List[str] = []
	
	def standardize(self, compact=False):
		"""Standardizes the values stored (mainly the description formatting)"""
		if compact:
			self.meta_description = maybeJoinStr(self.meta_description)
		else:
			self.meta_description = splitStr(maybeJoinStr(self.meta_description))

	def writeInternal(self, outF, indent):
		pass

	def write(self, outF, indent=0):
		ii = (indent + 2) * " "
		outF.write(
"""{{
{ii}"meta_name": {meta_name},
{ii}"meta_type": {meta_type},
{ii}"meta_description": """.format(
			ii=ii,
			meta_name = jd(self.meta_name),
			meta_type = jd(self.meta_type.value)))
		writeStrMaybeList(outF, self.meta_description, indent=indent+2)
		if self.meta_deprecated:
			outF.write(',\n{ii}"meta_deprecated": {meta_deprecated}'.format(
				ii=ii, meta_deprecated=jd(self.meta_deprecated)))
		if self.meta_abstract_types:
			outF.write(',\n{ii}"meta_abstract_types": {value}'.format(
				ii=ii, value=jd(self.meta_abstract_types)))
		self.writeInternal(outF, indent)
		outF.write('\n' + (indent * ' ') + '}')
	
	@staticmethod
	def fromDict(d):
		"""initializes a meta info value of the correct subclass from a dictionary"""
		try:
			mtype=MetaType(d.get('meta_type', 'type-value'))
		except:
			raise Exception(f"Failed to instantiate meta_info_entry, invalid meta_type '{d.get(meta_type)}''")
		dd = { k: v for k,v in d.items()}
		#dd['meta_type'] = mtype
		#if 'meta_data_type' in dd:
		#	dd['meta_data_type'] = MetaDataType(dd['meta_data_type'])
		try:
			if mtype == MetaType.type_value:
				el = MetaValue(**dd)
			elif mtype == MetaType.type_abstract:
				el = MetaAbstract(**dd)
			elif mtype == MetaType.type_section:
				el = MetaSection(**dd)
			elif mtype == MetaType.type_dimension:
				el = MetaDimensionValue(**dd)
		except:
			raise Exception(f"Failed to instantiate meta_info_entry of type {mtype} from {dd}")
		return el
		
class MetaEnum(BaseModel):
	"""gives the valid enum values that can be assumed"""
	meta_enum_value: str
	meta_enum_description: Union[str,List[str]]

	def standardize(self, compact=False):
		"""Standardizes the values stored (mainly the description formatting)"""
		if compact:
			self.meta_enum_description = maybeJoinStr(self.meta_enum_description)
		else:
			self.meta_enum_description = splitStr(maybeJoinStr(self.meta_enum_description))
	
	
	def write(self, outF, indent=0):
		"""Reproducible pretty print of meta enum to json"""
		ii = (indent + 2) * " "
		outF.write(
"""{{
{ii}"meta_enum_value": {value},
{ii}"meta_enum_description": """.format(
			ii = ii,
			value = jd(self.meta_enum_value)))
		writeStrMaybeList(outF, self.meta_enum_description, indent=indent+2)
		outF.write("\n" + (indent * " ") + "}")


class MetaQueryEnum(BaseModel):
	"""represents the enum values that one can write in a query.
	These can be a superset of the one stored, to allow for alternate spellings,..."""
	meta_query_expansion: str
	meta_query_values: Optional[List[str]]
	meta_query_regexp: Optional[str]
	
	def write(self, outF, indent=0):
		"""Reproducible pretty print of meta query to json"""
		ii = (indent + 2) * " "
		outF.write(
"""{{
{ii}"meta_query_expansion": {meta_query_expansion}""".format(
			ii=ii,
			meta_query_expansion=jd(self.meta_query_expansion)))
		if self.meta_query_values:
			outF.write(',\n{ii}"meta_query_values": {meta_query_values}'.format(
				ii=ii,
				meta_query_values=jd(self.meta_query_values)))
		if self.meta_query_regexp:
			outF.write(',\n{ii}"meta_query_regexp": {value}'.format(
				ii=ii,
				value=jd(self.meta_query_regexp)))
		outF.write("\n" + (indent * " ") + "}")


class MetaRangeKind(Enum):
	abs_value="abs-value" # The range is for the absolute value of the scalar value (or every component for arrays)
	norm2="norm2" # The range is for the euclidean norm of the value
	utf8_length="utf8-length" # The length of the string value using utf-8 encoding
	repetitions="repetitions" # The number of repetitions for a repeating value

class MetaRange(BaseModel):
	meta_range_kind: MetaRangeKind
	meta_range_minimum: Optional[float]
	meta_range_maximum: Optional[float]
	meta_range_units: Optional[str]

	def write(self, outF, indent=0):
		"""Reproducible pretty print of meta range to json"""
		ii = (indent + 2) * " "
		outF.write(
"""{{
{ii}"meta_range_kind": {value}""".format(
	ii=ii,
	value=jd(self.meta_range_kind.value)))
		if self.meta_range_minimum is not None:
			outF.write(',\n{ii}"meta_range_minimum": {value}'.format(
				ii=ii,
				value=jd(self.meta_range_minimum)))
		if self.meta_range_maximum is not None:
			outF.write(',\n{ii}"meta_range_maximum": {value}'.format(
				ii=ii,
				value=jd(self.meta_range_maximum)))
		if self.meta_range_units:
			outF.write(',\n{ii}"meta_range_units": {value}'.format(
				ii=ii,
				value=jd(self.meta_range_units)))	
		outF.write("\n" + (indent * " ") + "}")	

class MetaDataType(Enum):
	"""The different data types corresponding to a meta value"""
	Int="int"
	Int32="int32"
	Int64="int64"
	Boolean="boolean"
	Reference="reference"
	Float32="float32"
	Float="float"
	Float64="float64"
	String="string"
	Binary="binary"
	Json="json"


class MetaDimension(BaseModel):
	meta_dimension_fixed: Optional[int]
	meta_dimension_symbolic: Optional[str]

	#@validator('meta_dimension_symbolic')
	def either_defined_not_both(cls, v, values, **kwargs):
		if "meta_dimension_fixed" in values:
			if values["meta_dimension_fixed"] is not None:
				if v:
					raise ValueError('only one of meta_dimension_fixed and meta_dimension_symbolic should be defined, not both ({vFix}, {v})'.format(
						vFix=jd(values["meta_dimension_fixed"]),
						v=jd(v)))
			elif v is None:
					raise ValueError('One of meta_dimension_fixed or meta_dimension_symbolic should be defined (none given)')
		return v


	def write(self, outF, indent=0):
		"""Reproducible pretty print of meta dimension to json"""
		ii = (indent + 2) * " "
		outF.write("{")
		comma=''
		if self.meta_dimension_fixed is not None:
			outF.write('{comma}\n{ii}"meta_dimension_fixed": {value}'.format(
				ii=ii, comma=comma,
				value=jd(self.meta_dimension_fixed)))
			comma=','
		if self.meta_dimension_symbolic:
			outF.write('{comma}\n{ii}"meta_dimension_symbolic": {value}'.format(
				ii=ii, comma=comma,
				value=jd(self.meta_dimension_symbolic)))
		outF.write("\n" + (indent * " ") + "}")


class MetaDimensionValue(MetaInfoBase):
	meta_type = MetaType.type_dimension
	meta_data_type: Optional[MetaDataType]
	meta_parent_section: str
	
	def writeInternal(self, outF, indent):
		ii = (indent+2) * ' '
		outF.write(',\n{ii}"meta_parent_section": {value}'.format(
			ii=ii,
			value=jd(self.meta_parent_section)))
		if self.meta_data_type:
			outF.write(',\n{ii}"meta_data_type": {value}'.format(
				ii=ii,
				value=jd(self.meta_data_type.value)))


class MetaValue(MetaInfoBase):
	meta_type = MetaType.type_value
	meta_parent_section: str
	meta_data_type: MetaDataType
	meta_repeats: bool = False
	meta_required: bool = False
	meta_referenced_section: Optional[str]
	meta_dimension: List[MetaDimension] = []
	meta_default_value: Optional[str]
	meta_enum: Optional[List[MetaEnum]]
	meta_query_enum: Optional[List[MetaQueryEnum]]
	meta_range_expected: Optional[List[MetaRange]]
	meta_units: Optional[str]
	
	def standardize(self, compact=False):
		super().standardize(compact=compact)
		if self.meta_enum:
			for e in self.meta_enum:
				e.standardize(compact=compact)


	def writeInternal(self, outF, indent):
		ii = (indent+2) * ' '
		outF.write(',\n{ii}"meta_parent_section": {value}'.format(
			ii=ii,
			value=jd(self.meta_parent_section)))
		if self.meta_data_type:
			outF.write(',\n{ii}"meta_data_type": {value}'.format(
				ii=ii,
				value=jd(self.meta_data_type.value)))
		outF.write(',\n{ii}"meta_repeats": {value}'.format(
			ii=ii,
			value=jd(self.meta_repeats)))
		outF.write(',\n{ii}"meta_required": {value}'.format(
			ii=ii,
			value=jd(self.meta_required)))
		if self.meta_referenced_section:
			outF.write(',\n{ii}"meta_referenced_section": {value}'.format(
				ii=ii,
				value=jd(self.meta_referenced_section)))
		outF.write(f',\n{ii}"meta_dimension": [ ')
		first = True
		for dim in self.meta_dimension:
			if first:
				first = False
			else:
				outF.write(', ')
			dim.write(outF, indent + 2)
		outF.write(' ]')
		if self.meta_default_value is not None:
			outF.write(',\n{ii}"meta_default_value": {value}'.format(
				ii=ii,
				value=jd(self.meta_default_value)))
		first = True
		if self.meta_enum is not None:
			outF.write(',\n{ii}"meta_enum": [ '.format(ii=ii))
			for e in self.meta_enum:
				if first:
					first = False
				else:
					outF.write(', ')
				e.write(outF, indent=indent + 4)
			outF.write(' ]')
		first = True
		if self.meta_query_enum is not None:
			outF.write(',\n{ii}"meta_query_enum": [ '.format(ii=ii))
			for el in self.meta_query_enum:
				if first:
					first = False
				else:
					outF.write(', ')
				el.write(outF, indent=indent + 4)
			outF.write(' ]')
		first = True
		if self.meta_range_expected is not None:
			outF.write(',\n{ii}"meta_range_expected": [ '.format(ii=ii))
			for el in self.meta_range_expected:
				if first:
					first = False
				else:
					outF.write(', ')
				el.write(outF, indent=indent + 4)
			outF.write(' ]')
		if self.meta_units:
			outF.write(',\n{ii}"meta_units": {value}'.format(
				ii=ii,
				value=jd(self.meta_units)))


class MetaSection(MetaInfoBase):
	meta_type = MetaType.type_section
	meta_parent_section: Optional[str]
	meta_repeats: bool = True
	meta_required: bool = False
	meta_chosen_key: Optional[List[str]]
	meta_context_identifier: Optional[List[str]]
	meta_contains: Optional[List[str]]


	def writeInternal(self, outF, indent):
		ii = (indent+2) * ' '
		outF.write(',\n{ii}"meta_parent_section": {value}'.format(
			ii=ii,
			value=jd(self.meta_parent_section)))
		outF.write(',\n{ii}"meta_repeats": {value}'.format(
			ii=ii,
			value=jd(self.meta_repeats)))
		outF.write(',\n{ii}"meta_required": {value}'.format(
			ii=ii,
			value=jd(self.meta_required)))
		if self.meta_chosen_key:
			outF.write(',\n{ii}"meta_chosen_key": {value}'.format(
				ii=ii,
				value=jd(self.meta_chosen_key)))
		if self.meta_context_identifier:
			outF.write(',\n{ii}"meta_context_identifier": {value}'.format(
				ii=ii,
				value=jd(self.meta_context_identifier)))
		if self.meta_contains:
			outF.write(',\n{ii}"meta_contains": {value}'.format(
				ii=ii, value=jd(self.meta_contains)))


class MetaAbstract(MetaInfoBase):
	meta_type = MetaType.type_abstract

MetaInfoEntry=Union[MetaDimensionValue, MetaValue, MetaSection, MetaAbstract]

class MetadictRequire(BaseModel):
	metadict_required_name: str
	metadict_required_version: Optional[str]

	def write(self, outF, indent=0):
		"""reproducible pretty print to json"""
		ii=(indent + 2)*' '
		outF.write('{{\n{ii}"metadict_required_name": {value}'.format(
			ii=ii,
			value=jd(self.metadict_required_name)))
		if self.metadict_required_version is not None:
			outF.write(',\n{ii}"metadict_required_version": {value}'.format(
				ii=ii,
				value=jd(self.metadict_required_version)))
		outF.write('\n'+(indent*' ')+'}')

class MetaDictionary(BaseModel):
	metadict_name: str
	metadict_source: Optional[List[str]]
	metadict_description: Union[str,List[str]]
	metadict_version: Optional[str]
	metadict_require: List[MetadictRequire] = []
	meta_info_entry: List[MetaInfoEntry] = []
	
	@property
	def meta_info_entries(self):
		if self.__meta_info_entries:
			return self.__meta_info_entries
		elif self.meta_info_entry:
			self.__meta_info_entries = {
				el.meta_name: el for el in meta_info_entry
			}
			return self.__meta_info_entries
		else:
			return {}
	
	def standardize(self, compact=False):
		if compact:
			self.metadict_description=maybeJoinStr(self.metadict_description)
		else:
			self.metadict_description=splitStr(maybeJoinStr(self.metadict_description))
		for el in self.meta_info_entry:
			el.standardize(compact=compact)
	
	def write(self, outF, indent=0, writeName=True, writeSource=False):
		outF.write("{")
		ii = (indent+2) * ' '
		comma = ''
		if writeName:
			outF.write('{comma}\n{ii}"metadict_name": {value}'.format(ii=ii,
				comma=comma, value=jd(self.metadict_name)))
			comma=','
		if writeSource:
			outF.write('{comma}\n{ii}"metadict_source": {value}'.format(ii=ii,
				comma=comma, value=jd(self.metadict_source)))
			comma=','
		outF.write('{comma}\n{ii}"metadict_description": '.format(ii=ii, comma=comma))
		writeStrMaybeList(outF, self.metadict_description, indent=indent+2)
		if self.metadict_version is not None:
			outF.write(',\n{ii}"metadict_version": {value}'.format(
				ii=ii,
				value=jd(self.metadict_version)))
		outF.write(f',\n{ii}"metadict_require": [ ')
		first = True
		for el in self.metadict_require:
			if first:
				first = False
			else:
				outF.write(', ')
			el.write(outF, indent = indent + 4)
		outF.write(f',\n{ii}"meta_info_entry": [ ')
		first = True
		for el in self.meta_info_entry:
			if first:
				first = False
			else:
				outF.write(', ')
			el.write(outF, indent = indent + 4)
		outF.write(' ]')
		outF.write('\n' + (indent * ' ') + '}')


	@classmethod
	def fromDict(cls, d):
		try:
			metadict_name = d.get("metadict_name")
			metadict_source = d.get("metadict_source")
			metadict_description = d.get("metadict_description", "")
			metadict_version = d.get("metadict_version")
			metadict_require = [MetadictRequire(**x) for x in d.get("metadict_require", [])]
		except:
			dd = { k:v for k,v in d.items() if k != "meta_info_entry"}
			raise Exception(f"failed to get metadict attributes from {dd}")	
		d_meta_info_entry = d.get("meta_info_entry",[])
		meta_info_entry = []
		for e in d_meta_info_entry:
			meta_info_entry.append(MetaInfoBase.fromDict(e))
		return cls(
			metadict_name=metadict_name,
			metadict_source=metadict_source,
			metadict_description=metadict_description,
			metadict_version=metadict_version,
			metadict_require=metadict_require,
			meta_info_entry=meta_info_entry
		)


def FileLoader(paths: List[str]):
	
	def find(name):
		for basep in paths:
			p=os.path.join(basep, name + ".meta_dictionary.json")
			if os.path.exists(p):
				try:
					d=json.load(open(p, encoding='utf8'))
					if d.get('metadict_name', name) != name:
						raise Exception(f'metadict at {p} has unexpected name ({d["metadict_name"]})')
					d['metadict_name']=name
					p2 = os.path.realpath(os.path.abspath(p))
					uris=d.get('metadict_source', [])
					for pp in [p, p2]:
						uri = 'file://' + pp
						if not uri in uris:
							uris.insert(0, uri)
					d['metadict_source']=uris
					return MetaDictionary.fromDict(d)
				except:				
					raise Exception(f'failure loading dictionary at "{p}"')
		raise Exception(f'could not find dictionary {name} in {paths}')
	
	return find

class MetaInfo(BaseModel):
	dictionaries: Dict[str,MetaDictionary]
	
	def addMetaDict(self, name, metaDict):
		if name in self.dictionaries:
			raise Exception(f'dictionary {name} added twice to MetaInfo')
		self.dictionaries[name]=metaDict
	
	def complete(self, loadDictNamed):
		"""Ensures that all dependent dictionaries are loaded"""
		namesDone=set()
		while len(namesDone) < len(self.dictionaries):
			for n, d in self.dictionaries.items():
				if n not in namesDone:
					namesDone.add(n)
					for dep in d.metadict_require:
						name = dep.metadict_required_name
						if name not in self.dictionaries:
							newD=loadDictNamed(name)
							self.dictionaries[name]=newD
							
		
		
	
	
