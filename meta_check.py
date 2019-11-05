from meta_info import MetaType
from meta_schema import MetaSchema
from collections import namedtuple
from pydantic import BaseModel
from enum import Enum
import re

class EntryId(BaseModel):
	"Unique identifier for a meta_info_entry"
	meta_type: MetaType
	meta_name: str
	qualifier: str

class NameCheckLevel(Enum):
	"level of name check"
	strict=1
	normal=2
	weak=3

class ClashKinds(Enum):
	ValueAndDimSameType=1
	NameAndType=2
	NameOnly=4
	LowerCase=8
	NoUnderscore=16
	All=31

class MetaChecker(object):
	def __init__(self, schema):
		self.schema=schema
	
	def validNames(self, level: NameCheckLevel = NameCheckLevel.strict):
		"""checks if the meta name is valid"""
		strictRe=re.compile(r'\A[a-z_][a-z0-9_]*\Z')
		normalRe=re.compile(r'\A[a-zA-Z_][a-zA-Z0-9_]*\Z')
		weakRe=re.compile(r'\A\w+\Z')
		if level==NameCheckLevel.strict:
			nameRe=strictRe
		elif level==NameCheckLevel.weak:
			nameRe=weakRe
		elif level==NameCheckLevel.normal:
			nameRe=normalRe
		else:
			raise Exception(f'Unexpected name check level {level}')
		for e in self.loopIds():
			if not nameRe.match(e.meta_name):
				raise Exception(f"Invalid meta_name for entry {e}")
		
	def loopIds(self):
		'Loops on all entries ids'
		for sName, s in self.schema.sections.items():
			yield EntryId(MetaType.type_section, sName, '')
			for vName,v in s.valueEntries.items():
				yield EntryId(MetaType.type_value, vName, v.meta_parent_section+'.')
			for dName,d in s.dimensions:
				yield EntryId(MetaType.type_dimension, dName, d.meta_parent_section+'.')
		for aName, a in self.schema.abstractTypes.items():
			yield EntryId(MetaType.type_abstract, aName, '')
	
	def clashChecker(self, reducer, msg):
		msgs=[]
		names={}
		for el in self.loopIds():
			name=reducer(el)
			if name is not None:
				names[name]=names.get(name,[])+[el]
		for n,vals in names:
			if len(vals)>1:
				msgs.append(msg.format(items=vals, reducedName=n))
		return msgs

	def checkClashes(self, clashKinds=ClashKinds.All):
		"""Checks if there are clashes between meta names that are technically acceptable"""
		transformer=lambda x:x
		if clashKinds & ClashKinds.LowerCase != 0:
			transformer=lambda x:x.lower()
		if clashKinds & ClashKinds.NoUnderscore != 0:
			transformer=lambda x:transformer(x).replace('_','')
		if clashKinds & ClashKinds.ValueAndDimSameType != 0:
			tt=lambda x: MetaType.type_value if x == MetaType.type_dimension else x
		else:
			tt=lambda x: x.value
		if clashKinds & ClashKinds.NameOnly != 0:
			namer=lambda el: transformer(el.meta_name)
		elif clashKinds & ClashKinds.NameAndType != 0:
			namer=lambda el: f'{tt(el.meta_type).value}:{transformer(el.meta_name)}'
		else: #unique wrt transformer and tt
			lambda el: f'{tt(el.meta_type).value}:{transformer(el.qualifier)}{transformer(el.meta_name)}'
		
		return self.clashChecker(tn, 'Clash of names to {reducedName}: {vals}')

def doChecks(schema, nameCheckLevel = NameCheckLevel.strict, clashKinds=ClashKinds.All):
	checker=MetaChecker(schema)
	checker.validNames(nameCheckLevel)
	checker.checkClashes(clashKinds)
	
