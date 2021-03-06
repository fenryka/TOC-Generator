#!/usr/bin/python

import os
import re
import click

from typing import Callable, List, Dict, Tuple, AnyStr

# Table of Contents patterns
REGEX_MARKDOWN_HEADER = re.compile(r'(#+) ?(.+)\n?')
REGEX_TAG_START = re.compile(r'<!--[ ]*ts[ ]*-->', re.IGNORECASE)
REGEX_HEADER_LINKS = re.compile(r"(?P<text>[^[]*)(?P<link>[^)]*)\)|(?P<remainder>.+)")
REGEX_HEADER_LINK_TEXT = re.compile(r"\[(?P<useme>[^]]+)")

# Table of Figures patterns
REGEX_TOF_START = re.compile(r'<!--[ ]*tfs[ ]*-->', re.IGNORECASE)
REGEX_FIG_X = re.compile(r'<!--[ ]*fig_x[ ]*:[ ]*(?P<title>.*?)[ ]*-->', re.IGNORECASE)

# Where to start processing headers for the table of contents
REGEX_BODY_START = re.compile(r"<!--[ ]*body-start[ ]*-->")

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
        for root, directories, fileNames in os.walk(path):
            for filename in fileNames:
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


def parse_file(file_lines: StrList) -> Tuple[Tuple[int, int], StrList, StrList, Dict[int, AnyStr]]:
    """
    :param file_lines: All the lines in the file
    :type file_lines: list
    :return
    """

    toc: StrList = []
    tof: StrList = []
    link_tags_found = {}

    in_body = False
    figureCount = 0
    figureLines = {}
    toc_start = -1
    tof_start = -1
    for idx, line in enumerate(file_lines):
        if REGEX_TAG_START.match(line):
            toc_start = idx+1
        elif REGEX_TOF_START.match(line):
            tof_start = idx+1
        elif REGEX_BODY_START.match(line):
            in_body = True
        else:
            match = REGEX_MARKDOWN_HEADER.match(line)
            if match and in_body:
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

                fig_title = "***Figure %i***: *%s*" % (figureCount, figure.group("title"))
                figureLines[idx] = """<div align="center">%s</div>\n""" % fig_title
                tof.append(" * %s\n" % fig_title)

    return (toc_start, tof_start), toc, tof, figureLines


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

        for tag in reversed(tags):
            print(tag)
            del lines[tag[0]+1:tag[1]]

        if len(tags) > 0:

            starts, toc_lines, tof_lines, fig_lines = parse_file(lines)

            with open(file, 'w') as write_handle:
                for i in range(0, len(lines)):
                    if i == starts[0]:
                        for line in toc_lines:
                            write_handle.write(line)

                    if i == starts[1]:
                        for line in tof_lines:
                            write_handle.write(line)

                    if i in fig_lines:
                        write_handle.write(lines[i])
                        write_handle.write(fig_lines[i])
                    else:
                        write_handle.write(lines[i])


if __name__ == "__main__":
    main()
