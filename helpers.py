""" Helper functions for reading/modifying and storing restart files"""
import logging
import re
import copy
from datetime import datetime, timedelta
import time
import operator
from collections import OrderedDict
from subprocess import Popen, PIPE, CalledProcessError
from pathlib import Path
import numpy as np
import pandas as pd
from xtgeo import grid_from_file
# from ecl2df import grid, EclFiles


# logging.basicConfig()
LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(logging.NullHandler())
# Names to use of the keys in the contents dictionary
HEAD_LINE = "header line"
CONT_NAME = "Contents"
TYPE_NAME = "type"
SOL_NAME = "solutions"
HEAD_NAME = "headers"


def get_grid_actnum(egrid_path):
    """Makes an actnum that is the sum of the grid actnum, and actnum from file
    args:
        egrid_path (str): path to egrid
        grdecl_path (str): path to grdecl_file with actum
    """
    grid = grid_from_file(egrid_path)
    grid_actnum = pd.Series(np.ravel(grid.get_actnum().values, order="F"))

    return grid_actnum


def truncate_num_string(string, cont, **kwargs):
    """Truncates numbers in a string
    args:
    string (str): the string to truncate
    cont (bool): defines whether to convert to float or int
    returns trunc_string (str)
    """
    numbers = string_to_nums(string, cont)
    LOGGER.debug("Truncating a string of length %s", numbers.size)
    valids = ["low", "high"]
    if any(key not in valids for key in kwargs):
        raise KeyError("keyword args must be in ", valids)
    high = kwargs.get("high", numbers.max())
    low = kwargs.get("low", numbers.min())
    numbers[numbers > high] = high
    numbers[numbers < low] = low
    LOGGER.debug("After truncation: min: %s, max: %s", numbers.min(),
                 numbers.max())

    trunc_string = nums_to_string(reshape_nums(numbers, string))
    # LOGGER.debug("Truncated string %s", trunc_string)
    return trunc_string


def ensure_steps(restart, insteps):
    """Checks and sort out steps for input to other functions
    args:
    restart (dict, typically from read_fun): the dictionary to work on
    insteps (string, int or list): valid string are either of strings
                               first, or last
                               entries in list must be iso-8601 format
    """
    all_keys = restart.keys()
    key_list = list(all_keys)
    pre_steps = None
    print(key_list)
    try:
        pre_steps = [key_list[insteps]]

    except TypeError:

        if isinstance(insteps, str):

            LOGGER.info("Fetching step %s", insteps)

            if insteps == "all":

                pre_steps = key_list

            elif insteps == "first":

                insteps = key_list[0]

            elif insteps == "last":
                insteps = key_list[-1]

            if pre_steps is None:
                pre_steps = [insteps]

        else:
            LOGGER.info("Fetching steps %s", insteps)
            pre_steps = insteps
    print("------------")
    print(pre_steps)
    outsteps = []
    for step in pre_steps:
        if step in key_list:
            outsteps.append(step)
        else:
            LOGGER.warning("%s not valid", step)
    if len(outsteps) == 0:
        raise KeyError("No valid steps given")

    return outsteps


def read_actnum(**kwargs):
    """Chooses between actnum options"""
    egrid_path = kwargs.get("egrid_path", None)
    actnum_path = kwargs.get("actnum_path", None)
    actnum = kwargs.get("actnum", None)

    if actnum is None:

        if egrid_path is not None:
            actnum = get_grid_actnum(egrid_path)

        elif actnum_path is not None:
            actnum = read_grdecl(actnum_path)

    return actnum


