# Origin

This project is a fork of the origional work by Chris3606 that can be found [here](https://github/Chris3606/TOC-Generator). That project seemingly doesn't accept
pull requests so this is now a maintained fork, mostly for my own uses. It includes addtional functionality I requre.

# TOC-Generator
A table of contents generator for markdown, written in python.  Inspired by many of the table-of-contents generators that already exist, particularly [markdown-toc](https://github.com/jonschlinkert/markdown-toc).

# Installation/Prerequisites
The system consists of a single python script, requiring >= Python v3.5 to run.

# Usage
1. In all markdown files in your project that you want to generate tables of contents for, insert the following tags into the file, where you want the table of contents to be placed:
```
<!--ts-->
* [Examples](#examples)
<!--te-->
```
  * Any markdown headers found before the opening ``<!-- ts -->`` are not included in the table. This allows, for exmaple, a heading **Table of Contents**
    to not include itself
  * Hyperlinks in headers are stripped before generation

When the script is run, all text in between those two tags will be replaced with the table of contents.  Furthermore, the tags themselves will (obviously) not appear in the markdown view on GitHub, as they are html comments.

2. Run the included python script, passing as a command-line argument the directory of your project.  The script will automatically locate any markdown files (with .md extensions) within that folder and all subfolders.  It will scan them for the above tags.  If found, it will generate the table of contents for them, and replace any text inside the tags with the new table of contents.  Any file in which the tags can't be located will not be modified.
