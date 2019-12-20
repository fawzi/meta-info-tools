# version/ dictionaries/dict.meta_dictionary.json
# version/ schema/schema.json
# version/ index.html
# version/ sections
from .meta_schema import MetaSchema, DataVisitor
from .meta_info import MetaType, writeFile, safeRemove, maybeJoinStr
from .meta_json_schema import writeAllSchemas
import io, re, os, json, logging
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
    metaNameRe = re.compile(r"(\b[a-zA-Z0-9]*_[a-zA-Z0-9_]+\b|XXY[0-9]+YXX|\$[^$]*\$)")
    xxxRe = re.compile(r"(XXY[0-9]+YXX)")
    metaRe = re.compile(r"(\b[a-zA-Z0-9]*_[a-zA-Z0-9_]+\b)")
    mathRe = re.compile(r"\$[^$]*\$")
    modif = metaNameRe.split(maybeJoinStr(text))
    toRepl = set()
    for i in range(1, len(modif), 2):
        toRepl.add(modif[i])
    ii = 0
    repl = {}
    backR = {}
    logging.debug(f"md2html toRepl: {toRepl}")
    for toReplace in toRepl:
        ii += 1
        r = f"XXY{ii}YXX"
        while r in toRepl:
            ii += 1
            r = f"XXY{ii}YXX"
        if metaRe.match(toReplace):
            repl[toReplace] = r
            metas = schema.findMany(toReplace)
            if metas:
                if len(metas) == 1:
                    meta = metas[0]
                    link = pathToMetaDesc(meta.meta_info_entry, basePath)
                else:
                    link = os.path.join(basePath, f"meta/{toReplace}.html")
                backR[r] = f'<a href="{link}">{toReplace}</a>'
            else:
                backR[r] = toReplace
        elif mathRe.match(toReplace):
            if toReplace == "$$":
                repl[toReplace] = "$"
                # no back replacement
            else:
                repl[toReplace] = r
                backR[r] = (
                    "<span class='math'>"
                    + toReplace[1:-1].replace("<", "\\lt ").replace(">", "\\gt ")
                    + "</span>"
                )
        else:
            repl[toReplace] = toReplace
            if xxxRe.match(toReplace):
                backR[toReplace] = toReplace
    logging.debug(f"md2html repl: {repl}")
    logging.debug(f"md2html backR: {backR}")
    for i in range(1, len(modif), 2):
        modif[i] = repl[modif[i]]
    logging.debug(f"md2html to markdown: {''.join(modif)}")
    try:
        html = markdown.markdown("".join(modif))
    except:
        if raiseException:
            raise
        else:
            logging.exception(f"interpreting markdown {repr(text)} failed")
            html = text
    splitRes = xxxRe.split(html)
    logging.debug(f"md2html splitRes: {splitRes}")
    for i in range(1, len(splitRes), 2):
        placeholder = splitRes[i]
        if not placeholder in backR:
            logging.warning(
                f"Unknown placeholder {repr(placeholder)} when evaluating markdown"
            )
        else:
            splitRes[i] = backR[placeholder]
    logging.debug(f"finalhtml: {repr(''.join(splitRes))}")
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
        pathName = [e.name() for e in path]
        self.body.append(
            f'<li><a href={pathToMetaDesc(path[-1].section, self.basePath)} target="detail" class="index" id="IS-{".".join(pathName)}"><label class="index">{path[-1].name()}</label></a>\n'
        )
        sectionQualifier = ".".join(pathName[:-1])
        if sectionQualifier:
            sectionQualifier = sectionQualifier + "."
        self.body += self.siteWriter.sectionIndex(
            path[-1], self.basePath, sectionQualifier=sectionQualifier
        )
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
	schema_info.html
	meta_schema.json
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

    def __init__(self, schema, basePath, katex=None):
        self.schema = schema
        self.basePath = basePath
        if not os.path.isdir(basePath):
            os.makedirs(basePath)
        self.generatedPaths = {}
        self.katex = katex

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

    def writeLayout(
        self, targetPath, body, title, basePath, bodyClass="meta", extra={}
    ):
        """writes out the body into a full html page template"""
        if not basePath:
            basePath = "."

        def writer(outF):
            outF.write(
                f"""<!doctype html>
	<html lang="en">
	<head>
	  <meta charset="utf-8">
	  <title>{title}</title>
	  <meta name="description" content="Meta info description">
	  <meta name="author" content="meta_tool">
	  <link rel="stylesheet" href="{basePath}/css/metaStyle.css">{extra.get('headEnd', '')}
	</head>
	<body class="{bodyClass}">
"""
            )
            for l in body:
                outF.write(l)
            outF.write(f"{extra.get('bodyEnd','')}</body>\n</html>\n")

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

    def sectionIndexEls(
        self, section, basePath, subSections=False, sectionQualifier="", elTag="li"
    ):
        """returns a dictionary with html elTag (by default li) elements, for values, dimensions and subsections of section"""
        s = section
        sName = s.name()
        res = {
            "meta_value": [],
            "meta_dimension": [],
            "meta_sub_meta_names": [],
        }
        if not basePath:
            basePath = ""
        elif not basePath.endswith("/"):
            basePath = basePath + "/"
        if s.valueEntries:
            vals = res["meta_value"]
            for vName, v in sorted(s.valueEntries.items()):
                if v.meta_dimension:
                    dims = (
                        " ["
                        + (",".join([str(dim) for dim in entry.meta_dimension]))
                        + "]"
                    )
                else:
                    dims = ""
                vals.append(
                    f' <{elTag} class="subIndex" id="IV-{sectionQualifier}{sName}.{vName}"><a href="{basePath}section/{sName}/value/{vName}.html" target="detail" class="index"><label class="subIndex">{vName} ({v.meta_data_type.value}{dims})</label></a></{elTag}>\n'
                )
        if s.dimensions:
            dims = res["meta_dimension"]
            for vName, v in sorted(s.dimensions.items()):
                dims.append(
                    f' <{elTag} class="subIndex" id="ID-{sectionQualifier}{sName}.{vName}"><a href="{basePath}section/{sName}/dimension/{vName}.html" target="detail"><label class="subIndex">{vName} (dim)</label></a></{elTag}>\n'
                )
        if subSections and s.subSections:
            subs = res["meta_sub_meta_names"]
            for subName, subS in sorted(s.subSections.items()):
                subs.append(
                    f' <{elTag} class="subIndex subSection" id="IS-{sectionQualifier}{subName}"><a href="{basePath}section/{subName}/index.html" target="detail"><label class="subIndex">{subName}</label></a></{elTag}>\n'
                )
        return res

    def sectionIndex(self, section, basePath, subSections=False, sectionQualifier=""):
        """returns the html with the values, dimensions and optionally subsections of a section"""
        els = self.sectionIndexEls(section, basePath, subSections, sectionQualifier)
        s = section
        sName = s.name()
        body = []
        if not basePath:
            basePath = ""
        elif not basePath.endswith("/"):
            basePath = basePath + "/"
        if els["meta_value"]:
            body.append('<ul class="subIndex">\n')
            for el in els["meta_value"]:
                body.append(el)
            body.append("</ul>\n")
        if els["meta_dimension"]:
            body.append('<ul class="subIndex">\n')
            for el in els["meta_dimension"]:
                body.append(el)
            body.append("</ul>\n")
        if subSections and els["meta_sub_meta_names"]:
            body.append('<ul class="subIndex subSection">\n')
            for el in els["meta_sub_meta_names"]:
                body.append(el)
            body.append("</ul>\n")
        return body

    def writeMetaIndex(self, basePath=None):
        p = os.path.join(self.basePath, "meta_index.html")
        body = []
        data = []
        body.append(
            '<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>\n'
        )
        body.append(
            '<label>Filter:</label><input type="text" id="filter" size="40" >\n'
        )
        body.append('<span class="checkbox-list">')
        body.append('<ul class="index">\n')
        for sName, s in sorted(self.schema.sections.items()):
            body.append(
                f'<li class="index" id="IS-{sName}" ><label class="index"><a href="section/{sName}/index.html" target="detail" class="index">{sName}</label></a>\n'
            )
            data.append(
                {
                    "id": f"IS-{sName}",
                    "text": f"{sName} {MetaType.type_section.value} {s.section.meta_description}".lower(),
                }
            )
            for vName, v in sorted(s.valueEntries.items()):
                data.append(
                    {
                        "id": f"IV-{sName}.{vName}",
                        "text": f"{vName} {MetaType.type_value.value} {v.meta_description}".lower(),
                    }
                )
            for dName, d in sorted(s.dimensions.items()):
                data.append(
                    {
                        "id": f"ID-{sName}.{dName}",
                        "text": f"{dName} {MetaType.type_dimension.value} {d.meta_description}".lower(),
                    }
                )
            body += self.sectionIndex(s, basePath)
            body.append("</li>\n")
        for aName, a in sorted(self.schema.abstractTypes.items()):
            body.append(
                f'<li class="index" id="IA-{aName}"><label class="index"><a href="abstract/{aName}/index.html" target="detail" class="index">{aName}</a></label></li>\n'
            )
            data.append(
                {
                    "id": f"IA-{aName}",
                    "text": f"{aName} {MetaType.type_abstract.value} {a.abstract_type.meta_description}".lower(),
                }
            )
        body.append("</ul></span>\n")
        body.append("<script>let data=")
        body.append(json.dumps(data))
        body.append(
            """;
$('#filter').keyup(function() {
  var toSearch = $(this).val().toLowerCase().split(/ +/);

  data.forEach(function(x){
    let hasValue=true
    let i = 0
    let text=x.text
    while (hasValue && i < toSearch.length) {
      if (text.indexOf(toSearch[i]) < 0) {
        hasValue = false
      }
      i += 1
    }
    let el = $('#'+x.id)
    if (hasValue) {
      el.show()
      el.parents('li').show()           // show all li parents up the ancestor tree
    } else {
      el.hide();                // hide current li as it doesn't match
    }
  });
});</script>
"""
        )
        self.writeLayout(targetPath=p, body=body, title="Meta Index", basePath=basePath)

    def writeCss(self):
        p = os.path.join(self.basePath, "css/metaStyle.css")
        if not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))

        def writer(outF):
            outF.write(
                """
.deprecated {
color: red
}
.metaKey {
  font-weight: bold;
  font-size: small;
}
a {
  font-weight: bold;
  color: #2A2A9A;
  text-decoration-line: none;
}
a:visited {
  color: #4A2A99;
}
a.breadcrumb {
  font-size: small;
  border-radius: 0px 5px 5px 0px;
  background-color: #DDDDDD;
  padding: 1px 4px 1px 1px;
}
body.frames {
   margin: 0;            /* Reset default margin */
   background: #AAAAAA;
}
table.frames {
   border: none;
   width: 100%;
}
/* dl styling derived from Chad's comment on https://clicknathan.com/web-design/styling-html-5-description-lists-formerly-known-as-definition-lists-properly/ */
dl {
    display: flex;
    flex-wrap: wrap;
    width:100%;
    min-width: 450px
}
dl > * {
    padding-top: 0.5em;
}
dt {
    width:30%;
    font-weight: bold;
    text-align:right;
}
dd {
    width:60%;
    padding-left:1em;
    margin-left: 0px;
}
dd + dd {
    width: 100%;
    padding-left: calc(30% + 1em);
}
dt + dt {
    padding-right: 60%;
}
dt + dt + dd {
    margin-top: -1.625em; /* own height including padding */
    padding-left: calc(30% + 1em);
}
h1.meta_name {
  text-align: center;
}
.label {
background-color: #AA;
}
#frameIndex {
    display: block;       /* iframes are inline by default */
    border: none;         /* Reset default border */
    height: 95vh;        /* Viewport-relative units */
    width: 39vw;
    background: #FAFAFA;
}
#frameDetail {
    display: block;       /* iframes are inline by default */
    border: none;         /* Reset default border */
    height: 57vh;        /* Viewport-relative units */
    width: 59vw;
    background: #FAFAFA;
}
#frameData {
    display: block;       /* iframes are inline by default */
    border: none;         /* Reset default border */
    height: 37vh;        /* Viewport-relative units */
    width: 59vw;
    background: #FAFAFA;
}
ul.index,li.index,label.index {}
.subIndex {}
.rightTitle { text-align: right; }
.indented {
    padding: 0em 1.5em 0em 1.5em;
}
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
            t = f' target="{target}"'
        else:
            t = ""
        if mType == MetaType.type_abstract:
            pIndex = os.path.join(basePath, f"abstract/index.html")
            body.append(
                f'<a href="{pIndex}" class="breadcrumb"{t}>abstract types</a>:\n'
            )
        else:
            pIndex = os.path.join(basePath, f"section/index.html")
            body.append(f'<a href="{pIndex}" class="breadcrumb"{t}>sections</a>:\n')
        if "meta_parent_section" in meta.allSetKeys():
            sParent = self.schema.sections[meta.meta_parent_section]
            for sName in sParent.meta_path.split("."):
                sNow = self.schema.sections[sName]
                body.append(
                    metaLink(
                        sNow.section, basePath, target=target, htmlClass="breadcrumb",
                    )
                    + "."
                )
        if selfLink:
            body.append(
                metaLink(meta, basePath, target=target, htmlClass="label label-default")
            )
        elif selfLink is not None:
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
            "meta_deprecated",
            "meta_data_type",
            "meta_abstract_types",
            "meta_contains",
            "meta_referenced_section",
        ]
        body = []
        body += self.breadcrumb(meta, basePath, target="detail", selfLink=None)
        deprecated = ""
        if meta.meta_deprecated:
            deprecated = " deprecated"
        body.append(f'<h1 class="meta_name{deprecated}">{metaName}</h1>\n')
        body.append(
            f'<h3 class="rightTitle">{mType.value} from {ss.dictionariesOf(metaName, metaType=mType)}</h3>\n'
        )

        def descLink(name, dict="meta"):
            metaInfoPath = os.path.join(basePath, f"../{dict}")
            return f'<a href="{metaInfoPath}/section/meta_info_entry/value/{name}.html" class="metaKey">{name}</a>'

        body.append(f"<dl>\n")
        if deprecated:
            body.append(
                f'<dt class="deprecated">{descLink("meta_deprecated")}</dt><dd class="deprecated">true</dd>\n'
            )
        body.append(f'<dt>{descLink("meta_description")}</dt>\n')
        desc = md2html(meta.meta_description, schema=ss, basePath=basePath)
        body.append(f"<dd>{desc}</dd>\n")
        body.append(f'<dt>{descLink("meta_abstract_types")}</dt>\n<dd>[')
        first = True
        for refAName in meta.meta_abstract_types:
            if first:
                first = False
            else:
                body.append(",")
            body.append(
                f'  <span class="metaLink">{metaLink(self.schema.abstractTypes[refAName].abstract_type,basePath=basePath)}</span>\n'
            )
        body.append(f"]</dd>")
        if mType == MetaType.type_section:
            sNow = ss.sections[metaName]
            els = self.sectionIndexEls(sNow, basePath, elTag="dd")
            for k, ll in els.items():
                if ll:
                    body.append(f'<dt>{descLink(k, "meta_schema")}</dt>')
                    body += ll
        if "meta_required" in keys:
            body.append(
                f"<dt>{descLink('meta_required')}</dt><dd>{meta.meta_required}</dd>\n"
            )
        if "meta_repeats" in keys:
            body.append(
                f"<dt>{descLink('meta_repeats')}</dt><dd>{meta.meta_repeats}</dd>\n"
            )
        if "meta_parent_section" in keys:
            parentPath = os.path.join(
                basePath, f"section/{meta.meta_parent_section}/index.html"
            )
            body.append(
                f'<dt>{descLink("meta_parent_section")}</dt><dd><a href="{parentPath}" target="detail">{meta.meta_parent_section}</a></dd>\n'
            )
        if "meta_data_type" in keys:
            body.append(
                f'<dt>{descLink("meta_data_type")}</dt><dd>{meta.meta_data_type.value}</dd>\n'
            )
        for k in keys.difference(handledKeys):
            body.append(f"<dt>{descLink(k)}</dt>\n")
            body.append(f"<dd>{getattr(meta,k)}</dd>\n")
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
        if mType != MetaType.type_abstract:
            body.append(f"<h2>Data</h2>\n")
            body.append(f'<h3>Pristine</h3><div class="indented">\n')
            if mType == MetaType.type_section:
                leafVal = ""
            else:
                sNow = self.schema.sections[meta.meta_parent_section]
                if mType == MetaType.type_value:
                    leafVal = (
                        f'<a href="{{p}}#IV-{{dottedPath}}.{metaName}">{metaName}</a>\n'
                    )
                elif mType == MetaType.type_dimension:
                    leafVal = (
                        f'<a href="{{p}}#ID-{{dottedPath}}.{metaName}">{metaName}</a>\n'
                    )
                else:
                    raise Exception(f"unexpected meta type {mType}")
            sects = sNow.meta_path.split(".")
            rootSect = sects[0]
            p = os.path.join(basePath, f"pristine/{rootSect}/index.html")
            for i, v in enumerate(sects):
                ref = ".".join(sects[: i + 1])
                if i > 0:
                    body.append(".")
                body.append(f'<a href="{p}#IS-{ref}" target="data">{v}</a>')
            if leafVal:
                body.append(".")
                body.append(leafVal.format(p=p, dottedPath=".".join(sects)))
            body.append("</div>")
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

                def addList(pathNow, levelNow):
                    if not levelNow:
                        if pathNow and leafVal:
                            p = os.path.join(basePath, f"data/{pathNow[0]}/index.html")
                            body.append('<ul class=ïnstantations"><li>')
                            body.append(
                                leafVal.format(p=p, dottedPath=".".join(pathNow))
                            )
                            body.append("</li></ul>")
                        return
                    body.append('<ul class="instantiations">')
                    for elName, sub in sorted(levelNow.items()):
                        pathNew = pathNow + [elName]
                        p = os.path.join(basePath, f"data/{pathNew[0]}/index.html")
                        dottedPath = ".".join(pathNew)
                        body.append(
                            f'<li><a href="{p}#IS-{dottedPath}" target="data">{elName}</a>'
                        )
                        addList(pathNew, sub)
                        body.append("</li>")
                    body.append("</ul>")

                body.append(f"<h3>Instantiations</h3>\n")
                addList(pathNow=[], levelNow=instantiateTree)
        return body

    def mathExtra(self, basePath):
        "returns html head and scropt to render math in elements with class math with katex"
        if self.katex:
            return {
                "headEnd": """
<link rel="stylesheet" href="{katex}/katex.min.css">
<script defer src="{katex}/katex.min.js" onload="var math = document.getElementsByClassName('math');for (var i = 0; i < math.length; i++) {  katex.render(math[i].textContent, math[i]); }" ></script>
""",
            }
        return {
            "headEnd": """
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.11.1/dist/katex.min.css" integrity="sha384-zB1R0rpPzHqg7Kpt0Aljp8JPLqbXI3bhnPWROx27a9N0Ll6ZP/+DiW/UqRcLbRjq" crossorigin="anonymous">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.11.1/dist/katex.min.js" integrity="sha384-y23I5Q6l+B6vatafAwxRu/0oK/79VlbSz7Q9aiSZUvyWYIYsd+qj+o24G5ZU2zJz" crossorigin="anonymous" onload="var math = document.getElementsByClassName('math');for (var i = 0; i < math.length; i++) {  katex.render(math[i].textContent, math[i]); }" ></script>
            """
        }

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
            basePath = "../.."
            body = self.metaDesc(a.abstract_type, basePath=basePath)
            self.writeLayout(
                p,
                body=body,
                title=f"Abstract Type {aName}",
                basePath=basePath,
                extra=self.mathExtra(basePath),
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
            self.writeLayout(
                p,
                body=body,
                title=f"Section {sName}",
                basePath=basePath,
                extra=self.mathExtra(basePath),
            )
            for vName, v in s.valueEntries.items():
                basePath = "../../.."
                p = os.path.join(self.basePath, f"section/{sName}/value/{vName}.html")
                body = self.metaDesc(v, basePath=basePath)
                self.writeLayout(
                    p,
                    body=body,
                    title=f"Value {sName}",
                    basePath=basePath,
                    extra=self.mathExtra(basePath),
                )
            for dName, d in s.dimensions.items():
                basePath = "../../.."
                p = os.path.join(
                    self.basePath, f"section/{sName}/dimension/{dName}.html"
                )
                body = self.metaDesc(d, basePath=basePath)
                self.writeLayout(
                    p,
                    body=body,
                    title=f"Dimension {sName}",
                    basePath=basePath,
                    extra=self.mathExtra(basePath),
                )

    def dataIndex(self):
        """Returns the index of the data"""
        body = []
        basePath = ".."
        body.append(f'<h1>Data view index</h1>\n<ul class="index">\n')
        body.append('<ul class="index">\n')
        for sName in sorted(self.schema.dataView.keys()):
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
            f'<div class="breadcrumb"><a href="../index.html" target="_top" class="breadcrumb">Meta Schema</a>/<a href="schema_info.html" target="detail" class="breadcrumb">{self.schema.mainDictionary}</a></div>\n',
            """
    <table class="frames" padding="2">
      <tr> <td rowspan="2">
	  <iframe src="meta_index.html" name="index" id="frameIndex"></iframe> </td>
            <td> <iframe src="schema_info.html" name="detail" id="frameDetail"></iframe> </td></tr>
      <tr><td><iframe src="data/index.html" name="data" id="frameData"></iframe></td></tr>
    </table>
""",
        ]
        p = os.path.join(self.basePath, "index.html")
        self.writeLayout(p, body, title="Index", basePath=".")

    def writeMetaSchema(self):
        "Writes out the meta_schema in json format"
        p = os.path.join(self.basePath, "meta_schema.json")
        writeFile(p, self.schema.write)
        self.addGeneratedPath(p)

    def writeSchemaInfo(self):
        "Writes information on the current schema"
        pOut = os.path.join(self.basePath, "schema_info.html")
        body = []
        s = self.schema
        mInfo = s.metaInfo
        body.append(f'<a href="../index.html" class="breadcrumb">schemas</a>')
        body.append(f"<h1>Meta Info Schema for dictionary {s.mainDictionary}</h1>\n")
        body.append("<h2>Included Dictionaries</h2>\n")
        body.append("<ul>\n")
        for dictName in sorted(s.dictionaries):
            d = mInfo.dictionaries[dictName]
            v = d.metadict_version
            if v:
                v = " " + v
            else:
                v = ""
            descHtml = d.metadict_description
            p = f"../../meta_dictionary/{dictName}.meta_dictionary.json"
            body.append(
                f'<li><b>{dictName}{v}</b> (<a href="{p}">meta_dictionary.json</a>)<br>'
            )
            body.append(md2html(d.metadict_description, schema=s))
            stats = [f"{t}: {v}" for t, v in sorted(d.stats().items())]
            body.append(f"<div>{' '.join(stats)}</div>")
            body.append("</li>\n")
        body.append("</ul>\n")
        body.append(
            '<h2>Meta Info Reference</h2>\n<ul><li><a href="index.html" target="_top">frames</a></li><li><a href="meta_index.html" target="_top">no frames</a></li></ul>'
        )
        body.append("<h2>Schema</h2>\n<ul>")
        body.append('<li><a href="meta_schema.json">meta_schema.json</a></li>\n')
        body.append("</ul>\n")
        body.append("<h3>Json Schemas</h3>\n<ul>\n")
        for rName in sorted(self.schema.rootSections.keys()):
            baseP = "./"
            body.append(
                f'  <li><label>{rName}</label> (recursive: <a href="{baseP}json-schema-recursive-suspendable/{rName}.json-schema.json">suspendable</a>, <a href="{baseP}json-schema-recursive-simple/{rName}.json-schema.json">simple</a>; strict: <a href="{baseP}json-schema-strict-suspendable/{rName}.json-schema.json">suspendable</a>, <a href="{baseP}json-schema-strict-simple/{rName}.json-schema.json">simple</a>)</li>\n'
            )
        body.append("</ul>\n")
        self.writeLayout(
            pOut, body, title=f"{s.mainDictionary} Meta Info Schema", basePath="."
        )

    def writeJsonSchema(self):
        for p in writeAllSchemas(
            self.schema, self.basePath, pre="json-schema-", writeLayout=self.writeLayout
        ):
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
        self.writeJsonSchema()
        self.writeSchemaInfo()
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
                logging.warning(f"generatedFiles contains {f}: {pathNow} {f} {sub}")
            elif os.path.isdir(p):
                self.cleanupUnknown(p, sub)
