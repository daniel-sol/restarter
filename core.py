"""Contains class to modify restart files"""
import logging
from restarter import helpers


class RestartFile:
    """Class for modification of eclipse restart files"""

    def __init__(self, binary_path) -> None:
        """Sets some primary attributes converts binary to ascii,
        creates dict
        args:
        binary_path (str): path to existing restart file
        """
        self._binary_path = binary_path
        self._ascii_path = helpers.convert_restart(binary_path)
        self._dictionary = helpers.read_fun(self._ascii_path)
        self._actnum = helpers.get_grid_actnum(binary_path.replace("UNRST",
                                                                   "EGRID"))
        self._logger = logging.getLogger(__name__)
        self._logger.addHandler(logging.NullHandler())

    @property
    def binary_path(self):
        """Returns path of binary file"""
        return self._binary_path

    @property
    def ascii_path(self):
        """Returns path of ascii file"""
        return self._ascii_path

    @property
    def dictionary(self):
        """Returns the dictionary"""
        return self._dictionary

    @dictionary.setter
    def dictionary(self, dictionary):
        """Sets the dictionary attribute"""
        self._dictionary = dictionary

    @property
    def actnum(self):
        """Returns actnum"""
        return self._actnum

    @actnum.setter
    def actnum(self, actnum):
        """Sets actnum"""
        self._actnum = actnum

    @property
    def steps(self):
        """Returns steps in restart file"""
        return self.dictionary.keys()

    def write_fun(self):
        """Writes the dictionary back to ascii file"""
        print(f"Writing {self._dictionary.keys()} to {self._ascii_path}")
        return helpers.write_fun(self._dictionary, self._ascii_path)

    def replace_with_grdecl(self, prop_name, grdecl_path, steps):
        """Replaces property in self._dictionary with contents of grdecl file
        args:
        prop_name (str): name of property to be replaced
        grdecl_path (str): path to existing grdecl file to be used
        steps (list or string): time steps to use in ISO-8601 format, or
        """
        self._logger.info("Replacement ongoing")
        kwargs = {"actnum": self._actnum}
        helpers.replace_with_grdecl(self._dictionary, prop_name, grdecl_path,
                                    steps, **kwargs)

    def partial_replace_with_grdecl(self, prop_name, grdecl_path,
                                    replacer_path, oper, steps):

        """Does a partial replace of a property in self._dictionary
        args:
        prop_name (str): name of property to be replaced
        grdecl_path (str): path to existing grdecl file to be used
        replacer_path (str): path to file for controlling where to replace

        steps (list or string): time steps to use in ISO-8601 format, or
        """
        kwargs = {"actnum": self._actnum}

        helpers.partial_replace_with_grdecl(self._dictionary, prop_name,
                                            grdecl_path, replacer_path,
                                            oper, steps,
                                            **kwargs)

    def insert_initial_step(self, subtract_days):
        """Insert initial step in self._dictionary, bases it on the first
           existing step
        args:
        subtract_days (int): number of days to subtract
        """
        helpers.insert_initial_step(self._dictionary, subtract_days)

    def truncate_property(self, prop_name, steps, **kwargs):
        """Truncates property in self._dictionary
        args:
        prop_name (str): name of property to be replaced
        steps (list or string): time steps to use in ISO-8601 format, or
        """
        helpers.truncate_numerical(self._dictionary, prop_name, steps,
                                   **kwargs)

    def limit_time_steps(self, keep_steps):
        """Removes the steps that are not in list keep_steps
        args:
        keep_steps (list, string or int): the steps to keep

        """
        try:
            helpers.limit_time_steps_file(self._dictionary, keep_steps)
        except TypeError:
            helpers.limit_time_steps(self._dictionary, keep_steps)

    def __del__(self):
        """Writes back to ascii file, then converts to binary"""
        helpers.convert_restart(self.write_fun())
