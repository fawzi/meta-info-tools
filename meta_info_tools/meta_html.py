# version/ dictionaries/dict.meta_dictionary.json
# version/ schema/schema.json
# version/ index.html
# version/ sections
from .meta_schema import MetaSchema, DataVisitor
from .meta_info import MetaType, writeFile, safeRemove, maybeJoinStr
import io, re, os
import markdown


def pathToMetaDesc(meta, basePath):
    """Returns the link to the description of the given meta"""
    mType = meta.meta_type
    metaName = meta.meta_name
    if mType == MetaType.type_section:
        link = os.path.join(basePath, "section", metaName, "index.html")
    elif mType == MetaType.type_value:
        link = os.path.join(
            basePath, "section", meta.meta_parent_section, f"value/{metaName}.html"
        )
    elif mType == MetaType.type_abstract:
        link = os.path.join(basePath, f"abstract/{metaName}/index.html")
    elif mType == MetaType.type_dimension:
        link = os.path.join(
            basePath, "section", meta.meta_parent_section, f"dimension/{metaName}.html"
        )
    else:
        raise Exception(f"Unexpected meta_type {mType} in {metaName}")
    return link


def metaLink(meta, basePath, target="detail", htmlClass="index"):
    "returns the html corresponding to the link going at the given meta_info_entry"
    metaName = meta.meta_name
    if target is None:
        t = ""
    else:
        t = f' target="{target}"'
    return f'<a href="{pathToMetaDesc(meta,basePath)}"{t} class="{htmlClass}">{metaName}</a>'


def md2html(text, basePath="..", schema=None, raiseException=False):
    """Markdown to html conversion (and linking of meta_names)"""
    metaNameRe = re.compile(r"(\b[a-zA-Z0-9]*_[a-zA-Z0-9_]+\b|\bXXX[0-9]+XXX\b)")
    xxxRe = re.compile(r"(\bXXX[0-9]+XXX\b)")
    modif = metaNameRe.split(maybeJoinStr(text))
    toRepl = set()
    for i in range(1, len(modif), 2):
        toRepl.add(modif[i])
    ii = 0
    repl = {}
    backR = {}
    for metaName in toRepl:
        if xxxRe.match(metaName):
            repl[metaName] = metaName
            backR[metaName] = metaName
        else:
            r = f"XXX{ii}XXX"
            while r in toRepl:
                ii += 1
                r = f"XXX{ii}XXX"
            repl[metaName] = r
            metas = schema.findMany(metaName)
            if metas:
                if len(metas) == 1:
                    meta = metas[0]
                    link = pathToMetaDesc(meta.meta_info_entry, basePath)
                else:
                    link = os.path.join(basePath, f"meta/{metaName}.html")
                backR[r] = f'<a href="{link}">{metaName}</a>'
            else:
                backR[r] = r
    for i in range(1, len(modif), 2):
        modif[i] = repl[modif[i]]
    try:
        html = markdown.markdown("".join(modif))
    except:
        if raiseException:
            raise
        else:
            logging.exception(f"interpreting markdown {repr(text)} failed")
            html = text
    splitRes = xxxRe.split(html)
    for i in range(1, len(splitRes), 2):
        placeholder = splitRes[i]
        if not placeholder in backR:
            logging.warn(
                f"Unknown placeholder {repr(placeholder)} when evaluating markdown"
            )
        else:
            splitRes[i] = backR[placeholder]
    return "".join(splitRes)


def metaTypeName(metaType):
    "returns a human oriented name for the meta type"
    if metaType == MetaType.type_abstact:
        return "abstract type"
    elif metaType == MetaType.type_section:
        return "section"
    elif metaType == MetaType.type_dimension:
        return "dimension"
    elif metaType == MetaType.type_value:
        return "value"
    else:
        raise Exception(f"Unexpected meta type {metaType}")


class DataDumper(DataVisitor):
    """dumps the data structure out as nested html list"""

    def __init__(self, siteWriter, basePath):
        self.siteWriter = siteWriter
        self.basePath = basePath
        self.body = []

    def shouldVisitSection(self, path):
        self.body.append(
            f'<li><a href={pathToMetaDesc(path[-1].section, self.basePath)} target="detail" class="index"><label class="index">{path[-1].name()}</label></a>\n'
        )
        self.body += self.siteWriter.sectionIndex(path[-1], self.basePath)
        self.body.append(f"</li>\n")
        return True

    def shouldVisitSubsections(self, path):
        self.body.append('<ul class="subIndex">\n')
        return True

    def didVisitSubsections(self, path):
        self.body.append("</ul>\n")

    def didVisitSection(self, path):
        self.body.append("</li>\n")


