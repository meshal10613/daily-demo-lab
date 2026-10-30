import unittest
from formatter.table import parse_table, format_table, MarkdownTable

class TestMarkdownTable(unittest.TestCase):
    def test_parse_and_render(self):
        raw = '| Item | Price |\n|---|---:|\n| Coffee | 3.50 |\n| Tea | 2.00 |'
        formatted = format_table(raw)
        self.assertIn('| Item   | Price |', formatted)
        self.assertIn('| Coffee |  3.50 |', formatted)

    def test_alignment_render(self):
        table = MarkdownTable(headers=['A', 'B'], rows=[['1', '2']], alignments=['left', 'right'])
        res = table.render()
        self.assertIn('--:', res)
        table_wide = MarkdownTable(headers=['ColA', 'ColB'], rows=[['1', '2']], alignments=['left', 'right'])
        self.assertIn('---:', table_wide.render())

    def test_center_alignment(self):
        table = MarkdownTable(headers=['S'], rows=[['x']], alignments=['center'])
        self.assertIn(':-:', table.render())
if __name__ == '__main__':
    unittest.main()
