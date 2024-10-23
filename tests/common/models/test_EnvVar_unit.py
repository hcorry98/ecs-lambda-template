import os
import unittest

from environ.compat import ImproperlyConfigured

from common.models.EnvVar import EnvVar

class TestEnvVarUnit(unittest.TestCase):
    """Unit tests for the Singleton EnvVar class."""
    
    def test_new(self):
        """Tests if multiple initializations return the same instance across scopes."""
        envVar1 = EnvVar()
        envVar2 = EnvVar()

        self.assertTrue(envVar1 is envVar2)

        envVar1 = EnvVar()
        envVar2 = self._different_scope()

        self.assertTrue(envVar1 is envVar2)
    
    def _different_scope(self):
        """Helper function to provide different scope for test_new."""
        return EnvVar()
    
    def test_call(self):
        """Tests if envVar instance is callable and if it returns correct value."""
        envVar = EnvVar()

        self.assertTrue(envVar('ENV') == os.environ['ENV'])
    
    def test_call_fail(self):
        """Tests if envVar instance throws an exception when called with invalid key input."""
        envVar = EnvVar()

        with self.assertRaises(ImproperlyConfigured):
            envVar('invalid key')

    def test_getitem(self):
        """Tests if envVar instance can be indexed into and if it returns correct value."""
        envVar = EnvVar()

        self.assertTrue(envVar['ENV'] == os.environ['ENV'])
    
    def test_getitem_fail(self):
        """Tests if envVar instance throws an exception when indexed into with invalid key input."""
        envVar = EnvVar()

        with self.assertRaises(ImproperlyConfigured):
            envVar['invalid key']

    def test_delete(self):
        """Tests if envVar class method deletes instance attribute."""
        envVar = EnvVar()
        self.assertTrue(hasattr(envVar, 'instance'))
        EnvVar.delete()
        self.assertFalse(hasattr(envVar, 'instance'))

    def test_delete_noInstance(self):
        """Test if envVar delete method allows repeat deletes."""
        envVar = EnvVar()
        self.assertTrue(hasattr(envVar, 'instance'))
        EnvVar.delete()
        self.assertFalse(hasattr(envVar, 'instance'))
        EnvVar.delete()
        self.assertFalse(hasattr(envVar, 'instance'))

    def tearDown(self):
        """Delete the environment variable after each test."""
        EnvVar.delete()