def replace_with_grdecl(restart, name, grdecl_path, steps="all", **kwargs):
    """Replaces certain property in restart dictionary with contents of grdecl
        args:
    restart (dict, typically from read_fun): the dictionary to work on
    name (str): name of property to truncate
    grdec_path (str): path to grdecl file
    steps (list or string): time steps to use, these must be in iso-8601 format
    kwargs (dict): the options, valid ones are decided by truncate_num_string
    """
    steps = ensure_steps(restart, steps)
    actnum = read_actnum(**kwargs)
    nums = read_grdecl(grdecl_path)
    LOGGER.debug("Have read nums")
    nums = limit_numbers(nums, 1, actnum, "==")

    for step in steps:

        nums = reshape_nums(nums,
                            restart[step][SOL_NAME][name][CONT_NAME])
        LOGGER.debug("Done reshape")
        restart[step][SOL_NAME][name][CONT_NAME] = nums_to_string(nums)


def partial_replace_with_grdecl(restart, name, grdecl_path, replacer_path,
                                oper, steps="all", **kwargs):
    """Replaces certain property in restart dictionary with contents of grdecl
        args:
    restart (dict, typically from read_fun): the dictionary to work on
    name (str): name of property to truncate
    grdecl_path (str): path to grdecl file
    replacer_path (str): path to grdecl file that will be used as filter
    oper (str or list or ): controls what operation to perform when replacing
    steps (list or string): time steps to use, these must be in iso-8601 format
    kwargs (dict): the options, valid ones are decided by truncate_num_string
    """
    LOGGER.debug("The oper: %s", oper)
    LOGGER.debug("The steps given: %s", steps)

    steps = ensure_steps(restart, steps)
    actnum = read_actnum(**kwargs)
    replacement = read_grdecl(grdecl_path)
    replacer = read_grdecl(replacer_path)
    replacement = limit_numbers(replacement, 1, actnum, "==")
    replacer = limit_numbers(replacer, 1, actnum, "==")
    for step in steps:

        org = pd.Series(find_nums(restart[step][SOL_NAME][name][CONT_NAME]))
        changed = replace_numbers(org, replacement, oper, replacer)
        changed = reshape_nums(changed,
                               restart[step][SOL_NAME][name][CONT_NAME])
        restart[step][SOL_NAME][name][CONT_NAME] = nums_to_string(changed)


def truncate_numerical(restart, name, steps=None, **kwargs):
    """Truncates certain property in restart dictionary
    args:
    restart (dict, typically from read_fun): the dictionary to work on
    name (str): name of property to truncate
    steps (list or string): time steps to use, these must be in iso-8601 format
    kwargs (dict): the options, valid ones are decided by truncate_num_string
    """
    steps = ensure_steps(restart, steps)

    for step in steps:
        restart[step][SOL_NAME][name][CONT_NAME] = truncate_num_string(
                restart[step][SOL_NAME][name][CONT_NAME],
                True,
                **kwargs
        )

    return restart


def convertable(string):
    """Checks if string is convertable to number
    args:
    string (str): to check
    returns check (bool): if True it can be converted"""

    check = True
    try:
        float(string.strip())
    except ValueError:
        check = False
        LOGGER.debug("%s not convertable", string)
        # exit()
    return check


def find_nums(string):
    """Find numerical values inside of a text string
    args
    string (str): the string to interrogate
    returns nums (list): list or found numericals

    """
    # Removing comments
    # Adding line break to ensure that the last line is included
    # When removing comment lines
    string += " \n"
    num_string = "".join([part for part in string.split("\n")
                          if not part.startswith("--")])

    # Finding all number like, including - sign,
    # and E or e for scentific numbers
    nums = [num.strip() for num in re.findall(r"[\+0-9\.-eE]+\s+", num_string)
            if convertable(num)]
    # LOGGER.debug(nums)
    LOGGER.debug("Found %s numbers", len(nums))
    return nums

def limit_time_steps(restart, keep_steps):
    """Removes the steps that are not in list keep_steps
        args:
        restart (dict, typically from read_fun): the dictionary to work on
        keep_steps (list, string or int): the steps to keep
    """
    keep_steps = ensure_steps(restart, keep_steps)
    dict_steps = list(restart.keys())
    for step in dict_steps:
        if step not in keep_steps:
            del restart[step]


