# Patch unittest2 into unittest, or not.
import sys
from brennivin import testhelpers
sys.modules['unittest'] = testhelpers.unittest
