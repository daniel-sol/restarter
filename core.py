"""Contains the class to modify restart files"""
import restarter.helpers as helpers


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
        self._actnum_path = None

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

    @property
    def actnum_path(self):
        """Returns actnum path"""
        return self._actnum_path

    @actnum_path.setter
    def actnum_path(self, grdecl_path):
        """Sets actnum path"""
        self._actnum_path = grdecl_path

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
        steps (list or string): time steps to use in ISO-8601 format, or"""

        kwargs = {"actnum_path": self._actnum_path}
        helpers.replace_with_grdecl(self.dictionary, prop_name, grdecl_path,
                                    steps, **kwargs)

    def partial_replace_with_grdecl(self, prop_name, grdecl_path,
                                    replacer_path, replacement, oper, steps):
        """Does a partial replace of a property in self._dictionary
        args:
        prop_name (str): name of property to be replaced
        grdecl_path (str): path to existing grdecl file to be used
        steps (list or string): time steps to use in ISO-8601 format, or
        """
        kwargs = {"actnum_path": self._actnum_path}
        helpers.partial_replace_with_grdecl(self.dictionary, prop_name,
                                            grdecl_path, replacer_path,
                                            replacement, oper, steps,
                                            **kwargs)

    def insert_initial_step(self, subtract_days):
        """Insert initial step in self._dictionary, bases it on the first
           existing step
        args:
        subtract_days (int): number of days to subtract
        """
        helpers.insert_initial_step(self._dictionary, subtract_days)

    def truncate_property(self, prop_name, steps, kwargs):
        """Truncates property in self._dictionary
        args:
        prop_name (str): name of property to be replaced
        steps (list or string): time steps to use in ISO-8601 format, or
        """
        helpers.truncate_numerical(self._dictionary, prop_name, steps,
                                   **kwargs)

    def __del__(self):
        """Writes back to ascii file, then converts to binary"""
        helpers.convert_restart(self.write_fun())
