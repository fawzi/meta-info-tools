from meta_info import MetaType, EntryId
from meta_schema import MetaSchema
from collections import namedtuple
from pydantic import BaseModel
from typing import List
from enum import Enum
import re


class NameCheckLevel(Enum):
  "level of name check"
  strict = 'strict'
  normal = 'normal'
  weak = 'weak'

  def __str__(self):
    return self.value


class ClashKinds(Enum):
  UniqueSectionAttributes = 1
  IgnoreParentSection = 2
  IgnoreType = 4
  IgnoreCase = 8
  IgnoreUnderscores = 16
  IgnoreAll = 31


class NameClash(BaseModel):
  reducedName: str
  entries: List[EntryId]

  def __str__(self):
    return f'{self.reducedName} <- {self.entries}'

class ClashException(Exception):
	def __init__(self, clashes, schema):
		self.clashes=clashes
		self.schema=schema
		super().__init__('Name clashes detected in schema for {self.schema.mainDictionary}:\n  '+'\n  '.join([str(c) for c in self.clashes]))

class MetaChecker(object):
  def __init__(self, schema):
    self.schema = schema

  def validNames(self, level: NameCheckLevel=NameCheckLevel.strict):
    """checks if the meta name is valid"""
    strictRe = re.compile(r'\A[a-z_][a-z0-9_]*\Z')
    normalRe = re.compile(r'\A[a-zA-Z_][a-zA-Z0-9_]*\Z')
    weakRe = re.compile(r'\A\w+\Z')
    if level == NameCheckLevel.strict:
      nameRe = strictRe
    elif level == NameCheckLevel.weak:
      nameRe = weakRe
    elif level == NameCheckLevel.normal:
      nameRe = normalRe
    else:
      raise Exception(f'Unexpected name check level {level}')
    for e in self.schema.loopIds():
      if not nameRe.match(e.meta_name):
        raise Exception(f"Invalid meta_name for entry {e}")

  def clashChecker(self, reducer):
    clashes = []
    names = {}
    for el in self.schema.loopIds():
      name = reducer(el)
      if name is not None:
        names[name] = names.get(name, []) + [el]
    for n, vals in names.items():
      if len(vals) > 1:
        clashes.append(NameClash(entries=vals, reducedName=n))
    if clashes:
      raise ClashException(clashes, self.schema)

  def checkClashes(self, clashKinds=ClashKinds.IgnoreAll.value):
    """Checks if there are clashes between meta names that are technically acceptable"""
    if clashKinds & ClashKinds.IgnoreCase.value != 0:
      if clashKinds & ClashKinds.IgnoreUnderscores.value != 0:
        transformer = lambda x: x.replace('_', '').lower()
      else:
        transformer = lambda x: x.lower()
    elif clashKinds & ClashKinds.IgnoreUnderscores.value != 0:
      transformer = lambda x: x.replace('_', '')
    else:
      transformer = lambda x: x
    if clashKinds & ClashKinds.UniqueSectionAttributes.value != 0:
      tt = lambda x: MetaType.type_value if x == MetaType.type_dimension else x
    else:
      tt = lambda x: x
    if clashKinds & ClashKinds.IgnoreParentSection.value != 0:
      if clashKinds & ClashKinds.IgnoreType.value != 0:
        namer = lambda el: transformer(el.meta_name)
      else:
        namer = lambda el: f'{tt(el.meta_type)}:{transformer(el.meta_name)}'
    elif clashKinds & ClashKinds.IgnoreType.value != 0:
      namer = lambda el: f'{transformer(el.qualifier)}{transformer(el.meta_name)}'
    else:  #unique wrt transformer and tt
      namer = lambda el: f'{tt(el.meta_type).value}:{transformer(el.qualifier)}{transformer(el.meta_name)}'
    self.clashChecker(namer)

    if clashKinds & ClashKinds.UniqueSectionAttributes.value != 0:

      def attributeNames(el):
        if el.meta_type == MetaType.type_section:
          parent = self.schema.sections[
            el.meta_name].section.meta_parent_section
          if parent:
            return f'{transformer(parent)}.{transformer(el.meta_name)}'
          else:
            return transformer(el.meta_name)
        else:
          return f'{transformer(el.qualifier)}{transformer(el.meta_name)}'

      self.clashChecker(attributeNames)


def doChecks(schema,
             nameCheckLevel=NameCheckLevel.strict,
             clashKinds=ClashKinds.IgnoreAll.value):
  checker = MetaChecker(schema)
  checker.validNames(nameCheckLevel)
  checker.checkClashes(clashKinds)

