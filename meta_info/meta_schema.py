from typing import Union, List, Optional, Dict, Set, Any
from enum import Enum
from pydantic import BaseModel
import hashlib, logging
import json, tempfile
import re
import os, os.path
jd = lambda x: json.dumps(x, sort_keys=True, ensure_ascii=True)
from collections import namedtuple
from meta_info import *


class MetaSchemaSection(BaseModel):
  dictionary: str
  section: MetaSection
  valueEntries: Dict[str, MetaValue]
  subSections: dict  #Dict[str,'MetaSchemaSection']
  instantiatedCopies: dict  #Dict[str,obj]# 'MetaSchemaSection']
  dimensions: Dict[str, MetaDimensionValue]
  injectionBase: Optional[str]
  meta_path: Optional[str]

  def name(self):
    return self.section.meta_name

  @property
  def meta_sub_section_name(self):
    return sorted(self.subSections.keys())

  @property
  def meta_instantiated_at(self):
    return sorted(self.instantiatedCopies.keys())

  def write(self, outF, schema, indent=0):
    """Writes out the meta_info_entry with extra schema related info"""

    def writeExtra(outF, indent):
      """Writes out the extra schema related info"""
      ii = indent * ' '
      outF.write(
        ',\n{ii}"meta_path": {value}'.format(ii=ii, value=jd(self.meta_path)))
      outF.write(',\n{ii}"meta_source_dictionary": {value}'.format(
        ii=ii, value=jd(self.dictionary)))

    ii = indent * ' '
    sName = self.section.meta_name
    outF.write(f'{{\n{ii}  "meta_info_entry": [')
    self.section.write(outF, indent=indent + 4, writeExtra=writeExtra)
    outF.write('],\n{ii}  "meta_sub_section_name": {value}'.format(
      ii=ii, value=jd(self.meta_sub_section_name)))
    outF.write(f',\n{ii}  "meta_value": [')
    comma = ''
    for vName, v in sorted(self.valueEntries.items()):
      outF.write(f'{comma}{{\n{ii}    "meta_info_entry": [')
      comma = ', '

      def writeExtraValue(outF, indent):
        ii = indent * ' '
        outF.write(',\n{ii}"meta_path": {value}'.format(
          ii=ii, value=jd(self.meta_path + '.' + vName)))
        dicts = [
          el.metadict_name
          for el in schema.findMany(vName, MetaType.type_value)
          if el.meta_info_entry.meta_parent_section == sName
        ]
        if len(dicts) != 1:
          raise Exception(
            f'Expected exactly one entry of type value with meta_name {vName} and meta_parent_section {sName}, but got {dicts}'
          )
        outF.write(',\n{ii} "meta_source_dictionary": {value}'.format(
          ii=ii, value=jd(dicts[0])))

      v.write(outF, indent=indent + 4, writeExtra=writeExtraValue)
      outF.write(f']\n{ii}  }}')
    outF.write(f' ]')

    outF.write(f',\n{ii}  "meta_dimension_value": [')
    comma = ''
    for vName, v in sorted(self.dimensions.items()):
      outF.write(f'{comma}{{\n{ii}    "meta_info_entry": [')
      comma = ', '

      def writeExtraDim(outF, indent):
        ii = indent * ' '
        outF.write(',\n{ii}"meta_path": {value}'.format(
          ii=ii, value=jd(self.meta_path + '.' + vName)))
        dicts = [
          el.metadict_name
          for el in schema.findMany(vName, MetaType.type_dimension)
          if el.meta_info_entry.meta_parent_section == sName
        ]
        if len(dicts) != 1:
          raise Exception(
            f'Expected exactly one entry of type dimension with meta_name {vName} and meta_parent_section {sName}, but got several in the following dictionaries {dicts}'
          )
        outF.write(',\n{ii}  "meta_source_dictionary": {value}'.format(
          ii=ii, value=jd(dicts[0])))

      v.write(outF, indent=indent + 4, writeExtra=writeExtraDim)
      outF.write(f']\n{ii}  }}')
    outF.write(f' ]')
    comma = ''
    outF.write(f',\n{ii}  "meta_instantiated_at": [')
    for el in self.meta_instantiated_at:
      outF.write(f'{comma}\n{ii}    {jd(el)}')
      if not comma:
        comma = ', '
    outF.write(f']\n{ii}}}')

  def isPartialSection(self):
    """if this section is a partial section that gets injected in other sections"""
    return not self.injectionBase and (self.section.meta_inject)

  def isInjected(self):
    """If this section is an injected partial section"""
    return bool(self.injectionBase)

  def addSubsection(self, subsection, schema):
    """Adds the given subsection to this section"""
    existingSub = self.subSections.get(subsection.section.meta_name)
    if not existingSub:
      self.subSections[subsection.section.meta_name] = subsection
    else:
      if schema:
        dicts=schema.dictionariesOf(subsection.section.meta_name, metaType=MetaType.type_section)
      else:
        dicts=[]
      if subsection.section == existingSub.section and subsection.dictionary == existingSub.dictionary:
        raise Exception(
        f'Duplicate add of section {subsection.section.meta_name} from dictionary {subsection.dictionary} (known dictionaries {dicts})'
        )
      else:
        raise Exception(
        f'Duplicate section {subsection.section.meta_name} in {existingSub.dictionary} and {subsection.dictionary}: {existingSub.section} vs {subsection.section} (dictionaries:{dicts})'
        )

  def addDimension(self, dimension: MetaDimensionValue, schema):
    existingDim = self.dimensions.get(dimension.meta_name)
    if not existingDim:
      self.dimensions[dimension.meta_name] = dimension
    else:
      if schema:
        dicts=[el.metadict_name for el in schema.findMany(dimension.meta_name, metaType=MetaType.type_dimension) if el.meta_info_entry.meta_parent_section==dimension.meta_parent_section]
      else:
        dicts=[]
      if dimension == existingDim:
        raise Exception(f'Duplicate add of dimension {dimension} (dictionaries: {dicts})')
      else:
        raise Exception(
        f'Duplicate dimension {dimension.meta_name}: {existingDim} vs {dimension} (dictionaries: {dicts})'
        )

  def addValue(self, value: MetaValue, dictionary, schema):
    existing = self.valueEntries.get(value.meta_name)
    if not existing:
      self.valueEntries[value.meta_name] = value
    else:
      if schema:
        dicts=[el.metadict_name for el in schema.findMany(value.meta_name, metaType=MetaType.type_value) if el.meta_info_entry.meta_parent_section==value.meta_parent_section]
      else:
        dicts=[]
      if value == existing:
        raise Exception(
        f'Duplicate add of value {value} from {self.dictionariesOf(value.metaName, metaType=MetaType.type_value)} (dictionaries: {dicts})'
        )
      else:
        # with schema we could use dictionariesOf and return all dictionaries, add extra arg?
        raise Exception(
        f'Duplicate dimension {value.meta_name}: {existing} vs {value} from {dictionary} (dictionaries: {dicts})'
        )

  def writeSchema(self, outF, indent=0, indentIncrement=4):
    ii = indent * ' '
    ij = (indent + indentIncrement) * ' '
    outF.write(f'\n{ii}* ## {self.section.meta_name}')
    for entryName, entry in sorted(self.valueEntries.items()):
      if entry.meta_dimension:
        dims = ' [' + (','.join([str(dim)
                                 for dim in entry.meta_dimension])) + ']'
      else:
        dims = ''
      outF.write(f'\n{ij}- {entryName} ({entry.meta_data_type.value}{dims})')
    for dimName in sorted(self.dimensions.keys()):
      dim = self.dimensions[dimName]
      outF.write(f'\n{ij}* dimension({dimName})')
    for secName in sorted(self.subSections.keys()):
      sec = self.subSections[secName]
      sec.writeSchema(
        outF, indent=indent + indentIncrement, indentIncrement=indentIncrement)

  def copyToInject(self, injectionBase):
    """creates a copy of this to inject in another section"""
    if injectionBase:
      subBase = injectionBase + '.' + self.name()
    else:
      subBase = self.name()
    subS = {
      subName: sub.copyToInject(subBase)
      for subName, sub in sorted(self.subSections.items())
    }
    newSect = self.copy(update={
      'subSections': subS,
      'instantiatedCopies': {},
      'injectionBase': injectionBase
    })
    if subBase in self.instantiatedCopies:
      raise Exception(f'double inject of {self.name()} to {subBase}')
    self.instantiatedCopies[subBase] = newSect
    return newSect


