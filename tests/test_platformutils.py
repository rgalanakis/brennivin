import mock
import unittest

from brennivin import platformutils as pu


class TestGetInterpreterFlavorPurepython(unittest.TestCase):

    def testBadPath(self):
        """Test that a bad path raises NameError."""
        p = r'E:\foo\bar.exe'
        self.assertRaises(NameError, pu.get_interpreter_flavor, _exepath=p)

    def _runtest(self, exe, ideal, vinfo=None):
        """Runs tests to ensure a known good, including support for debug
        versions."""
        entries = exe, exe.replace('.exe', '_d.exe')
        for e in entries:
            result = pu.get_interpreter_flavor(_exepath=e, _vinfo=vinfo)
            self.assertEqual(result, ideal)

    def testPython26(self):
        self._runtest('foo/python.exe', pu.EXE_VANILLA26, (2, 6))

    def testPython27(self):
        self._runtest('foo\\pythonw.exe', pu.EXE_VANILLA27, (2, 7))

    def testMaya(self):
        self._runtest('foo/MAYA.exe', pu.EXE_MAYA, (2, 6))
        self._runtest('foo/mayabatch.exe', pu.EXE_MAYA, (2, 6))

    def testMaya27(self):
        self._runtest('foo/MAYA.exe', pu.EXE_MAYA27, (2, 7))
        self._runtest('foo/mayabatch.exe', pu.EXE_MAYA27, (2, 7))

    def testMayapy(self):
        self._runtest('foo/mayapy.exe', pu.EXE_MAYA, (2, 6))

    def testExeFile(self):
        self._runtest('foo/exefile.exe', pu.EXE_EXEFILE)
        self._runtest('foo/ExeFileConsole.exe', pu.EXE_EXEFILE)


class Test64BitProc(unittest.TestCase):
    def makestruct(self, size):
        calcsizemock = mock.Mock(return_value=size)
        structmock = mock.Mock(calcsize=calcsizemock)
        return structmock

    def testKnown(self):
        """Tests 4 and 8 pointer size."""
        mock4 = self.makestruct(4)
        self.assertFalse(pu.is_64bit_process(mock4))
        mock8 = self.makestruct(8)
        self.assertTrue(pu.is_64bit_process(mock8))

    def testUnknown(self):
        """Tests an OSError is raised for unknown struct size."""
        self.assertRaises(OSError, pu.is_64bit_process, self.makestruct(16))
        self.assertRaises(OSError, pu.is_64bit_process, self.makestruct(2))
