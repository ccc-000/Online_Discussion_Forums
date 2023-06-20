import unittest
from utils import *


class MyTestCase(unittest.TestCase):
    def test_something(self):
        jsonStr = '{"code": 0, "message": "Hello"}'
        response = json2Response(jsonStr)
        self.assertEqual(0, response.code)  # add assertion here
        self.assertEqual("Hello", response.message)  # add assertion here

        response.code = 1
        self.assertEqual('{"code": 1, "message": "Hello"}', response.to_json())


if __name__ == '__main__':
    unittest.main()