class MetaSchemaAbstract(BaseModel):
  dictionary: str
  abstract_type: MetaAbstract
  sections: Set[str]
  values: Set[str]
  dimensions: Set[str]
  abstractTypes: Set[str]

  @property
  def meta_used_in_sections(self):
    return sorted(self.sections)

  @property
  def meta_used_in_values(self):
    return sorted(self.values)

  @property
  def meta_used_in_dimensions(self):
    return sorted(self.dimensions)

  @property
  def meta_used_in_abstract_types(self):
    return sorted(self.abstractTypes)

  def write(self, outF, schema, indent=0):
    """Writes out the meta_info_entry with extra schema related info"""

    def writeExtra(outF, indent):
      """Writes out the extra schema related info"""
      ii = indent * ' '
      aName = self.abstract_type.meta_name
      aType = schema.findOne(aName, MetaType.type_abstract)
      outF.write(',\n{ii}"meta_source_dictionary": {value}'.format(
        ii=ii, value=jd(aType.metadict_name)))

    ii = indent * ' '
    outF.write(f'{{\n{ii}  "meta_info_entry": [')
    self.abstract_type.write(outF, indent=indent + 4, writeExtra=writeExtra)
    outF.write('],\n{ii}  "meta_used_in_sections": {value}'.format(
      ii=ii, value=jd(self.meta_used_in_sections)))
    outF.write(',\n{ii}  "meta_used_in_values": {value}'.format(
      ii=ii, value=jd(self.meta_used_in_values)))
    outF.write(',\n{ii}  "meta_used_in_dimensions": {value}'.format(
      ii=ii, value=jd(self.meta_used_in_dimensions)))
    outF.write(',\n{ii}  "meta_used_in_abstract_types": {value}'.format(
      ii=ii, value=jd(self.meta_used_in_abstract_types)))
    outF.write(f'\n{ii}}}')


