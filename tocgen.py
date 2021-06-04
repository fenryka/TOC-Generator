#!/usr/bin/python

import os
import re
import click

from typing import Callable, List, Dict, Tuple, SupportsInt, AnyStr

# Table of Contents patterns
REGEX_MARKDOWN_HEADER = re.compile(r'(#+) ?(.+)\n?')
REGEX_TAG_START = re.compile(r'<!--[ ]*ts[ ]*-->', re.IGNORECASE)
REGEX_HEADER_LINKS = re.compile(r"(?P<text>[^[]*)(?P<link>[^)]*)\)|(?P<remainder>.+)")
REGEX_HEADER_LINK_TEXT = re.compile(r"\[(?P<useme>[^]]+)")

# Table of Figures patterns
REGEX_TOF_START = re.compile(r'<!--[ ]*tfs[ ]*-->', re.IGNORECASE)
REGEX_FIG_X = re.compile(r'<!--[ ]*fig_x[ ]*:[ ]*(?P<title>.*?)[ ]*-->', re.IGNORECASE)

REGEX_TAG_END = re.compile(r'<!--[ ]*end[ ]*-->', re.IGNORECASE)

StrList = List[str]


def is_markdown_file(file_path: str) -> bool:
    return file_path[-3:].lower() == '.md'


def get_file_names(path: str, selector_lambda: Callable = None) -> StrList:
    def default_selector(_):
        return

    files = []

    # By default we select everything
    if not selector_lambda:
        selector_lambda = default_selector

    if os.path.isfile(path):
        files.append(path)
    else:
        for root, directories, filenames in os.walk(path):
            for filename in filenames:
                if selector_lambda(filename):
                    files.append(os.path.join(root, filename))

    return files


def get_link_tag(header: str, link_tags_found: Dict) -> str:
    result = ''
    for c in header.lower():
        if c.isalnum():
            result += c
        elif c == ' ' or c == '-':
            result += '-'
    # else it's punctuation so we drop it.

    if result not in link_tags_found:
        link_tags_found[result] = 0
    else:
        link_tags_found[result] += 1
        result += '-' + str(link_tags_found[result])

    return '(#' + result + ')'


def sanitise_toc_line(line_: str) -> str:
    rtn = ''
    res = REGEX_HEADER_LINKS.finditer(line_)
    for x in res:
        if x.group('remainder'):
            rtn += x.group('remainder')
        else:
            rtn += x.group('text')
            match = REGEX_HEADER_LINK_TEXT.match(x.group('link'))
            rtn += (match.group('useme'))
    return rtn


def parse_file(start: int, file_lines: StrList) -> Tuple[StrList, Dict[int, AnyStr]]:
    """
    :param start: Lines before this marker are not included in the table of contents
    :type start: int
    :param file_lines: All the lines in the file
    :type file_lines: list
    :return
    """

    toc: StrList = []
    link_tags_found = {}

    figureCount = 0
    figureLines = {}
    for idx, line in enumerate(file_lines):
        if idx < start:
            continue

        match = REGEX_MARKDOWN_HEADER.match(line)
        if match:
            # add spaces based on sub-level, add [Header], then figure out what the git link is for that
            # header and add it
            toc_entry = '    ' * (len(match.group(1)) - 1) \
                        + '* [' \
                        + sanitise_toc_line(match.group(2)) \
                        + ']' \
                        + get_link_tag(match.group(2), link_tags_found)
            toc.append(toc_entry + '\n')

        figure = REGEX_FIG_X.match(line)
        if figure:
            figureCount += 1
            figureLines[idx] = """<div align="center">**Figure %i**: %s</div>\n""" % (figureCount, figure.group("title"))

    return toc, figureLines


def find_tags(file_lines: List[AnyStr]) -> List[Tuple[int, int]]:
    """
    :return indexes in the strings where tag starts and where it finishes.
    :return -1, -1 if tag not found
    """

    rtn = []

    for idx, line in enumerate(file_lines):
        if REGEX_TAG_START.match(line) or REGEX_TOF_START.match(line) or REGEX_FIG_X.match(line):
            rtn.append((idx, -1))
        elif REGEX_TAG_END.match(line):
            rtn[-1] = (rtn[-1][0], idx)

    return rtn


@click.command()
@click.argument("path")
@click.option("-v", "--verbose", is_flag=True)
def main(path, verbose):
    md_files = get_file_names(path, is_markdown_file)

    for file in md_files:
        if verbose:
            click.echo("Checking file: " + file)

        with open(file, 'r') as file_handle:
            lines = file_handle.readlines()

        tags = find_tags(lines)

        start = 0

        for tag in reversed(tags):
            print(tag)
            del lines[tag[0]+1:tag[1]]

        if len(tags) > 0:

            toc_lines, fig_lines = parse_file(start, lines)

            with open(file, 'w') as write_handle:
                for i in range(0, start + 1):
                    write_handle.write(lines[i])

                for line in toc_lines:
                    write_handle.write(line)

                for i in range(start + 1, len(lines)):
                    if i in fig_lines:
                        write_handle.write(lines[i])
                        write_handle.write(fig_lines[i])
                    else:
                        write_handle.write(lines[i])


if __name__ == "__main__":
    main()
