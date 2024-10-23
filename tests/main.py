import sys, os
currentDir = os.path.dirname(os.path.realpath(__file__))
root = os.path.dirname(currentDir)
src = os.path.join(root, 'src')
sys.path.append(src)
sys.path.append(root)

import unittest

from tests.discover import testSuiteFromRecursiveDiscover

if __name__ == '__main__':
    """Main function for running all tests in the tests folder."""
    result = unittest.TextTestRunner(verbosity=2).run(testSuiteFromRecursiveDiscover('tests', 'test_*.py'))
    sys.exit(not result.wasSuccessful())