class DataVisitor:
  """Visits the hierarchical data of partial or full section"""

  def shouldVisitSection(self, path):
    return True

  def shouldVisitValues(self, path):
    return False

  def visitValue(self, path, value):
    pass

  def didVisitValues(self, path):
    pass

  def shouldVisitSubsections(self, path):
    return True

  def didVisitSubsections(self, path):
    pass

  def didVisitSection(self, path):
    pass


class JsonDataDumper(DataVisitor):
  """Visits the hierarchical data of partial or full section"""

  def __init__(self,
               indent=0,
               dumpInjected=True,
               dumpPartial=True,
               dumpFullRoot=True):
    self.indent = indent
    self.dumpInjected = dumpInjected
    self.dumpPartial = dumpPartial

  def shouldVisitSection(self, path):
    sec = path[-1]
    if (not self.dumpInjected and sec.isInjected() or
        not self.dumpPartial and sec.isPartialSection()):
      return False
    self.write('{')
    return True

  def shouldVisitValues(self, path):
    return True

  def visitValue(self, path, value):
    pass

  def didVisitValues(self, path):
    pass

  def shouldVisitSubsections(self, path):
    return True

  def didVisitSubsections(self, path):
    pass

  def didVisitSection(self, path):
    pass


KnownTypes = namedtuple("KnownTypes", ["sectionName", "fullTypeName"])
TypeChanges = namedtuple("TypeChanges", ["typeName"])


