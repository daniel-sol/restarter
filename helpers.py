import logging
import re
import time
from collections import OrderedDict
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
HEAD_LINE = "header line"
CONTENTS_NAME = "Contents"
TYPE_NAME = "type"

def parse_intehead(inte_string):
    """parses the string containing intehead
    args:
    inte_string (str): string containing the intehead
    returns date (str): the column name to select from the corresponding ecl2df
    """
    LOGGER.debug("What to parse:")
    LOGGER.debug(inte_string)
    parts = re.findall(r".*\n", inte_string)
    LOGGER.debug(parts)
    LOGGER.debug(parts[11])
    LOGGER.debug(parts[10])

    year_part = re.search(r"(\d{4})\s", parts[11]).group(1)
    LOGGER.debug(year_part)
    day_part = re.search(r"\d+\s+\d{1,2}\s*$",parts[10] ).group(0).split()
    LOGGER.debug(day_part)
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


def add_contents(contents, type_name, name, text):
    """Adds to the main dictionary,
    args:
        content (dict): the main dictionary
        type_name (str): name of one of the dictionaries of dict
        name (str): name of one of the keys in the dict of dict named type_name
        text (str): text string to be stored as value corresponding to name
    """
    if name not in contents[type_name]:
        contents[type_name][name] = []
    contents[type_name][name].append(text)


def count_blocks(block, val_count=True):
    """Checks block of text for how many lines
        args:
         block (str): the block of text to check
    """
    line_count = len(block.split("\n"))
    number_count = len(re.findall(r"[0-9\.]+", block))
    LOGGER.debug("Block has %i lines, and %i values", line_count, number_count)
    if val_count:
        return_value = number_count
    else:
        return_value = line_count
    return return_value
        # time.sleep(1)

def read_back_fun(fun_path):
    """Reads file, returns a list of the lines
    args:
       fun_path (str): path to file
    raises OSError:

    """
    contents = []
    try:
        with open(fun_path, "r") as funhandle:
            contents = funhandle.read().split("\n")
    except OSError as ose:
        raise OSError("Cannot open ", fun_path) from ose
    return contents


def check_files(first_fun, second_fun):

    """Compares two FUNRST files
    args:
        first_fun (str): path to file
        second_fun (str): path to file
    """
    LOGGER.info("Comparing %s vs %s\n", first_fun, second_fun)
    LOGGER.info("----------------------------------------------\n")
    first = read_back_fun(first_fun)
    second = read_back_fun(second_fun)
    first_length = len(first)
    second_length = len(second)

    if first_length != second_length:
        LOGGER.warning("Difference in length first is %i, second %i",
                       first_length, second_length)
    for i, first_line in enumerate(first):
        if first_line != second[i]:
            LOGGER.warning("Line %i: \n|%s|\n|%s|\n", i, first_line, second[i])
            exit()


# def check_fun(contents):
#     """Checking that the dictionary is aligned"""
#     for date in contents:
#         for date.
def read_fun(path):
    """Reads funrst file
    args:
    path (str): name of funrst file
    returns contents (dictionary)
    """
    LOGGER.debug("Reading from %s", path)

    contents = OrderedDict()

    type_name = "headers"
    block = ""
    prev_name = None
    head_name = None
    discrete = False

    try:
        with open(path, "r") as funhandle:
            LOGGER.debug("Opening the show")
            sol_listen = False
            # matches lines with possible whitespace,
            # then letters inside '' then whitespace,
            # also needed to add 1 / and _, because you have names like
            # 1/BO and WAT_DEN
            # then numbers,
            # then letters inside ''
            head_pattern = re.compile(
                r"(\s+)?'([1\/_A-Z\s]+)'\s+(\d+)\s+'([A-Z]+)'"
            )
            for line in funhandle:
                # LOGGER.debug(line)
                # LOGGER.debug(date_record)
                if head_pattern.match(line):
                    LOGGER.debug(f"prev: {prev_name} current: {head_name}")
                    # Storing results from earlier reading
                    try:
                        if type_name not in date_record:
                            date_record[type_name] = OrderedDict()
                        date_record[type_name][head_name] = name_record

                    except UnboundLocalError:
                        LOGGER.debug("Date record does not exist")
                    except TypeError:
                        LOGGER.debug("Date record is not initialized properly")

                    if prev_name == "INTEHEAD":
                        date = parse_intehead(block)
                        # LOGGER.debug(date_record)

                    if len(block) > 0:
                        LOGGER.debug("--> Block defined")
                        name_record[CONTENTS_NAME] = block # count_blocks(block)
                        # exit()
                        block = ""

                    # Defines the name record for the next header
                    head_name, _, head_type = split_head(line)
                    name_record = {HEAD_LINE: line, TYPE_NAME: head_type}

                    # if prev_name == "INTEHEAD":
                    #     exit()
                    # discrete = "INTE" in line

                    LOGGER.debug("---> %s", head_name)

                    if head_name == "STARTSOL":
                        type_name = "solutions"
                        block = ""

                    if head_name == "SEQNUM":
                        date_record = {}
                        type_name = "headers"
                        try:
                            contents[date] = date_record
                            # print(date_record)
                        except UnboundLocalError:
                            LOGGER.debug("No date record defined yet")
                        time.sleep(1)
                        # exit()
                    prev_name = head_name

                else:
                    if discrete:
                        line = re.sub(r"\.[0-9]+", "", line)
                    block += line

    except UnicodeDecodeError:
        LOGGER.error("Cannot read %s, is this a binary file?", path)

    except FileNotFoundError:
        LOGGER.error("Cannot read %s, file does not exist", path)
    # The last ENDSOL will not be included, adding that
    if head_name == "ENDSOL":

        date_record[type_name][head_name] =  {HEAD_LINE: line, TYPE_NAME: head_type}
    # The last date record will not be stored, adding that as well
    contents[date] = date_record
    # print("returning ", contents)
    return contents


def write_fun(contents, file_name="TEST.FUNRST", check_file=None):
    """Writes FUNRST file from dictionary
       args:
           contents (dict): dictionary with contents of future file
           file_name (str): name of output file
    """
    # write_sol = False
    LOGGER.debug("Writing %s", file_name)
    with open(file_name, "w") as outhandle:
        for date in contents:
            LOGGER.debug(date)
            for data_type in contents[date]:
                section = contents[date][data_type]
                for header_name in section:
                        part = section[header_name]
                        print(header_name)
                        print(part.keys())
                        outhandle.write(part[HEAD_LINE])
                        if header_name in ["STARTSOL", "ENDSOL"]:
                            continue
                        outhandle.write(part[CONTENTS_NAME])
    LOGGER.info("Written %s", file_name)
    if check_file is not None:

        check_files(file_name, check_file)
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
