"""Tests for restarter"""
import numpy as np
import helpers


def test_investigate_string():
    """Tests investigation of string"""
    string = " 1 2 3\n 4 5 6\n 7 8 9\n 10 11\n"
    print(string)
    print(helpers.investigate_string(string))
    array = helpers.string_to_nums(string, True)
    assert array.size == 12, "Size is wrong"
    print(array)
    assert array.dtype == np.float32, "Cont type not good"
    # array = helpers.string_to_nums(string, False)
    # assert array.dtype == np.int32, "Disc type is good"
    new_string = helpers.nums_to_string(array)
    assert isinstance(new_string, str)
    print(new_string)


def test_read_grdecl(path="test_data/pressure.grdecl"):
    """Checks reading of grdecl file
    """
    out = helpers.read_grdecl(path)
    name = out.name
    size = out.size

    assert name == "Hydrostatic", f"Name is wrong is {name}, should be Hydrostatic"
    assert size == 770500, f"Wrong size of cont is {size}, should be 770500"
    # print(outdict)
    return out


def test_read_disc_grdecl(path="test_data/actnum.grdecl"):
    """Checks reading of grdecl file
    args:
    path (str): path to grdecl file
    """
    out = helpers.read_grdecl(path)
    print(out)
    name = out.name
    size = out.size
    assert name == "ACTNUM", f"Name is wrong is{name}, should be ACTNUM"
    assert size == 770500, f"Wrong size of disc is {size}, should be 770500"
    # assert out.dtype = ""
    return out


def test_limit_numbers():
    prop = test_read_grdecl()
    disc = test_read_disc_grdecl()
    limited = helpers.limit_numbers(prop, 1, disc, oper="==")
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
    test_date = "@2022-09-01"
    changed_header = helpers.change_date_intehead(header, "2022-09-01")
    new_date = helpers.find_date(changed_header)
    print(f"{test_date} vs {new_date}")
    assert new_date == test_date, "dates are not identical"


def test_read_scientific_string(path="test_data/pressure_string_noscientific.txt"):
    with open(path, "r") as inhandle:
        text = inhandle.read()
    split_string = text.split()
    print(len(split_string))

    nums = helpers.string_to_nums(text, True)

    print(len(nums))


def test_limited_to_string_to_nums():
    limited = test_limit_numbers()
    results = helpers.string_to_nums(limited.to_string(index=False),
                              False)
    print(results)
    size = results.size
    print(size)


def test_reshape_limited_with_string(path="test_data/pressure_string.txt"):
    limited = test_limit_numbers()
    with open(path, "r") as infile:
        press_string = infile.read()
    results = helpers.reshape_nums(limited, press_string)
    print(results.shape)
    size = results.size
    print(size)


def test_truncate_str(path="test_data/pressure.txt"):
    """test truncation of numbers in a string
    args:
    path (str): path to inteheader file
    """
    with open(path, "r") as inhandle:
        num_string = inhandle.read()
    helpers.truncate_num_string(num_string, True, high=300)


def test_replace_with_list():
    """Tests replacing part of the contents of a grdecl file"""
    press_path = "test_data/pressure.grdecl"
    swl_path = "test_data/pressure.grdecl"
    zone_path = "test_data/FIPZONE.grdecl"
    pressure = helpers.read_grdecl(press_path)
    zones = helpers.read_grdecl(zone_path)
    swl = helpers.read_grdecl(swl_path)
    new_pressure = helpers.replace_numbers(pressure, [1, 2, 3, 4], swl,
                                           zones)

    assert not new_pressure.equals(pressure), "The two series are the same, they should not be"
    print(new_pressure.head())

if __name__ == "__main__":
    test_read_scientific_string()
    #test_limit_numbers()
    #time.sleep(1)
    # test_read_grdecl()
    # test_change_intehead()
    # test_investigate_string()
    # test_truncate_str()