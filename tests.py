import numpy as np
import helpers


def test_investigate_string():
    """Tests investigation of string"""
    string = "1 2 3\n4 5 6\n7 8 9\n 9 10\n"
    print(string)
    print(helpers.investigate_string(string))
    array = helpers.string_to_nums(string, True)
    print(array)
    assert array.dtype == np.float32, "Cont type is good"
    # array = helpers.string_to_nums(string, False)
    # assert array.dtype == np.int32, "Disc type is good"
    new_string = helpers.nums_to_string(array)
    assert isinstance(new_string, str)
    print(new_string)


def test_read_grdecl(path="test_data/short_pressure.grdecl"):
    """Checks reading of grdecl file
    args:
    path (str): path to grdecl file
    """
    out = helpers.read_grdecl(path)
    print(out)
    assert out.name == "Hydrostatic", "Name is wrong"
    # print(outdict)


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


def test_truncate_str(path="test_data/pressure.txt"):
    """test truncation of numbers in a string
    args:
    path (str): path to inteheader file
    """
    with open(path, "r") as inhandle:
        num_string = inhandle.read()
    helpers.truncate_num_string(num_string, True, high=300)


if __name__ == "__main__":
    test_read_grdecl()
    # test_change_intehead()
    # test_investigate_string()
    # test_truncate_str()