""" test for parser & generator """
import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import abnf_parser

def _quick_test(defn, name):
  tmp1 = abnf_parser.process_rules(defn + "\n\n")
  assert tmp1 is not None, f"Fail to parse definition [{defn}]"
  tmp2 = tmp1.get_rule(name)
  assert tmp2 is not None, f"Can not find rule nam [{name}]"
  tmp3 = tmp2.generate()
  assert tmp3 is not None, "Fail to generate value"
  return tmp3

cur_dir = os.path.dirname(os.path.abspath(__file__))

with open(cur_dir + "/test.abnf",'r') as f:
  test_rules = f.read()
  f.close()

class TestParsers(unittest.TestCase):
  """ test cases """

  def _test_rule(self, expected, rule, name='START', fnc = None):
    if fnc is None:
      fnc = self.assertEqual
    return fnc(
      expected,
      _quick_test(rule, name)
    )

  def test_bin_string(self):
    self._test_rule(
      expected = b'ABC',
      rule = "START = %x41.42.43"
    )
    self._test_rule(
      expected = b'ABC',
      rule = "START = %d65.66.67"
    )
    self._test_rule(
      expected = b'ABC',
      rule = "START = %b01000001.01000010.01000011"
    )
    self._test_rule(
      expected = b'AAA',
      rule = "START = %x41 %d65 %b01000001"
    )


  def test_repeat(self):
    self._test_rule(
      expected = b"XXXX",
      rule =
        """
        START = 4B
        B = "X"
        """
    )

  def test_group_repeat(self):
    self._test_rule(
      expected = b"XYXY",
      rule =
        """
        START = 2( B )
        B = "XY"
        """
    )
    self._test_rule(
      expected = b'12121212',
      rule = """
        START = 2( 2( B ))
        B = "12"
      """
    )

  def test_alternative(self):
    self._test_rule(
      expected = b'12|21',
      fnc = self.assertRegex,
      rule = """
        START = A B / B A
        A = "1"
        B = "2"
      """,
    )

  def test_optional(self):
    self._test_rule(
      expected = b'123?',
      fnc = self.assertRegex,
      rule = """
        START = A [ B ]
        A = "12"
        B = "3"
      """
    )

  def test_bad_rules(self):
    with self.assertRaises(Exception) as context:
      abnf_parser.process_rules("foo\n")
    with self.assertRaises(Exception) as context:
      abnf_parser.process_rules("foo === bar;\n")
    with self.assertRaises(Exception) as context:
      abnf_parser.process_rules("=1' or 1='1\n")


if __name__ == '__main__':
  unittest.main()

