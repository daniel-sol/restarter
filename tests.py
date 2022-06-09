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


def test_read_grdecl(path="../../../../rms/output/pressure.grdecl"):
    """Checks reading of grdecl file
    args:
    path (str): path to grdec file
    """
    outdict = helpers.read_grdecl(path)
    print(outdict.keys())
    # print(outdict)


if __name__ == "__main__":
    # test_read_grdecl()
    test_investigate_string()