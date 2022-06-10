""" Helper functions for reading/modifying and storing restart files"""
import logging
import re
import time
from collections import OrderedDict
from subprocess import Popen, PIPE, CalledProcessError
from pathlib import Path
import numpy as np
import pandas as pd
# from ecl2df import grid, EclFiles


logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
# LOGGER.addHandler(logging.NullHandler())
# Names to use of the keys in the contents dictionary
HEAD_LINE = "header line"
CONTENTS_NAME = "Contents"
TYPE_NAME = "type"


def find_nums(string):
    """Find numerical values inside of a text string
    args
    string (str): the string to interrogate
    returns (nums):

    """
    # Finding all number like, including - sign,
    # and E or e for scentific numbers
    nums =   [num.strip() for num in re.findall(r"[0-9\.-eE]+\s+", string)
              if num.strip() not in ["E", "e", "-"]]
    return nums


def change_date_intehead(header, new_date):
    """changes the date in the header of intehead
    args:
    header (str): the header
    new_date (str): the new date in iso.. format
    returns new_header (str): The new header
    """
    head_array = string_to_nums(header, False)
    if new_date.startswith("@"):
        new_date = new_date[1:]
    try:
        year, mon, day = new_date.split("-")
    except ValueError:
        LOGGER.error("Wrong string supplied")
    head_array[11, 0] = int(year)
    head_array[10, 4] = f"{int(mon):02d}"
    head_array[10, 5] = f"{int(day):02d}"

    LOGGER.debug(head_array)
    new_header = nums_to_string(head_array)
    return new_header


def find_date(inte_string):
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
    day_part = re.search(r"\d+\s+\d{1,2}\s*$", parts[10] ).group(0).split()
    LOGGER.debug(day_part)
    return_date = f"@{year_part}-{int(day_part[0]):02d}-{int(day_part[1]):02d}"
    return return_date


def read_grdecl(path):
    """Reads eclipse grdecl parameter from file
    args:
    path (str): path to file
    returns numbers (pd.Series): name found in file asd key,
                           the numbers from the file as values
    """
    contents = Path(path).read_text()
    # LOGGER.debug(contents)
    strings = [name for name in re.findall(r"[A-Za-z]+", contents)
               if "ECHO" not in name]
    LOGGER.debug(strings)
    name = strings.pop()

    numbers = pd.Series(find_nums(contents), name=name)

    return numbers


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


def string_to_nums(string, cont, template_string=None):
    """Converts string to numpy array
       args:
       string (str): string to convert
       cont (bool): decides if array is continuous or discrete
       template_string (str): other string to use in reshaping of string
       returns arr (numy array): the string as an array
    """
    types = {True: np.float32, False: np.int32}
    dtype = types[cont]

    if template_string is None:
        template_string = string
    inv = investigate_string(template_string)
    arr = np.array(find_nums(string), dtype=dtype)
    missing = np.empty(inv["missing_count"], dtype=dtype)
    if cont:
        missing[:] = np.nan
    arr = np.concatenate((arr, missing)).reshape(inv["row_count"],
                                                 inv["col_count"])
    return arr


def nums_to_string(array):
    """Converts numpy array to string
    args:
    array (np.array): what should be converted to string
    return string (str): string from array"""
    string = pd.DataFrame(array).to_string(header=False, index=False,
                                           na_rep="")
    return string


def investigate_string(string):
    """Checks string of text for how many lines
        args:
         string (str): the string of text to check
    returns investigation (dict): dictionary of checks
    """
    rows = string.strip().split("\n")
    investigation = {}

    investigation["number_count"] = len(find_nums(string))

    investigation["row_count"] = len(rows)
    investigation["col_count"] = len(rows[0].strip().split())
    investigation["complete_square_count"] = (
        investigation["row_count"] * investigation["col_count"]
    )
    investigation["last_count"] = len(rows[-1].strip().split())
    investigation["missing_count"] = (
        investigation["col_count"] - investigation["last_count"]
    )
    investigation["missing_check"] = (
        investigation["complete_square_count"] - investigation["number_count"]
    )

    if investigation["missing_count"] != investigation["missing_check"]:
        LOGGER.warning("The numbers don't add up")
    else:
        LOGGER.info("Everything fine")

    LOGGER.debug(investigation)
    return investigation


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
            break


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
                    LOGGER.debug("prev: %s current: %s", prev_name, head_name)
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
                        date = find_date(block)
                        # LOGGER.debug(date_record)

                    if len(block) > 0:
                        LOGGER.debug("--> Block defined")
                        name_record[CONTENTS_NAME] = block
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
        date_record[type_name][head_name] = {HEAD_LINE: line,
                                             TYPE_NAME: head_type}

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

    out_path = (
        str(unrst_path.absolute().parent) + "/" + unrst_path.stem + suffix
    )
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