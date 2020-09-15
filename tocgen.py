#!/usr/bin/python

import os
import re
import click

from typing import Callable, List, Dict

REGEX_MARKDOWN_HEADER = re.compile(r'(#+) ?(.+)\n?')
REGEX_TAG_START = re.compile(r'<!--[ ]*ts[ ]*-->', re.IGNORECASE)
REGEX_TAG_END = re.compile(r'<!--[ ]*te[ ]*-->', re.IGNORECASE)
REGEX_HEADER_LINKS = re.compile(r"(?P<text>[^[]*)(?P<link>[^)]*)\)|(?P<remainder>.+)")
REGEX_HEADER_LINK_TEXT = re.compile(r"\[(?P<useme>[^]]+)")

StrList = List[str]


def is_markdown_file(file_path: str) -> bool:
    return file_path[-3:].lower() == '.md'


def get_file_names(path: str, selector_lambda: Callable = None) -> StrList:
    def default_selector(_):
        return

    # By default we select everything
    if not selector_lambda:
        selector_lambda = default_selector

    files = []
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


def generate_toc_lines(start: int, file_lines: StrList) -> StrList:
    """
    :param start: Lines before this marker are not included in the table of contents
    :type start: int
    :param file_lines: All the lines in the file
    :type file_lines: list
    """

    toc: StrList = []
    link_tags_found = {}

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

    return toc


# Returns indexes in the strings where tag starts and where it finishes.
# Returns -1, -1 if tag not found
def find_tags(file_lines: List):
    current = 0
    for line in file_lines:
        if REGEX_TAG_START.match(line):
            for i in range(current + 1, len(file_lines)):
                if REGEX_TAG_END.match(file_lines[i]):
                    return current, i
            # If we get here we didn't find a matching tag so just move on.
            return -1, -1

        current += 1

    return -1, -1


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

        start, end = find_tags(lines)

        if start != -1:  # Found tags
            del lines[start + 1:end]  # Remove anything in between the tags (eg. the table of contents)

            toc_lines = generate_toc_lines(start, lines)

            with open(file, 'w') as write_handle:
                for i in range(0, start + 1):
                    write_handle.write(lines[i])

                for line in toc_lines:
                    write_handle.write(line)

                for i in range(start + 1, len(lines)):
                    write_handle.write(lines[i])


if __name__ == "__main__":
    main()