def limit_time_steps_file(restart, file_name):
    """Removes the steps that are not in file
        args:
        restart (dict, typically from read_fun): the dictionary to work on
        keep_file (string): file with the steps to keep
    """
    try:
        contents = Path(file_name).read_text(encoding="utf-8").split("\n")
        keep_steps = [date for date in contents if date != ""]

    except TypeError:
        LOGGER.debug("File not input")

    limit_time_steps(restart, keep_steps)


def insert_initial_step(restart, subtract_days):
    """Inserts a step at start of restart file
    args:
    restart (dict, typically from read_fun): the dictionary to work on
    subtract_days (int): number of days to subtract
    """
    head_name = "INTEHEAD"
    exist_step = list(restart.keys())[0]
    dateformat = "%Y-%M-%d"
    date = datetime.strptime(exist_step, dateformat)
    earlier_date = date - timedelta(days=subtract_days)
    insert_step = datetime.strftime(earlier_date, dateformat)
    LOGGER.debug("Creating step %s from %s", insert_step, exist_step)

    restart[insert_step] = copy.deepcopy(restart[exist_step])
    restart[insert_step][HEAD_NAME][head_name][CONT_NAME] = change_date_intehead(
      restart[insert_step][HEAD_NAME][head_name][CONT_NAME], insert_step
    )
    restart.move_to_end(insert_step, last=False)

    for i, step in enumerate(restart):
        restart[step][HEAD_NAME]["SEQNUM"][CONT_NAME] = f"    {i}\n"
    steps = list(restart.keys())
    LOGGER.debug(steps)
    time.sleep(3)
    assert steps[0] != steps[1], "Have not managed to insert a unique new step"


def change_date_intehead(header, new_date):
    """changes the date in the header of intehead
    args:
    header (str): the header
    new_date (str): the new date in iso-8601 format
    returns new_header (str): The new header
    """
    head_array = reshape_nums(string_to_nums(header, False), header)
    LOGGER.debug(head_array.shape)
    if new_date.startswith("@"):
        new_date = new_date[1:]
    try:
        year, mon, day = new_date.split("-")
    except ValueError:
        LOGGER.error("Wrong string supplied")
    head_array[11, 0] = int(year)
    head_array[10, 5] = int(mon)
    head_array[10, 4] = int(day)

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
    head_array = reshape_nums(string_to_nums(inte_string, False), inte_string)
    year = int(head_array[11, 0])
    mon = int(head_array[10, 5])
    day = int(head_array[10, 4])
    return_date = f"{year}-{mon:02d}-{day:02d}"
    return return_date


def read_grdecl(path):
    """Reads eclipse grdecl parameter from file
    args:
    path (str): path to file
    returns numbers (pd.Series): name found in file asd key,
                           the numbers from the file as values
    """
    contents = Path(path).read_text(encoding="utf-8")
    # LOGGER.debug(contents)
    strings = [name for name in re.findall(r"[A-Za-z]+", contents)
               if "ECHO" not in name]
    LOGGER.debug(strings)
    name = strings.pop()

    numbers = pd.Series(find_nums(contents), name=name)
    LOGGER.debug("Returning series of lengt %s", numbers.size)
    LOGGER.debug(numbers.head())
    return numbers


def make_selector(limiter, limit_values, oper):
    """makes a boolean pd.Series from a set criteria"""

    LOGGER.debug("Limiter: %s", limiter)
    LOGGER.debug("Limit_values: %s", limit_values)
    LOGGER.debug("Oper: %s", oper)
    operators = {">": operator.gt, ">=": operator.ge,
                 "<": operator.lt, "<=": operator.le,
                 "==": operator.eq, "!=": operator.ne}

    if not isinstance(limit_values, list) and oper not in operators:
        raise TypeError(
            f"operation needs to either be among {operators.keys()} " +
            "or be a list",
        )

    if limiter.dtype == np.object:
        try:
            limit_values = [str(val) for val in limit_values]
        except TypeError:
            limit_values = str(limit_values)

    try:
        LOGGER.debug("Checking if values are in %s", limit_values)
        selector = limiter.isin(limit_values)

    except TypeError:
        LOGGER.debug("Checking if values are %s %s", oper, limit_values)

        selector = operators[oper](limiter, limit_values)

    LOGGER.debug("Selector has %s values", selector.sum())
    LOGGER.debug("Selector is %s", selector)
    return selector


