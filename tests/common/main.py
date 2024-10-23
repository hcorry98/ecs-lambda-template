import sys, os
currentDir = os.path.dirname(os.path.realpath(__file__))
testsDir = os.path.dirname(currentDir)
root = os.path.dirname(testsDir)
src = os.path.join(root, "src")
sys.path.append(src)
sys.path.append(root)

import unittest

from tests.discover import testSuiteFromRecursiveDiscover

if __name__ == "__main__":
    """Main function for running all tests in tests/common."""
    result = unittest.TextTestRunner(verbosity=2).run(testSuiteFromRecursiveDiscover('tests/common', 'test_*.py'))
    sys.exit(not result.wasSuccessful())
