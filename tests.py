"""Tests for restarter"""
import sys
import pytest
import numpy as np
import helpers
# import restarter.helpers as helpers
# import restarter.core as core


@pytest.fixture
def return_string():
    "Returns the test string"
    string = " 1 2 3\n 4 5 6\n 7 8 9\n 10 11\n"
    print(f"This is the string\n {string}")
    return string


@pytest.fixture
def pressure_property(path="test_data/pressure.grdecl"):
    "Reads property, used in tests below"
    return helpers.read_grdecl(path)


@pytest.fixture
def actnum_property(path="test_data/actnum.grdecl"):
    """Checks reading of grdecl file
    args:
    path (str): path to grdecl file
    """
    return helpers.read_grdecl(path)


@pytest.fixture
def restart_dict(path="test_data/large.FUNRST"):
    """Reads fun file into dictionary
    args:
    path (str): path to fun file
    """
    return helpers.read_fun(path)


def test_ensure_steps():
    """Tests function ensure steps in helpers"""
    test_dict = {"2020-1-1": [], "2020-1-2": []}
    test_keys = list(test_dict.keys())
    func = helpers.ensure_steps
    steps_tests = {"all": test_keys, "first": [test_keys[0]],
                   "last": [test_keys[-1]], 0: [test_keys[0]], 1: [test_keys[1]],
                   -1: [test_keys[-1]]}
    for step in steps_tests:
        return_val = func(test_dict, step)
        error_string = f"{step} returned {return_val} should be {steps_tests[step]}"
        print(f"{step} gives {return_val}")
        assert return_val == steps_tests[step], error_string


def test_find_nums_mixed_string(path="test_data/mixed_string.txt"):
    """finding nums in a mixed string"""
    with open(path, "r") as inhandle:
        mixed = inhandle.read()
    nums = helpers.find_nums(mixed)
    correct_size = 104
    num_size = len(nums)
    print(nums)
    assert  num_size == correct_size, f"Wrong set of numbers {num_size} vs {correct_size}"


def test_restart_dict(restart_dict):
    """Checks reading of restart"""
    helpers.check_fun(restart_dict)


def test_nums_to_string():
    """Tests function nums_to_string"""
    string = helpers.nums_to_string(np.arange(10))
    results = '  0\n  1\n  2\n  3\n  4\n  5\n  6\n  7\n  8\n  9\n'
    assert string == results, f"String is {string}, should be {results}"


def test_find_nums():
    """Tests finding the numbers in a string"""
    string = (
    """
    173.882751     174.296326     135.613281     173.494736
    174.038651      174.70993     175.039764     173.864014
    173.338898     173.834641     173.955643     174.093491
     135.79747     136.025009     174.171631     135.828781
    174.465851     174.300064     135.832092     174.346695
    174.461823      174.39386     175.045898     174.638412
    175.123505     175.396927     136.099228     174.273865
    174.470627     174.196945     173.681488     174.174561
    174.522537     174.257263     174.403656     174.384125
    136.027695      135.78096      135.66568     135.701187
    174.245178     174.034698     136.145401     135.818314
    174.650925     174.610596     135.962921     174.786819
    174.445267     174.728653     174.567001     136.267166
    174.733124     174.601501     136.447388     174.626205
    174.654755     174.788223     136.145569     136.177948
    """)
    nums = helpers.find_nums(string)
    print(nums)


def test_key_combinations():
    """tests the combination of keys one can input"""
    the_key_dict = {"2022-02-01": "blah", "22-03-01": "bu",
                    "22-04-01": "hi",  "22-05-01": "ho",
                    "22-06-01": "btw"}
    keys_as_dict = list(the_key_dict)
    all_keys = helpers.ensure_steps(the_key_dict, "all")
    assert all_keys == keys_as_dict, "Does not extract all keys"
    first_key = helpers.ensure_steps(the_key_dict, "first")
    assert first_key == [keys_as_dict[0]], "First key not correctly extracted"
    num_first_key = helpers.ensure_steps(the_key_dict, 0)
    assert num_first_key == [keys_as_dict[0]], "First num key not correctly extracted"

    last_key = helpers.ensure_steps(the_key_dict, "last")
    assert last_key == [keys_as_dict[-1]], "Last key not correctly extracted"
    num_last_key = helpers.ensure_steps(the_key_dict, -1)
    assert num_last_key == [keys_as_dict[-1]], "Last num key not correctly extracted"


def test_restart_dict_keys(restart_dict):
    """Checks reading of restart"""
    print(restart_dict.keys())