def limit_numbers(nums, limit_values, limiter=None, oper=">"):
    """cuts down the size of a pandas series
    args:
    nums (pd.Series): the series to limit
    limiter (pd.Series): the series to limit with
    limit_values (number or list of numbers)
    """
    if limiter is None:
        limiter = nums.copy()

    LOGGER.debug("Will limit %s", nums)
    LOGGER.debug("Limiter is %s", limiter)
    LOGGER.debug("Will limit %s \n", nums)
    LOGGER.debug("Limiter is %s \n", limiter)
    LOGGER.debug("Limit values are %s", limit_values)
    LOGGER.debug("oper is %s \n", oper)

    selector = make_selector(limiter, limit_values, oper)
    output = nums.loc[selector]

    LOGGER.debug("After limiting size went from %s to %s", nums.size,
                 output.size)

    if output.size == nums.size:
        LOGGER.warning("No reduction happened!")

    return output


def replace_numbers(nums, replacement, replacer_values, replacer=None,
                    oper=">"):
    """swaps the numbers in a pandas series
    args:
    nums (pd.Series): the series to change
    replacer (pd.Series): the series to limit with
    replacement (pd.Series): the series to replace with
    replacer_values (number or list of numbers): The values to be use in
                                                  selection
    """
    LOGGER.debug("nums: %s", nums)
    LOGGER.debug("replace vals %s", replacer_values)
    LOGGER.debug("replacement %s", replacement)
    LOGGER.debug("oper: %s", oper)
    out = nums.copy()
    if replacer is None:
        replacer = nums.copy()

    selection = make_selector(replacer, replacer_values, oper)

    LOGGER.debug("Replacing %s values", selection.sum())
    LOGGER.debug("Replacing %s values", selection.sum())
    out.values[selection] = replacement.values[selection]

    return out


def split_head(line):
    """Splits header line into components
    args:
    line (str): string to split
    returns parts (tuple): first entry is name, second is number of entries
    """
    parts = line.replace("'", "").strip().split()

    LOGGER.debug(parts)
    return parts


def reshape_nums(nums, template_string):
    """Reshapes nums to with template string
    args:
    nums (np.array):
    returns reshaped (np.array): the array reshaped
    """
    inv = investigate_string(template_string)
    if inv["number_count"] != nums.size:
        raise ValueError(
            f"The string is before conversion {nums.size} long, " +
            f"but should be {inv['number_count']}"
            )

    missing = np.empty(inv["missing_count"], dtype=nums.dtype)
    cont = nums.dtype == np.float32
    LOGGER.debug("Trickery with missing")
    if cont:
        LOGGER.debug("Continuous option")
        missing[:] = np.nan
    else:
        LOGGER.debug("Discrete option")
        nums = pd.DataFrame(nums).astype(str).values
        missing = pd.DataFrame(missing).astype(str).values
        missing[:] = ""
    LOGGER.debug("Reshaping")
    reshaped = np.concatenate((nums, missing)).reshape(inv["row_count"],
                                                       inv["col_count"])
    return reshaped


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
    arr = np.array(find_nums(string), dtype=dtype)

    return arr


def nums_to_string(array):
    """Converts numpy array to string
    args:
    array (np.array): what should be converted to string
    return string (str): string from array"""
    string = pd.DataFrame(array).to_string(header=False, index=False,
                                           na_rep="")
    if not string.endswith("\n"):
        string += "\n"
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
    # exit()
    return investigation


