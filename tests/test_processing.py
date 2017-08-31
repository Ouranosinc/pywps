##################################################################
# Copyright 2016 OSGeo Foundation,                               #
# represented by PyWPS Project Steering Committee,               #
# licensed under MIT, Please consult LICENSE.txt for details     #
##################################################################

"""Unit tests for processing
"""

import unittest

from pywps import configuration


class ProcessingTest(unittest.TestCase):
    """Processing test cases"""

    def setUp(self):
        # self.database = configuration.get_config_value('logging', 'database')
        pass

    def test_default(self):
        """Test pywps.formats.Format class
        """
        self.assertEqual(configuration.get_config_value('processing', 'mode'), 'default')
        # self.assertTrue(session)


def load_tests(loader=None, tests=None, pattern=None):
    """Load local tests
    """
    if not loader:
        loader = unittest.TestLoader()
    suite_list = [
        loader.loadTestsFromTestCase(ProcessingTest)
    ]
    return unittest.TestSuite(suite_list)
