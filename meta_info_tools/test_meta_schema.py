import unittest
from .meta_schema import *
from .test_meta_info import metaMetaInfo
import io
import json


def metaMetaSchema():
    "returns the MetaSchema of the built-in meta dictionary"
    return MetaSchema.forDictionary(dictName="meta", metaInfo=metaMetaInfo())


class TestMetaSchema(unittest.TestCase):
    """tests the schema generation"""

    def test_metaMetaSchema(self):
        schema = metaMetaSchema()


if __name__ == "__main__":
    unittest.main()
