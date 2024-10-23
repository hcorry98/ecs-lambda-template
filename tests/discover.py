import unittest
import glob
import os

def test_suite_from_recursive_discover(folder: str, pattern: str) -> unittest.TestSuite:
    """Provides test suite object containing tests found in the given folder that begin with the given pattern.

    Args:
        folder (str): path to the folder to search for tests
        pattern (str): regex to match the names of tests we would like to store in the suite

    Returns:
        TestSuite: a unittest object representing an aggregation of test cases
    """
    currentDir = os.path.dirname(os.path.realpath(__file__))
    root = os.path.dirname(currentDir)

    testFiles = glob.glob(f'{root}/{folder}/**/{pattern}', recursive=True)
    testDirs = list(set(([os.path.dirname(os.path.abspath(testFile)) for testFile in testFiles])))

    suites = [unittest.TestLoader().discover(start_dir=d, pattern=pattern) for d in testDirs]
    suite = unittest.TestSuite(suites)
    return suite