class ConcreteTypeDefiner(DataVisitor):
  """Visits the types in the reverse order so that no forward declaration is needed.
	Type dumper should dump the definition for the the full type if superName is None, and just the renames otherwise.
	A full dump must still respect the renames, hey give a mapping section > name of the type.
	The name of the type must still be changed in most languages to avoid clashes with field names.
	Typically you will want to just use the visitTypes class method and forget about this type."""

  def __init__(self, schema, typeDumper, knownTypes=None):
    if self.knownTypes:
      self.knownTypes = knownTypes
    else:
      self.knownTypes = {}
    self.typeDumper = typeDumper
    self.pathNames = {}

  @classmethod
  def visitTypes(cls, schema, typeDumper, knownTypes=None):
    newVisitor = cls(schema, typeDumper, knownTypes)
    for secName, sec in ordered(schema.partialSections().items()):
      schema.visitDataPath([sec], newVisitor)
    for secName, sec in ordered(schema.fullRootSections().items()):
      schema.visitDataPath([sec], newVisitor)

  def defineType(self, path, typeName, superName, renames):
    typeDumper(path, typeName, superName, renames)

  def didVisitSection(self, path):
    namePath = '.'.join([el.name() for el in path]) + '.'
    parentPath = '.'.join([el.name() for el in path[:-1]]) + '.'
    renames = self.pathNames.get(namePath, {})
    sec = path[-1]
    injected = False
    for s in path:
      if s.isInjected():
        injected = True
    if injected:
      if renames:
        v = json.dumps(renames, order_keys=True, ensure_ascii=False)
        checksum = base64.b32encode(
          hashlib.sha512(v.encode('utf8')).digest())[:-1]
        fullName = sec.name() + '_' + checksum
        newTypeInfo = KnownTypes(sec.name(), fullName)
        i = len(sec.name()) + 2
        alreadyDumped = False
        while i < len(fullName):
          shortName = fullName[:i]
          existing = self.knownTypes.get(shortName)
          if not existing:
            self.knownTypes[shortName] = newTypeInfo
            break
          elif existing == newTypeInfo:
            alreadyDumped = True
            break
          else:
            i += 1
        parentRenames = self.pathNames.get(parentPath, {})
        parentRenames[sec.name()] = shortName
        self.pathNames[parentPath] = parentRenames
        if not alreadyDumped:
          self.defineType(
            path, typeName=shortName, superName=sec.name(), renames=renames)
      elif not sec.name() in self.knownTypes:
        raise Exception(
          f'Internal error unmodified section {sec.name()} from {namePath[:-1]} is not in knownTypes (should have been dumped already)'
        )
      else:
        pass
    else:  #non injected
      secName = sec.name()
      if secName in self.knownTypes:
        raise Exception(
          f'Normal non injected unmodified section {sec.name()} should not have been dumped yet, but is in knownTypes'
        )
      else:
        self.knownTypes[secName] = KnownTypes(secName, secName)
      self.defineType(path, typeName=secName, superName=None, renames=renames)


SectToInject = namedtuple('SectToInject', [
  'sect', 'sectRegexp', 'requiredAbstract', 'excludedAbstract'
])


