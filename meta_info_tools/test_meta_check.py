import unittest
from .meta_check import *
from .test_meta_schema import metaMetaSchema
import io
import json


class TestMetaCheck(unittest.TestCase):
    """tests the checks"""

    def test_meta_check(self):
        schema = metaMetaSchema()
        doChecks(schema)


if __name__ == "__main__":
    unittest.main()
