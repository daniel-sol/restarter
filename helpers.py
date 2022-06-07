import logging
import re
import argparse
from subprocess import Popen, PIPE, CalledProcessError
from pathlib import Path
import numpy as np
import pandas as pd
from ecl2df import grid, EclFiles


logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
# LOGGER.addHandler(logging.NullHandler())
# Names to use of the keys in the contents dictionary
HEAD_NAMES = "headers"
HEAD_LINES = "header line"
HEAD_CONT = "header contents"
SOL_NAME = "solution name"
SOL_VALUES = "solutions"

def parse_intehead(inte_string):
    """parses the string containing intehead
    args:
    inte_string (str): string containing the intehead
    returns date (str): the column name to select from the corresponding ecl2df
    """
    parts = re.findall(r".*\n", inte_string)
    print(parts)
    print(parts[11])
    print(parts[10])

    year_part = re.search(r"(\d{4})\s", parts[11]).group(1)
    print(year_part)
    day_part = re.search(r"\d+\s+\d{1,2}\s*$",parts[10] ).group(0).split()
    print(day_part)
    return_date = f"@{year_part}-{day_part[0]}-{day_part[1]}"
    return return_date


def read_grdecl(path):
    """Reads eclipse grdecl parameter from file
    args:
    path (str): path to file
    returns record (dict): name found in file asd key,
                           the numbers from the file as values
    """
    contents = Path(path).read_text()
    strings = [name for name in re.findall(r"^[A-Za-z^\s]+", contents)
               if "ECHO" not in name]
    name = strings.pop()

    numbers = [num.strip() for num in re.findall(r"[0-9\.]+\s+", contents)]
    record = {name: numbers}
    return record


def split_head(line):
    """Splits header line into components
    args:
    line (str): string to split
    returns parts (tuple): first entry is name, second is number of entries
    """
    parts = line.replace("'", "").strip().split()
    LOGGER.debug(parts)
    return parts


def add_contents(contents, type_name, name, line):
    """Adds to the main dictionary,
    args:
        content (dict): the main dictionary
        type_name (str): name of one of the dictionaries of dict
        name (str): name of one of the keys in the dict of dict named type_name
        line (str): text string to be stored as value corresponding to name
    """
    if name not in contents[type_name]:
        contents[type_name][name] = []
    contents[type_name][name].append(line)


def read_fun(path):
    """Reads funrst file
    args:
    path (str): name of funrst file
    returns contents (dictionary)
    """
    LOGGER.debug("Reading from %s", path)
    contents = {HEAD_NAMES: [], HEAD_LINES: [], HEAD_CONT: {},
                SOL_NAME: [], SOL_VALUES: {}}

    head_name = None
    sol_listen = False
    block = None
    prev_name = "Not assigned"
    discrete = False
    try:
        with open(path, "r") as funhandle:
            LOGGER.debug("Opening the show")
            sol_listen = False

            for line in funhandle:
                # matches lines with possible whitespace,
                # then letters inside '' then whitespace,
                # also needed to add 1 / and _, because you have names like
                # 1/BO and WAT_DEN
                # then numbers,
                # then letters inside ''
                head_m = re.match(r"(\s+)?'([1\/_A-Z\s]+)'\s+(\d+)\s+'([A-Z]+)'",
                                  line)

                if head_m:
                    if prev_name == "INTEHEAD":
                        date = parse_intehead(block)
                        print(date)
                        exit()
                    LOGGER.debug(line)
                    head_name = split_head(line)[0]
                    LOGGER.debug("---> %s", head_name)
                    if block is not None:
                        LOGGER.debug("--> Block defined")
                        if sol_listen:
                            LOGGER.debug("--> storing block in solutions")
                            split_block = block.split("\n")
                            LOGGER.debug("%s lines are %i", prev_name,
                                         len(split_block))
                            # time.sleep(1)
                            add_contents(contents, SOL_VALUES, prev_name, block)
                            contents[SOL_NAME].append(head_name)
                            block = ""
                    LOGGER.debug("--> adding and appending head, and full line")
                    add_contents(contents, HEAD_CONT, prev_name, block)

                    contents[HEAD_NAMES].append(head_name)
                    discrete = "INTE" in line
                    contents[HEAD_LINES].append(line)
                    LOGGER.debug(head_name)
                    block = ""
                    prev_name = head_name

                if not head_m:
                    if discrete:
                        line = re.sub(r"\.[0-9]+", "", line)
                    block += line

                if head_name == "STARTSOL":
                    sol_listen = True
                    block = ""

                if head_name == "ENDSOL":
                    sol_listen = False

    except UnicodeDecodeError:
        LOGGER.error("Cannot read %s, is this a binary file?", path)

    except FileNotFoundError:
        LOGGER.error("Cannot read %s, file does not exist", path)


    return contents


def write_fun(contents, file_name="TEST.FUNRST"):
    """Writes FUNRST file from dictionary
       args:
           contents (dict): dictionary with contents of future file
           file_name (str): name of output file
    """
    write_sol = False
    LOGGER.debug("Writing %s", file_name)
    with open(file_name, "w") as outhandle:
        for i, head_name in enumerate(contents[HEAD_NAMES]):
            LOGGER.debug(head_name)
            head_line = contents[HEAD_LINES][i]
            outhandle.write(contents[HEAD_LINES][i])
            try:
                outline = contents[HEAD_CONT][head_name].pop(0)

                outhandle.write(outline)
            except IndexError:
                LOGGER.warning("Cannot dump header contents for %s", head_name)
            except KeyError:
                LOGGER.warning("Cannot write %s", head_name)

            if head_name == "ENDSOL":
                write_sol = False
            if write_sol:
                outhandle.write(contents[SOL_VALUES][head_name].pop(0))

            if head_name == "STARTSOL":
                write_sol = True
    LOGGER.info("Written %s", file_name)
    return file_name


def convert_restart(restart_path, background=False):
    """Converts unrst file to funrst file
    args:
        restart_path (str): path to existing restart file
    returns: out_path (str): name of funrst file generated
    """
    LOGGER.debug("Converting unrst file %s", restart_path)
    unrst_path = Path(restart_path)
    suffix = ".FUNRST"
    if restart_path.endswith(".FUNRST"):

        suffix = ".UNRST"

    out_path = str(unrst_path.absolute().parent) + "/" + unrst_path.stem + suffix
    command = ["convert.x", restart_path]
    LOGGER.debug(command)
    process = Popen(command, stdout=PIPE,
                    stderr=PIPE)
    try:
        process = Popen(command, stdout=PIPE,
                        stderr=PIPE)
        if not background:
            stdout, stderr = process.communicate()
            if stdout:
                LOGGER.debug(stdout.decode("utf-8"))

            if stderr:
                LOGGER.debug(stderr.decode("utf-8"))

    except CalledProcessError:
        LOGGER.error('Could not run command %s', ' '.join(command))
    return out_path