def check_fun(restart):
    """Checks that a restart dictionary seems correct
    restart (dict, typically from read_fun): the dictionary to work on
    """
    for date in restart:
        print(f"{date}")
        for name in restart[date]:
            print(f"  {name}")
            for section in restart[date][name]:
                print(f"    {section}")
    print("And that will be all folks!")


def read_back_fun(fun_path):
    """Reads file, returns a list of the lines
    args:
       fun_path (str): path to file
    raises OSError:

    """
    contents = []
    try:
        with open(fun_path, "r", encoding="utf-8") as funhandle:
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


def add_date(contents, date, date_record):
    """Ads date to dictionary from restart file
    args:
    contents (dict): dictionary of restart contents
    date_record (dict): dictionary for given date
    """
    if date is not None and len(date_record) > 0 and date not in contents:
        contents[date] = date_record
    else:
        LOGGER.debug("No date record defined yet")


def read_fun(path):
    """Reads funrst file
    args:
    path (str): name of funrst file
    returns contents (dictionary)
    """
    LOGGER.debug("Reading from %s", path)

    contents = OrderedDict()

    type_name = HEAD_NAME
    block = ""
    line = None
    date = None
    prev_name = None
    head_name = None
    name_record = {}
    date_record = {}
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
    for line in Path(path).open(encoding="utf-8"):
        # LOGGER.debug(line)
        # LOGGER.debug(date_record)
        if head_pattern.match(line):
            # Storing results from earlier reading
            try:
                date_record[type_name] = date_record.get(type_name,
                                                         OrderedDict())
                date_record[type_name][head_name] = name_record

            except TypeError:
                LOGGER.debug("Date record is not initialized properly")

            if prev_name == "INTEHEAD":
                date = find_date(block)
                # LOGGER.debug(date_record)

            if len(block) > 0:
                LOGGER.debug("--> Block defined")
                name_record[CONT_NAME] = block
                block = ""

            # Defines the name record for the next header
            head_name, _, head_type = split_head(line)
            name_record = {HEAD_LINE: line, TYPE_NAME: head_type}

            LOGGER.debug("---> %s", head_name)

            if head_name == "STARTSOL":
                type_name = SOL_NAME
                block = ""

            if head_name == "SEQNUM":
                date_record = {}
                type_name = HEAD_NAME
                add_date(contents, date, date_record)

            prev_name = head_name

        else:
            if head_type == "INTE":
                line = re.sub(r"\.[0-9]+", "", line)
            block += line

    # The last ENDSOL will not be included, adding that
    if head_name == "ENDSOL" and line is not None:
        date_record[type_name][head_name] = {HEAD_LINE: line,
                                             TYPE_NAME: head_type}

    # Under certain conditions the last date record will not be stored,
    # if this is the case adding that as well
    add_date(contents, date, date_record)
    # LOGGER.debug("returning ", contents)
    return contents


def write_fun(contents, file_name="TEST.FUNRST", check_file=None):
    """Writes FUNRST file from dictionary
       args:
           contents (dict): dictionary with contents of future file
           file_name (str): name of output file
    """
    # write_sol = False
    LOGGER.debug("Writing %s", file_name)
    file = Path(file_name)
    with file.open("w", encoding="utf-8") as outhandle:
        for date in contents:
            LOGGER.debug(date)
            for data_type in contents[date]:
                section = contents[date][data_type]
                for header_name in section:
                    part = section[header_name]
                    LOGGER.debug(header_name)
                    LOGGER.debug(part.keys())
                    outhandle.write(part[HEAD_LINE])
                    if header_name in ["STARTSOL", "ENDSOL"]:
                        continue
                    outhandle.write(part[CONT_NAME])
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
    try:
        with Popen(command, stdout=PIPE,
                   stderr=PIPE) as process:
            if not background:
                stdout, stderr = process.communicate()
                if stdout:
                    LOGGER.debug(stdout.decode("utf-8"))

                if stderr:
                    LOGGER.debug(stderr.decode("utf-8"))

    except CalledProcessError:
        LOGGER.error('Could not run command %s', ' '.join(command))
    return out_path