class MetaSchema(BaseModel):
  metaInfo: MetaInfo
  mainDictionary: str
  dictionaries: Set[str]
  sections: Dict[str, MetaSchemaSection]
  abstractTypes: Dict[str, MetaSchemaAbstract]
  dimensions: Dict[str, MetaDimensionValue]
  rootSections: Dict[str, MetaSchemaSection]
  dataView: Dict[str, MetaSchemaSection]

  def findMany(self, metaName, metaType=None):
    return self.metaInfo.findMany(metaName, metaType, self.dictionaries)

  def findOne(self, metaName, metaType=None):
    return self.metaInfo.findOne(metaName, metaType, self.dictionaries)

  def dictionariesOf(self, metaName, metaType=None):
    """Returns a list of the dictionaries in which the given metaName is defined"""
    return [x.metadict_name for x in self.findMany(metaName, metaType)]

  def ensureSection(self, sectionName):
    """Ensures that the section with the given name is in the schema (and all its super sections), and returns the corresponding MetaSchemaSection"""
    sAttName = sectionName
    sectionPath = []
    sectionPathNames = []
    foundTop = False
    while sAttName:
      if sAttName in sectionPathNames:
        raise Exception(f'circular ref back to {sAttName} after {superDone}')
      try:
        sAtt = self.metaInfo.findSection(
          sAttName, dictionaryNames=self.dictionaries)
      except:
        raise Exception(
          f'Failed to find {sAttName} climbing up the parents of {sectionPathNames} to ensure {sectionName}'
        )
      existingSection = self.sections.get(sAttName)
      if not existingSection:
        newSection = MetaSchemaSection(
          dictionary=sAtt.metadict_name,
          section=sAtt.meta_info_entry,
          valueEntries={},
          instantiatedCopies={},
          subSections={},
          dimensions={})
        self.sections[sAttName] = newSection
        if sectionPath:
          newSection.addSubsection(sectionPath[-1], self)
        sectionPath.append(newSection)
        sectionPathNames.append(sAttName)
        sAttName = sAtt.meta_info_entry.meta_parent_section
      else:
        if sectionPath:
          existingSection.addSubsection(sectionPath[-1], self)
        sectionPath.append(existingSection)
        sectionPathNames.append(existingSection.meta_path)
        foundTop = True
        break
    if not foundTop and sectionPathNames[-1] not in self.rootSections:
      self.rootSections[sectionPathNames[-1]] = sectionPath[-1]
    sectionPathNames.reverse()
    for i, s in enumerate(sectionPath):
      s.meta_path = '.'.join(sectionPathNames[:len(sectionPathNames) - i])
    return sectionPath[0]

  def partialSections(self):
    return {
      secName: sec
      for secName, sec in self.rootSections.items() if sec.isPartialSection()
    }

  def fullRootSections(self):
    return {
      secName: sec
      for secName, sec in self.rootSections.items()
      if not sec.isPartialSection()
    }

  #def visitDataSectionPaths(self, visit, pristine=False):
  #  """visit all data sections paths for which visit returns true"""
  #  if pristine:
  #    rSects = self.rootSections
  #  else:
  #    rSects = self.dataView
  #  for rSecName, rSec in sorted(rSects.items()):
  #    self.visitSectionPath([rSec], visit)

  #def visitSectionPath(self, path, visit):
  #  """visit all subsection of the given path for which visit returns true
  #  Probably recursive code would be nicer.
  #  Modifies the current path in place (copy if you want to hang it on the next iteration)"""
  #  path = list(path)
  #  minDepth = len(path)
  #  while path:
  #    goDeeper = visit(path)
  #    # go sub
  #    lastS = path[-1]
  #    pathNames = [el.section.meta_name for el in path]
  #    if goDeeper and lastS.subSections:
  #      firstSubSName = sorted(lastS.subSections.keys())[0]
  #      if firstSubSName in pathNames:
  #        raise Exception(
  #          'Section loop, {pathNames} comes back to {firstSubSName}')
  #      path.append(lastS.subSections[firstSubSName])
  #    else:
  #      # go next
  #      while len(path) > minDepth:
  #        lastName = path[-1].section.meta_name
  #        parentS = path[-2]
  #        siblingsNames = sorted(parentS.subSections.keys())
  #        nextIndex = siblingsNames.index(lastName) + 1
  #        if nextIndex < len(parentS.subSections):
  #          path[-1] = parentS.subSections[siblingsNames[nextIndex]]
  #          break
  #        else:
  #          path.pop()
  #      if len(path) == minDepth:
  #        return

  def visitData(self,
                visitor,
                partialSections=True,
                fullSections=True,
                pristine=False):
    """Iterate on all section paths that are partialSections or fullSections"""
    if pristine:
      rSects = self.rootSections
    else:
      rSects = self.dataView
    for secName, sec in sorted(rSects.items()):
      partial = sec.isPartialSection()
      if partial and partialSections or not partial and fullSections:
        self.visitDataPath([sec], visitor)

  def visitDataPath(self, path, visitor):
    if not visitor.shouldVisitSection(path):
      return False
    secNow = path[-1]
    if secNow.valueEntries and visitor.shouldVisitValues(path):
      for valName, val in sorted(secNow.valueEntries.items()):
        visitor.visitValue(path, val)
      visitor.didVisitValues(path)
    res = False
    if secNow.subSections and visitor.shouldVisitSubsections(path):
      res = True
      for secName, sec in sorted(path[-1].subSections.items()):
        newPath = path + [sec]
        self.visitDataPath(newPath, visitor)
      visitor.didVisitSubsections(path)
    visitor.didVisitSection(path)

  def iterateData(self,
                  partialSections=True,
                  fullSections=True,
                  pristine=False):
    """Iterate on all section paths that are partialSections or fullSections"""
    if pristine:
      rSects = self.rootSections
    else:
      rSects = self.dataView
    for secName, sec in sorted(rSects.items()):
      partial = sec.isPartialSection()
      if partial and partialSections or not partial and fullSections:
        yield from self.iterateDataPath([sec])

  def iterateDataPath(self, path):
    """Iterate on all sub section paths starting with the given path"""
    yield path
    for sec in sorted(path[-1].subSections.items()):
      newPath = path + [sec]
      yield from iterateDataPath(newPath)

  def loopIds(self):
    'Loops on all entries ids'
    for sName, s in self.sections.items():
      yield s.section.entryId()
      for vName, v in s.valueEntries.items():
        yield v.entryId()
      for dName, d in s.dimensions.items():
        yield d.entryId()
    for aName, a in self.abstractTypes.items():
      yield a.abstract_type.entryId()

  def addSchemaOfDictionary(self, dict: MetaDictionary):
    for entry in dict.meta_info_entry:
      meta_type = entry.meta_type
      if meta_type == MetaType.type_abstract:
        existingEntry = self.abstractTypes.get(entry.meta_name)
        if not existingEntry:
          self.abstractTypes[entry.meta_name] = MetaSchemaAbstract(
            dictionary=dict.metadict_name,
            abstract_type=entry,
            sections=set(),
            values=set(),
            dimensions=set(),
            abstractTypes=set())
        elif existingEntry != entry:
          raise Exception(
            f'Duplicated abstract type {entry.meta_name}: {entry} vs {existingEntry} ({self.dictionariesOf(entry.meta_name,metaType=MetaType.type_abstract)})'
          )
        else:
          raise Exception(
            f'Duplicated add of abstract type {entry.meta_name} ({self.dictionariesOf(entry.meta_name,metaType=MetaType.type_abstract)})'
          )  # ignore?
      elif meta_type == MetaType.type_dimension:
        existingEntry = self.dimensions.get(entry.meta_name)
        if not existingEntry:
          self.dimensions[entry.meta_name] = entry
          try:
            self.ensureSection(entry.meta_parent_section).addDimension(entry, self)
          except:
            raise Exception(
            f'Failure to find meta_parent_section {entry.meta_parent_section} of dimension {entry.meta_name}'
          )
        elif existingEntry != entry:
          raise Exception(
            f'Duplicated dimension {entry.meta_name}: {entry} vs {existingEntry} ({self.dictionariesOf(entry.meta_name,metaType=MetaType.type_dimension)})'
          )
        else:
          raise Exception(
            f'Duplicated add of abstract type {entry.meta_name} ({self.dictionariesOf(entry.meta_name,metaType=MetaType.type_dimension)})'
          )  # ignore?
      elif meta_type == MetaType.type_section:
        self.ensureSection(entry.meta_name)
      elif meta_type == MetaType.type_value:
        try:
          sec = self.ensureSection(entry.meta_parent_section)
        except:
          raise Exception(
            f'Failure to find meta_parent_section {entry.meta_parent_section} of value {entry.meta_name}'
          )
        sec.addValue(entry, dict.metadict_name, self)
      else:
        raise Exception(
          f'Unexpected meta_type {meta_type} in entry {entry.meta_name} of dictionary {dict.metadict_name}'
        )

  def injectSections(self):
    """Injects the sections that need to be injected, cleans and recreates dataView from scratch"""
    injectable = [
      sec for sec in self.sections.values() if sec.section.meta_inject
    ]
    injectable.sort(key=lambda x: x.section.meta_name)
    nonRootInject = {sect.section.meta_name
                     for sect in injectable
                     }.difference(self.rootSections.keys())
    secToInject = []
    if nonRootInject:
      raise Exception(
        f'Inject of non root sections {nonRootInject} not supported')
    for sToI in injectable:
      for metaInject in sToI.section.meta_inject:
        regexpStr = metaInject.meta_inject_if_section_regexp
        if regexpStr:
          regexpStr2 = r'\A(?:' + regexpStr + r')\Z'
          try:
            regexp = re.compile(regexpStr2)
          except:
            raise Exception(
              f'Could not compile regexp {repr(regexpStr2)} from meta_inject_if_section_regexp of section {sec.section.meta_name}'
            )
        else:
          regexp = re.compile('.*')
        abstractTypesRequired = set()
        abstractTypesToExclude = set()
        if metaInject.meta_inject_if_abstract_type:
          for aType in metaInject.meta_inject_if_abstract_type:
            if aType.startsWith('!'):
              abstractTypesToExclude.add(aType[1:])
            else:
              abstractTypesRequired.add(aType)
        secToInject.append(
          SectToInject(sToI, regexp, abstractTypesRequired,
                       abstractTypesToExclude))

    class InjectChecker(DataVisitor):
      def __init__(self, schema):
        self.schema = schema

      def shouldVisitSection(self, path):
        pastSectNames = [s.section.meta_name for s in path]
        sec = path[-1]
        if sec.section.meta_contains:
          for sName in sec.section.meta_contains:
            if sName in sec.subSections or sName in pastSectNames:
              continue
            sToAdd = self.schema.sections[sName]
            dottedPath = '.'.join(pastSectNames)
            injectedSection = sToAdd.copyToInject(dottedPath)
            pathsToCheck.append(path + [injectedSection])
        for sToI in secToInject:
          if sToI.sect.name() in sec.subSections or sToI.sect.name(
          ) in pastSectNames:
            continue
          if (sToI.sectRegexp.match(sec.section.meta_name) and
              sToI.abstractTypesRequired.issubset(sec.meta_abstract_types) and
              sToI.abstractTypesToExclude.isdisjoint(sec.meta_abstract_types)):
            dottedPath = '.'.join(pastSectNames)
            injectedSection = sToI.copyToInject(dottedPath)
            pathsToCheck.append(path + [injectedSection])
        return True

    # clean old
    self.dataView = {}
    for s in self.sections.values():
      s.instantiatedCopies = {}
    for sName, s in self.rootSections.items():
      self.dataView[sName] = s.copyToInject('')

    pathsToCheck = [[sect]
                    for sName, sect in sorted(self.rootSections.items())]
    pathsToCheck.sort(key=lambda x: x[0].section.meta_name)
    visitor = InjectChecker(self)
    while pathsToCheck:
      pathToCheck = pathsToCheck[0]
      pathsToCheck = pathsToCheck[1:]
      self.visitDataPath(pathToCheck, visitor)

  def linkAbstracts(self):
    """links the usages of the abstract types with its abstract type"""
    for secName, sec in self.sections.items():
      for aStr in sec.section.meta_abstract_types:
        abNow = self.abstractTypes.get(aStr)
        if not abNow:
          raise Exception(
            f'Missing abstract type {aStr} used in section {sec.name()} from dictionary {sec.dictionary}'
          )
        abNow.sections.add(secName)
      for vName, v in sec.valueEntries.items():
        for aStr in v.meta_abstract_types:
          abNow = self.abstractTypes.get(aStr)
          if not abNow:
            raise Exception(
              f'Missing abstract type {aStr} used in value {vName} of section {secName} from dictionary {v.dictionary}'
            )
          abNow.values.add(f'{secName}.{vName}')
    for abName, ab in self.abstractTypes.items():
      for aStr in ab.abstract_type.meta_abstract_types:
        abNow = self.abstractTypes.get(aStr)
        if not abNow:
          raise Exception(
            f'Missing abstract type {aStr} used in abstract type {self.findMany(abName,metaType=MetaType.type_abstract)})'
          )
        abNow.abstractTypes.add(abName)
    for dimName, dim in self.dimensions.items():
      for aStr in dim.meta_abstract_types:
        abNow = self.abstractTypes.get(aStr)
        if not abNow:
          raise Exception(
            f'Missing abstract type {aStr} used in dimension {self.findMany(dimName,metaType=MetaType.type_dimension)}'
          )
        abNow.dimensions.add(f'{dim.meta_parent_section}.{dimName}')

  def extendToDictionary(self, newDictName: str):
    """Modifies this dictionary adding the missing dependencies of newDictName
		The result is equivalent to forDictionary(newDictName) only if self.mainDictionary is in the dependencies of newDictName"""
    newDeps = self.metaInfo.depsOfDict(newDictName)
    oldDeps = self.dictionaries
    toDo = newDeps
    if oldDeps.difference(newDeps):
      logging.warn(
        f'extendending {self.mainDictionary} to {newDictName} that is not a superset will leave extra dictionaries in the schema'
      )
    self.dictionaries = self.dictionaries.union(newDeps)
    self.mainDictionary = newDictName
    for d in toDo:
      dict = metaInfo.dictionaries[d]
      self.addSchemaOfDictionary(dict)
    return self

  def write(self, outF, indent=0):
    "Writes out json version of the schema"
    ii = indent * ' '
    outF.write(
      f'{{\n{ii}  "meta_schema_main_dictionary": {jd(self.mainDictionary)}')
    outF.write(
      f',\n{ii}  "meta_schema_included_dictionary": {jd(sorted(self.dictionaries))}'
    )
    outF.write(f',\n{ii}  "meta_section": [')
    comma = ''
    for sName, s in sorted(self.sections.items()):
      if comma:
        outF.write(comma)
      else:
        comma = ', '
      s.write(outF, indent=indent + 4, schema=self)
    outF.write(' ]')
    outF.write(f',\n{ii}  "meta_abstract": [')
    comma = ''
    for aName, a in sorted(self.abstractTypes.items()):
      if comma:
        outF.write(comma)
      else:
        comma = ', '
      a.write(outF, schema=self, indent=indent + 4)
    outF.write(' ]')
    outF.write(f'\n{ii}}}')

  def writeSchema(self, outF, indent=0, indentIncrement=4):
    ii = indent * ' '
    outF.write(f'# Dictionary {self.mainDictionary}')
    fullSects = self.fullRootSections()
    if fullSects:
      outF.write(f'\n{ii}Data Structure')
      for secName in sorted(fullSects.keys()):
        sec = self.sections[secName]
        sec.writeSchema(outF, indent=indent, indentIncrement=indentIncrement)
    partialSects = self.partialSections()
    if partialSects:
      outF.write(f'\n{ii}PartialSections')
      for secName, sec in sorted(partialSects.items()):
        sec.writeSchema(outF, indent=indent, indentIncrement=indentIncrement)
    if self.abstractTypes:
      outF.write(f'\n{ii}Abstract Types')
    for abstract in sorted(self.abstractTypes.keys()):
      outF.write(f'\n{ii}- {abstractName}')
    outF.write('\n')
    outF.flush()

  @classmethod
  def forDictionary(cls, dictName: str, metaInfo: MetaInfo):
    deps = metaInfo.depsOfDict(dictName)
    schema = MetaSchema(
      metaInfo=metaInfo,
      mainDictionary=dictName,
      dictionaries=deps,
      sections={},
      abstractTypes={},
      dimensions={},
      rootSections={},
      dataView={})
    for dep in deps:
      dict = metaInfo.dictionaries[dep]
      schema.addSchemaOfDictionary(dict)
    schema.injectSections()
    schema.linkAbstracts()
    return schema