class SiteWriter:
    """Writes out the html with the documentation for the given schema.
	Creates the following structure at basePath:
		
	index.html
	meta_index.html
	meta/<xxx>.html
	css/metaStyle.css
	section/index.html
	section/<yy>/index.html
	section/<yy>/values/<xxx>.html
	section/<yy>/dimensions/<xxx>.html
	abstract/index.html
	abstract/<zzz>/index.html
	data/index.html
	data/<rootSection>/index.html 
	pristine/index.html
	pristine/<rootName>/index.html
	"""

    def __init__(self, schema, basePath):
        self.schema = schema
        self.basePath = basePath
        if not os.path.isdir(basePath):
            os.makedirs(basePath)
        self.generatedPaths = {}

    def addGeneratedPath(self, path):
        pNow = self.generatedPaths
        for d in os.path.relpath(os.path.normpath(path), self.basePath).split("/"):
            if not d in pNow:
                pNow[d] = {}
            pNow = pNow[d]

    def resetToPath(self, basePath):
        "reinitializes the basePath and resets the generatedPaths"
        self.basePath = basePath
        self.generatedPaths = {}

    def writeLayout(self, targetPath, body, title, basePath):
        """writes out the body into a full html page template"""

        def writer(outF):
            outF.write(
                f"""<!doctype html>
	<html lang="en">
	<head>
	  <meta charset="utf-8">
	  <title>{title}</title>
	  <meta name="description" content="Meta info description">
	  <meta name="author" content="meta_tool">
	  <link rel="stylesheet" href="{basePath}/css/metaStyle.css">
	</head>
	<body>
		"""
            )
            for l in body:
                outF.write(l)
            outF.write("</body>\n</html>\n")

        if not os.path.isdir(os.path.dirname(targetPath)):
            os.makedirs(os.path.dirname(targetPath))
        writeFile(targetPath, writer)
        self.addGeneratedPath(targetPath)

    def writeRedirect(path, target):
        """Outputs an html that redicrects to target to a file at path"""

        def writer(outF):
            outF.write(
                """<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <title>Redirecting&hellip;</title>
  <link rel="canonical" href="{target}">
  <script>location="{target}"</script>
  <meta http-equiv="refresh" content="0; url={target}">
  <meta name="robots" content="noindex">
</head>
<body>
  <h1>Redirecting&hellip;</h1>
  <a href="{target}">Click here if you are not redirected.</a>
</body>
</html>
"""
            )

        if not os.path.isdir(os.path.dirname(targetPath)):
            os.makedirs(os.path.dirname(targetPath))
        writeFile(targetPath, writer)
        self.addGeneratedPath(targetPath)

    def writeMetaNameRedirect(self, metaName):
        """Writes out a disambiguation page for the given meta name"""
        metas = self.schema.findMany()
        p = os.path.join(basePath, f"meta/{metaName}.html")
        basePath = ".."
        if len(metas) == 1:
            link = pathToMetaDesc(metas[0], basePath)
            self.writeRedirect(p, link)
        elif metas:
            kinds = {m.meta_type for m in metas}
            body = [f"<h1>Disambiguate {metaName}</h1>\n<dl>\n"]
            for k in sorted(kinds):
                body.append(f"<dt>{k.value}</dt>\n")
                body.append(f"<dd>\n<ul>\n")
                if k in [MetaType.type_value, MetaType.type_dimension]:
                    elements = {
                        m.meta_parent_section: m for m in metas if m.meta_type == k
                    }
                    for parentName, meta in sorted(elements.items()):
                        outF.write(
                            f'<li class="index extraLink">{metaLink(self.sections[parentName].section, basePath)}.{metaLink(meta, basePath)}</li>\n'
                        )
                else:
                    outF.write(
                        f'<li class="index extraLink">{metaLink(meta, basePath)}</li>\n'
                    )
                body.append(f"</ul></dd>")
            body.append(f"</dl>")
            self.writeLayout(
                p, body=body, title=f"Disambiguate {metaName}", basePath=".."
            )
        else:
            raise Exception(
                f"writeMetaNameRedirect called with unkown meta_name {repr(metaName)}"
            )

    def writeMetas(self):
        metaDone = set()
        for sName, s in sorted(self.schema.sections.items()):
            if sName not in metaDone:
                self.writeMetaNameRedirect(sName)
                metaDone.add(sName)
            for valName in sorted(s.valueEntries.keys()):
                if sName not in metaDone:
                    self.writeMetaNameRedirect(sName)
                    metaDone.add(sName)
            for valName in sorted(s.dimensions.keys()):
                if sName not in metaDone:
                    self.writeMetaNameRedirect(sName)
                    metaDone.add(sName)
        for aName, a in sorted(self.schema.abstractTypes.items()):
            if aName not in metaDone:
                self.writeMetaNameRedirect(aName)
                metaDone.add(aName)

    def sectionIndex(self, section, basePath, subSections=False):
        """returns the html with the values, dimensions and optionally subsections of a section"""
        s = section
        sName = s.name()
        body = []
        if not basePath:
            basePath = ""
        elif not basePath.endswith("/"):
            basePath = basePath + "/"
        if s.valueEntries:
            body.append('<ul class="subIndex">\n')
            for vName, v in sorted(s.valueEntries.items()):
                if v.meta_dimension:
                    dims = (
                        " ["
                        + (",".join([str(dim) for dim in entry.meta_dimension]))
                        + "]"
                    )
                else:
                    dims = ""
                body.append(
                    f' <li class="subIndex" id="IV-{sName}-{vName}"><a href="{basePath}section/{sName}/value/{vName}.html" target="detail" class="index"><label class="subIndex">{vName} ({v.meta_data_type.value}{dims})</label></a></li>\n'
                )
            body.append("</ul>\n")
        if s.dimensions:
            body.append('<ul class="subIndex">\n')
            for vName, v in sorted(s.dimensions.items()):
                body.append(
                    f' <li class="subIndex" id="ID-{sName}-{vName}"><a href="{basePath}section/{sName}/dimension/{vName}.html" target="detail"><label class="subIndex">{vName} (dim)</label></a></li>\n'
                )
            body.append("</ul>\n")
        if subSections and s.subSections:
            body.append('<ul class="subIndex subSection">\n')
            for subName, subS in sorted(s.subSections.items()):
                body.append(
                    f' <li class="subIndex subSection" id="IS-{subName}"><a href="{basePath}section/{subName}/index.html" target="detail"><label class="subIndex">{subName}</label></a></li>\n'
                )
            body.append("</ul>\n")
        return body

    def writeMetaIndex(self, basePath=None):
        p = os.path.join(self.basePath, "meta_index.html")
        body = []
        body.append('<ul class="index">\n')
        for sName, s in sorted(self.schema.sections.items()):
            body.append(
                f'<li class="index" id="IS-{sName}" ><label class="index"><a href="section/{sName}/index.html" target="detail" class="index">{sName}</label></a>\n'
            )
            body += self.sectionIndex(s, basePath)
            body.append("</li>\n")
        for aName, a in sorted(self.schema.abstractTypes.items()):
            body.append(
                f'<li class="index" id="IA-{aName}"><label class="index"><a href="abstract/{aName}/index.html" target="detail" class="index">{aName}</a></label></li>\n'
            )
        body.append("</ul>\n")
        self.writeLayout(targetPath=p, body=body, title="Meta Index", basePath=basePath)

    def writeCss(self):
        p = os.path.join(self.basePath, "css/metaStyle.css")
        if not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))

        def writer(outF):
            outF.write(
                """
			ul.index,li.index,label.index {}
			.subIndex {}
			.rightTitle { text-align: right; }
			.metaKey {}
			.metaValue {}
			.metaValues {}
			"""
            )
            outF.flush()

        writeFile(p, writer)
        self.addGeneratedPath(p)

    def breadcrumb(self, meta, basePath, target="detail", selfLink=True):
        body = []
        mType = meta.meta_type
        body.append('<div class="breadcrumb">\n')
        if target:
            t = ' target="{target}"'
        else:
            t = ""
        if mType == MetaType.type_abstract:
            pIndex = os.path.join(basePath, f"abstract/index.html")
            body.append(f'<a href="{pIndex}" class="index"{t}>abstract types</a>:\n')
        else:
            pIndex = os.path.join(basePath, f"section/index.html")
            body.append(f'<a href="{pIndex}" class="index"{t}>sections</a>:\n')
        if "meta_parent_section" in meta.allSetKeys():
            sParent = self.schema.sections[meta.meta_parent_section]
            for sName in sParent.meta_path.split("."):
                sNow = self.schema.sections[sName]
                body.append(metaLink(sNow.section, basePath, target=target) + ".")
        if selfLink:
            body.append(metaLink(meta, basePath, target=target))
        else:
            body.append(meta.meta_name)
        body.append("\n</div>\n")
        return body

    def metaDesc(self, meta, basePath):
        """returns an array with the description of the given meta_info_entry"""
        ss = self.schema
        mType = meta.meta_type
        metaName = meta.meta_name
        keys = set(meta.allSetKeys())
        handledKeys = [
            "meta_name",
            "meta_type",
            "meta_description",
            "meta_parent_section",
            "meta_required",
            "meta_repeats",
        ]
        body = []
        body += self.breadcrumb(meta, basePath, target="detail")
        body.append(f"<h1>{metaName}</h1>\n")
        body.append(
            f'<h3 class="rightTitle">{mType.value} from {ss.dictionariesOf(metaName, metaType=mType)}</h3>\n'
        )
        if mType == MetaType.type_section:
            sNow = ss.sections[metaName]
            body += self.sectionIndex(sNow, basePath, subSections=True)
        body.append(f'<div class="metaKey">meta_description</div>\n')
        desc = md2html(meta.meta_description, schema=ss, basePath=basePath)
        body.append(f'<div class="metaValue">{desc}</div>\n')
        body.append(
            f'<div class="metaKey">meta_abstract_types</div>\n<div class="metaValue">'
        )
        for refAName in meta.meta_abstract_types:
            body.append(
                f'  <span class="metaLink">{metaLink(self.schema.abstractTypes[refAName].abstract_type,basePath=basePath)}</span>\n'
            )
        body.append(f"</div>")
        body.append(f'<div class="metaValue">{desc}</div>\n')
        body.append('<dl class="metaValues">\n')
        if "meta_required" in keys:
            body.append(f"<dt>meta_required</dt><dd>{meta.meta_required}</dd>\n")
        if "meta_repeats" in keys:
            body.append(f"<dt>meta_repeats</dt><dd>{meta.meta_repeats}</dd>\n")
        if "meta_parent_section" in keys:
            parentPath = os.path.join(
                basePath, f"section/{meta.meta_parent_section}/index.html"
            )
            body.append(
                f'<dt>meta_parent_section</dt><dd><a href="{parentPath}" target="detail">{meta.meta_parent_section}</a></dd>\n'
            )
        for k in keys.difference(handledKeys):
            body.append(f'<dt class="metaValues">{k}</dt>\n')
            body.append(f'<dd class="metaValues">{getattr(meta,k)}</dd>\n')
        body.append("</dl>\n")
        if mType == MetaType.type_abstract:
            aType = self.schema.abstractTypes[metaName]
            body.append(f"<h2>Uses</h2>\n")
            hasUses = False
            if aType.meta_used_in_sections:
                body.append("<h3>Sections</h3>\n")
                for sName in aType.meta_used_in_sections:
                    body.append(metaLink(ss.sections[sName].section, basePath) + "\n")
            if aType.meta_used_in_values:
                body.append("<h3>Values</h3>\n")
                for svName in aType.meta_used_in_values:
                    names = svName.split(".")
                    if len(names) != 2:
                        raise Exception(
                            f"value name should be section.value, found {svName}"
                        )
                    sName = names[0]
                    vName = names[1]
                    sNow = ss.sections[sName]
                    body.append(
                        metaLink(sNow.section, basePath)
                        + "."
                        + metaLink(sNow.valueEntries[vName], basePath)
                        + "\n"
                    )
            if aType.meta_used_in_dimensions:
                body.append("<h3>Dimensions</h3>\n")
                for sdName in aType.meta_used_in_dimensions:
                    names = sdName.split(".")
                    if len(names) != 2:
                        raise Exception(
                            f"dimension name should be section.dimension, found {sdName}"
                        )
                    sName = names[0]
                    dName = names[1]
                    sNow = ss.sections[sName]
                    body.append(
                        metaLink(sNow.section, basePath)
                        + "."
                        + metaLink(sNow.dimensions[dName], basePath)
                        + "\n"
                    )
            if aType.meta_used_in_abstract_types:
                body.append("<h3>Abstract Types</h3>\n")
                for aName in aType.meta_used_in_abstract_types:
                    body.append(
                        metaLink(ss.abstractTypes[aName].abstract_type, basePath) + "\n"
                    )
        if mType == MetaType.type_section:
            body.append(f"<h2>Data</h2>\n")
            body.append(f"<h3>Pristine</h3>\n")
            sects = sNow.meta_path.split(".")
            rootSect = sects[0]
            p = os.path.join(basePath, f"pristine/{rootSect}/index.html")
            for i, v in enumerate(sects):
                ref = ".".join(sects[: i + 1])
                if i > 0:
                    body.append(".")
                body.append(f'<a href="{p}#S_{ref}" target="data">{v}</a>')
            if sNow.meta_instantiated_at:
                instantiateTree = {}
                for iPath in sNow.meta_instantiated_at:
                    components = iPath.split(".")
                    tNow = instantiateTree
                    for component in components:
                        if component not in tNow:
                            tNow[component] = {}
                        tNow = tNow[component]
                fullRootsNames = set(ss.fullRootSections().keys())
                roots = {
                    cName: c
                    for cName, c in instantiateTree.items()
                    if cName in fullRootsNames
                }
                nonRoots = {
                    cName: c
                    for cName, c in instantiateTree.items()
                    if cName not in fullRootsNames
                }

                def addList(pathNow, levelNow):
                    if not levelNow:
                        return
                    body.append('<ul class="instantiations">')
                    for elName, sub in sorted(levelNow.items()):
                        pathNew = pathNow + [elName]
                        p = os.path.join(basePath, f"data/{pathNew[0]}/index.html")
                        dottedPath = ".".join(pathNew)
                        body.append(
                            f'<li><a href="{p}#S_{dottedPath}" target="data">{elName}</a>'
                        )
                        addList(pathNew, sub)
                        body.append("</li>")
                    body.append("</ul>")

                body.append(f"<h3>Root</h3>\n")
                addList(pathNow=[], levelNow=roots)
                body.append(f"<h3>Injectable</h3>\n")
                addList(pathNow=[], levelNow=nonRoots)
        return body

    def abstractsIndex(self):
        """Returns the index of all abstract types"""
        body = []
        basePath = ".."
        body.append(f'<h1>Abstract types index</h1>\n<ul class="index">\n')
        for aName, a in sorted(self.schema.abstractTypes.items()):
            body.append(f"<li>{metaLink(a.abstract_type,basePath)}</li>\n")
        body.append("</ul>")
        return body

    def writeAbstract(self):
        p = os.path.join(self.basePath, "abstract/index.html")
        self.writeLayout(
            p, body=self.abstractsIndex(), basePath="..", title="Abstract Types Index"
        )
        for aName, a in sorted(self.schema.abstractTypes.items()):
            p = os.path.join(self.basePath, f"abstract/{aName}/index.html")
            aa = a.abstract_type
            body = self.metaDesc(a.abstract_type, basePath="../..")
            self.writeLayout(
                p, body=body, title=f"Abstract Type {aName}", basePath="../.."
            )

    def sectionsIndex(self):
        """Returns the index of all sections"""
        body = []
        basePath = ".."
        body.append(f'<h1>Section index</h1>\n<ul class="index">\n')
        for sName, s in sorted(self.schema.sections.items()):
            body.append(f"<li>{metaLink(s.section,basePath)}\n")
            body += self.sectionIndex(s, basePath)
            body.append("</li>\n")
        body.append("</ul>")
        return body

    def writeSection(self):
        """write all section descriptions and their index"""
        p = os.path.join(self.basePath, "section/index.html")
        self.writeLayout(
            p, body=self.sectionsIndex(), basePath="..", title="Sections Index"
        )
        for sName, s in sorted(self.schema.sections.items()):
            basePath = "../.."
            p = os.path.join(self.basePath, f"section/{sName}/index.html")
            sec = s.section
            body = self.metaDesc(sec, basePath=basePath)
            self.writeLayout(p, body=body, title=f"Section {sName}", basePath=basePath)
            for vName, v in s.valueEntries.items():
                basePath = "../../.."
                p = os.path.join(self.basePath, f"section/{sName}/value/{vName}.html")
                body = self.metaDesc(v, basePath=basePath)
                self.writeLayout(
                    p, body=body, title=f"Value {sName}", basePath=basePath
                )
            for dName, d in s.dimensions.items():
                basePath = "../../.."
                p = os.path.join(
                    self.basePath, f"section/{sName}/dimension/{dName}.html"
                )
                body = self.metaDesc(d, basePath=basePath)
                self.writeLayout(
                    p, body=body, title=f"Dimension {sName}", basePath=basePath
                )

    def dataIndex(self):
        """Returns the index of the data"""
        body = []
        basePath = ".."
        body.append(f'<h1>Data view index</h1>\n<ul class="index">\n')
        if self.schema.fullRootSections():
            body.append(f"<h2>Root</h2>\n")
            body.append('<ul class="index">\n')
            for sName in sorted(self.schema.fullRootSections().keys()):
                body.append(f'<li><a href="{sName}/index.html">{sName}</a></li>')
            body.append("</ul>\n")
        if self.schema.partialSections():
            body.append(f"<h3>Injectable</h3>\n")
            body.append('<ul class="index">\n')
            for sName in sorted(self.schema.partialSections().keys()):
                body.append(f'<li><a href="{sName}/index.html">{sName}</a></li>')
            body.append("</ul>\n")
        return body

    def writeData(self):
        p = os.path.join(self.basePath, "data/index.html")
        self.writeLayout(p, self.dataIndex(), title="Data Index", basePath=".")
        for sName, s in sorted(self.schema.dataView.items()):
            p = os.path.join(self.basePath, f"data/{sName}/index.html")
            dumper = DataDumper(self, basePath="../..")
            dumper.body.append(f'<h1>{sName} data view</h1>\n<ul class="index">\n')
            self.schema.visitDataPath([s], dumper)
            dumper.body.append(f"</ul>\n")
            self.writeLayout(
                p, body=dumper.body, title=f"Data {sName}", basePath="../.."
            )

    def pristineIndex(self):
        """Returns the index of the pristine data"""
        body = []
        basePath = ".."
        body.append(f'<h1>Pristine data view index</h1>\n<ul class="index">\n')
        body.append('<ul class="index">\n')
        for sName in sorted(self.schema.rootSections.keys()):
            body.append(f'<li><a href="{sName}/index.html">{sName}</a></li>')
        body.append("</ul>\n")
        return body

    def writePristine(self):
        p = os.path.join(self.basePath, "pristine/index.html")
        self.writeLayout(
            p, self.dataIndex(), title="Prisitine Data Index", basePath=".."
        )
        for sName, s in sorted(self.schema.rootSections.items()):
            p = os.path.join(self.basePath, f"pristine/{sName}/index.html")
            dumper = DataDumper(self, basePath="../..")
            dumper.body.append(
                f'<h1>{sName} pristine data view</h1>\n<ul class="index">\n'
            )
            self.schema.visitDataPath([s], dumper)
            dumper.body.append(f"</ul>\n")
            self.writeLayout(
                p, body=dumper.body, title=f"Pristine Data {sName}", basePath="../.."
            )

    def writeIndex(self):
        "writes the main index"
        body = [
            """
    <table>
      <tr> <td rowspan="2">
	  <iframe src="meta_index.html" height="615" width="350" name="index"></iframe> </td><td> <iframe src="section/index.html" height="400" width="550" name="detail"></iframe> </td></tr>
      <tr><td><iframe src="data/index.html" height="200" width="550" name="data"></iframe></td></tr>
    </table>
"""
        ]
        p = os.path.join(self.basePath, "index.html")
        self.writeLayout(p, body, title="Index", basePath=".")

    def writeMetaSchema(self):
        "Writes out the meta_schema in json format"
        p = os.path.join(self.basePath, "meta_schema.json")
        writeFile(p, self.schema.write)
        self.addGeneratedPath(p)

    def writeAll(self):
        "Writes out the whole site"
        self.writeMetaIndex()
        self.writeCss()
        self.writeAbstract()
        self.writeSection()
        self.writeData()
        self.writePristine()
        self.writeIndex()
        self.writeMetaSchema()

    def cleanupUnknown(self, pathNow=None, dirNow=None):
        """safely removes unknown files (likely leftover of old versions) renaming them to *.bk files/direcories"""
        if pathNow is None:
            pathNow = self.basePath
        if dirNow is None:
            dirNow = self.generatedPaths
        if not dirNow:
            # do not clean up directories without at least an entry
            return
        inDir = set(os.listdir(pathNow))
        toRm = [os.path.join(pathNow, f) for f in inDir.difference(dirNow.keys())]
        safeRemove(toRm)
        for f, sub in dirNow.items():
            p = os.path.join(pathNow, f)
            if f == "." or f == "..":
                logging.warn(f"generatedFiles contains {f}")
            elif os.path.isdir(p):
                self.cleanupUnknown(p, sub)
