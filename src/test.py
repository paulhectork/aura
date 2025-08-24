import unittest

from envelope import Envelope
from splice import Splice
from split import Split
from track import Track

class TestEnvelope(unittest.TestCase):
    def setUp(self):
        print("HELLOOOOOOOOO")

    def tearDown(self):
        ...

def load_tests(loader=unittest.TestLoader(), tests=[], pattern=None) -> unittest.TestSuite:
    # test classes to run should be added here
    test_cases = [TestEnvelope]

    suite = unittest.TestSuite()
    for t in test_cases:
        tests = loader.loadTestsFromTestCase(t)
        suite.addTests(tests)
    return suite

def runner() -> None:
    textrunner = unittest.TextTestRunner()
    suite = load_tests()
    textrunner.run(suite)
    return


if __name__ == "__main__":
    runner()

