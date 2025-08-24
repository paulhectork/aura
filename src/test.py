import unittest

from envelope import Envelope
from splice import Splice
from split import Split
from track import Track

class TestEnvelope(unittest.TestCase):
    def setUp(self):
        print("HELLOOOOOOOOO setUp")

    def tearDown(self):
        ...

    def test_xxx(self):
        print("HELLOOOOOOOOO test_xxx")


def runner() -> None:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests([
        # add other tests here
        loader.loadTestsFromTestCase(TestEnvelope)
    ])

    runner = unittest.TextTestRunner()
    runner.run(suite)
    return


if __name__ == "__main__":
    runner()

