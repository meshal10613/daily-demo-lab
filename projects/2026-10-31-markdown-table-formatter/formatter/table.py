from dataclasses import dataclass
from typing import List, Optional

@dataclass
class MarkdownTable:
    headers: List[str]
    rows: List[List[str]]
    alignments: List[str]  # 'left', 'right', 'center'

    def render(self) -> str:
        col_count = len(self.headers)
        widths = [len(h) for h in self.headers]
        for row in self.rows:
            for idx in range(col_count):
                val = row[idx] if idx < len(row) else ''
                widths[idx] = max(widths[idx], len(val))
        widths = [max(w, 3) for w in widths]

        def format_cell(text: str, width: int, align: str) -> str:
            if align == 'right':
                return text.rjust(width)
            elif align == 'center':
                return text.center(width)
            return text.ljust(width)

        lines = []
        header_line = '| ' + ' | '.join(format_cell(h, widths[i], self.alignments[i]) for i, h in enumerate(self.headers)) + ' |'
        lines.append(header_line)
        sep_cells = []
        for i, align in enumerate(self.alignments):
            w = widths[i]
            if align == 'right':
                sep_cells.append('-' * (w - 1) + ':')
            elif align == 'center':
                sep_cells.append(':' + '-' * (w - 2) + ':')
            else:
                sep_cells.append('-' * w)
        lines.append('| ' + ' | '.join(sep_cells) + ' |')
        for row in self.rows:
            cells = [format_cell(row[i] if i < len(row) else '', widths[i], self.alignments[i]) for i in range(col_count)]
            lines.append('| ' + ' | '.join(cells) + ' |')
        return '\n'.join(lines)

def parse_table(markdown_text: str) -> MarkdownTable:
    lines = [l.strip() for l in markdown_text.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        raise ValueError('Markdown table must have at least header and separator lines.')
    def split_row(line: str) -> List[str]:
        parts = [p.strip() for p in line.strip('|').split('|')]
        return parts
    headers = split_row(lines[0])
    sep_row = split_row(lines[1])
    alignments = []
    for s in sep_row:
        if s.startswith(':') and s.endswith(':'):
            alignments.append('center')
        elif s.endswith(':'):
            alignments.append('right')
        else:
            alignments.append('left')
    while len(alignments) < len(headers):
        alignments.append('left')
    rows = [split_row(l) for l in lines[2:]]
    return MarkdownTable(headers=headers, rows=rows, alignments=alignments)

def format_table(markdown_text: str) -> str:
    table = parse_table(markdown_text)
    return table.render()

def align_table(table: MarkdownTable, col_idx: int, align: str) -> MarkdownTable:
    if col_idx < len(table.alignments):
        table.alignments[col_idx] = align
    return table