def test_investigate_string(return_string):
    """Tests investigation of string"""
    investigation = helpers.investigate_string(return_string)
    print(f"Investigation returns {investigation}")
    assert investigation["number_count"] == 11, "Wrong number count"
    assert investigation["row_count"] == 4, "Wrong row count"
    assert investigation["col_count"] == 3, "Wrong col count"
    assert investigation["complete_square_count"] == 12, "Wrong square count"
    assert investigation["last_count"] == 2, "Wrong last count"
    assert investigation["missing_count"] == 1, "Wrong missing count"
    assert investigation["missing_check"] == 1, "Wrong missing check"


def test_string_to_nums(return_string):
    " Tests conversion of string to numbers"
    array = helpers.string_to_nums(return_string, True)
    assert array.sum() == 66, "Sum is not correct"
    assert array.size == 11, "Size is wrong"
    print(array)
    assert array.dtype == np.float32, "Cont type not good"
    array = helpers.string_to_nums(return_string, False)
    assert array.dtype == np.int32, "Disc type not good"
    new_string = helpers.nums_to_string(array)

    assert isinstance(new_string, str), "String not returned"
    print(new_string)


def test_read_grdecl(pressure_property):
    """Checks reading of grdecl file
    """
    name = pressure_property.name
    size = pressure_property.size

    assert name == "Hydrostatic", f"Name is wrong is {name}, should be Hydrostatic"
    assert size == 770500, f"Wrong size of cont is {size}, should be 770500"


def test_read_disc_grdecl(actnum_property):
    """Checks reading of grdecl file
    args:
    path (str): path to grdecl file
    """
    name = actnum_property.name
    size = actnum_property.size
    assert name == "ACTNUM", f"Name is wrong is {name}, should be ACTNUM"
    assert size == 770500, f"Wrong size of disc is {size}, should be 770500"
    # assert out.dtype = ""


def test_limit_numbers(pressure_property, actnum_property):
    """Testing limiting numbers"""
    limited = helpers.limit_numbers(pressure_property, 1, actnum_property, oper="==")
    size = limited.size
    assert size == 600800, f"Wrong size of disc is {size}, should be 600800"
    return limited


def test_change_intehead(path="test_data/inteheader.txt"):
    """tests changing the inteheader
    args:
    path (str): path to inteheader file
    """
    with open(path, "r") as inhandle:
        header = inhandle.read()

    print(header)
    test_date = "2022-09-01"
    org_date = helpers.find_date(header)
    print(f" org date : {org_date}")
    changed_header = helpers.change_date_intehead(header, "2022-09-01")
    new_date = helpers.find_date(changed_header)
    print(f"original date {org_date}: changed to {new_date} vs {test_date}")
    assert new_date == test_date, "dates are not identical"


def test_read_scientific_string(path="test_data/pressure_string_noscientific.txt"):
    """Tests helper function string_to_nums with scientific numbers"""
    with open(path, "r") as inhandle:
        text = inhandle.read()
    split_string = text.split()
    print(len(split_string))

    nums = helpers.string_to_nums(text, True)

    print(len(nums))


def test_truncate_str(path="test_data/pressure.txt"):
    """test truncation of numbers in a string
    args:
    path (str): path to inteheader file
    """
    with open(path, "r") as inhandle:
        num_string = inhandle.read()
    truncated = np.array(
        helpers.find_nums(helpers.truncate_num_string(num_string, True,
                                                      high=300, low=100)),
    dtype=np.float)
    assert truncated.max() <= 300
    assert truncated.min() >= 100


def test_replace_with_list(pressure_property):
    """Tests replacing part of the contents of a grdecl file"""
    swl_path = "test_data/swl.grdecl"
    zone_path = "test_data/FIPZONE.grdecl"
    zones = helpers.read_grdecl(zone_path)
    swl = helpers.read_grdecl(swl_path)

    assert pressure_property.astype(float).sum() != swl.astype(float).sum(), "Pressure and swl have the same sum, something is wrong"

    print(swl.head())
    print(pressure_property.head())
    new_pressure = helpers.replace_numbers(pressure_property, swl, [1, 2, 3, 4],
                                           zones)
    pressure_property = pressure_property.astype(float)
    new_pressure = new_pressure.astype(float)
    print(new_pressure.head())
    print(pressure_property.sum())
    print(new_pressure.sum())
    assert pressure_property.sum() != new_pressure.sum(), "Sums are equal they should not be"
    assert ~(not new_pressure.equals(pressure_property)), "The two series are the same, they should not be"


