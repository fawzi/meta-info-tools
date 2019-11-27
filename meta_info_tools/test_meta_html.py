import unittest
from .meta_html import *
from .test_meta_schema import metaMetaSchema
import io
import json
import tempfile, shutil


class TestMetaHtml(unittest.TestCase):
    """tests the documentation generation"""

    def test_md2html(self):
        "tests markdown to html conversion (and math and meta info linking)"
        self.maxDiff = None
        test1 = [
            "The shape of the multidimensional array used to store the data corresponding to this meta info, either ",
            "meta_dimension_fixed or meta_dimension_symbolic.\n",
            "Example: [{ ``meta_dimension_symbolic'': ``number_of_atoms''}, {``meta_dimension_fixed'': 3 }].\n",
            "If no meta_dimension are given the data is a scalar.",
        ]
        schema = metaMetaSchema()
        r1 = md2html(
            text="".join(test1), basePath="..", schema=schema, raiseException=True
        )
        self.assertEqual(
            r1,
            '<p>The shape of the multidimensional array used to store the data corresponding to this meta info, either <a href="../section/meta_dimension/value/meta_dimension_fixed.html">meta_dimension_fixed</a> or <a href="../section/meta_dimension/value/meta_dimension_symbolic.html">meta_dimension_symbolic</a>.\nExample: [{ <code><a href="../section/meta_dimension/value/meta_dimension_symbolic.html">meta_dimension_symbolic</a>\'\':</code>number_of_atoms\'\'}, {``<a href="../section/meta_dimension/value/meta_dimension_fixed.html">meta_dimension_fixed</a>\'\': 3 }].\nIf no <a href="../section/meta_dimension/index.html">meta_dimension</a> are given the data is a scalar.</p>',
        )

    def test_site_writer(self):
        "tests SiteWriter (currently just that it runs)"
        tempDir = tempfile.mkdtemp(suffix="testSiteWriter")
        schema = metaMetaSchema()
        try:
            w = SiteWriter(schema, tempDir)
            w.writeAll()
            w.cleanupUnknown()
        finally:
            shutil.rmtree(tempDir)


if __name__ == "__main__":
    unittest.main()