def test_replace_function(restart_dict):
    """Tests replacement of a property in restart_dict
    """
    steps = list(restart_dict.keys())
    print(len(steps))
    first_step = steps[0]
    print(first_step)
    sol_name = "solutions"
    press_name = "PRESSURE"
    cont_name = "Contents"
    swl_path = "test_data/swl.grdecl"
    actnum_path = "test_data/actnum.grdecl"
    print("Badabing")
    pre_pressure = restart_dict[first_step][sol_name][press_name][cont_name]
    print(pre_pressure)
    helpers.replace_with_grdecl(restart_dict, press_name, swl_path, first_step,
                                actnum_path=actnum_path)
    post_pressure = restart_dict[first_step][sol_name][press_name][cont_name]
    print(post_pressure)
    assert pre_pressure != post_pressure, "No change after replacement.."
    helpers.write_fun(restart_dict, "test_data/output.FUNRST", "test_data/large.FUNRST")


def test_replace_function_from_restartfile():
    """Tests replacement of a property in restart_dict
    """
    restart = core.RestartFile("test_data/large.unrst")
    steps = list(restart.steps)
    print(len(steps))
    first_step = steps[0]
    print(first_step)
    sol_name = "solutions"
    press_name = "PRESSURE"
    cont_name = "Contents"
    swl_path = "test_data/swl.grdecl"
    restart.actnum_path = "test_data/actnum.grdecl"
    print("Badabing")
    pre_pressure = restart.dictionary[first_step][sol_name][press_name][cont_name]
    print(pre_pressure)
    restart.replace_with_grdecl(press_name, swl_path, first_step)

    post_pressure = restart.dictionary[first_step][sol_name][press_name][cont_name]
    print(post_pressure)
    assert pre_pressure != post_pressure, "No change after replacement.."


def test_make_selector(pressure_property):
    """Tests function make_selector in helpers"""
    print(pressure_property.astype(float).describe())
    zones = helpers.read_grdecl("test_data/FIPZONE.grdecl")
    org_size = pressure_property.size
    assert zones.size == pressure_property.size, "The zones and pressure are not of same size"
    print(org_size)
    results = helpers.make_selector(pressure_property.astype(float), 100, ">")
    greater_size = results.astype(int).sum()
    print(greater_size)
    assert greater_size < org_size, f"No change in size after greater than {greater_size} {org_size}"

    zone_results = helpers.make_selector(zones, [1, 2, 3], "<")
    zone_size = zone_results.astype(int).sum()
    assert zone_size < org_size, f"No change in size after list shortening {zone_size} {org_size}"


def test_insert_initial_step(fun_file="test_data/small.FUNRST"):
    """Tests the insertion of timestep in a funrst file"""
    contents = helpers.read_fun(fun_file)
    correct_date = "2010-01-30"
    assert len(contents.keys()) == 1, "More than one step initially"
    helpers.insert_initial_step(contents, 1)
    steps_after = list(contents.keys())
    assert len(steps_after) == 2, "Another step not added in dictionary"
    assert steps_after[0] != steps_after[1], "The steps are identical, they should not be"
    first_date = helpers.find_date(contents[steps_after[0]]["headers"]["INTEHEAD"]["Contents"])
    second_date = helpers.find_date(contents[steps_after[1]]["headers"]["INTEHEAD"]["Contents"])
    assert first_date != second_date, f"Identical dates, and date is {first_date}"


    check_path = "test_data/TEST.FUNRST"
    helpers.write_fun(contents, check_path)
    made_contents = helpers.read_fun(check_path)
    steps = list(made_contents.keys())
    assert len(steps) == 2, "Another step not added in written file"
    first_step = steps[0]
    second_step = steps[1]
    inteheader = made_contents[first_step]["headers"]["INTEHEAD"]["Contents"]
    inteheader_date = helpers.find_date(inteheader)
    assert first_step == correct_date, f"Wrong step date {first_step} vs {correct_date}"
    assert inteheader_date == correct_date, f"Wrong head date {inteheader_date} vs {correct_date}"
    assert first_step != second_step, "Steps are identical, they shouldn't be"


def test_dictionary_in_core(name="test_data/small.unrst"):
    """Tests dictionary in core"""
    core.RestartFile(name)
    print(core._dictionary)


if __name__ == "__main__":
    test_find_nums_mixed_string()
    # test_find_nums()
    # test_key_combinations()
    # print(sys.path)
    # test_restart_dict(helpers.read_fun("test_data/large.FUNRST"))
    # test_replace_with_list()
    #test_limit_numbers()
    #time.sleep(1)
    # test_read_grdecl()
    # test_change_intehead()
    # test_insert_initial_step()
    # test_investigate_string()
    # test_truncate_str()
