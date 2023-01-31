"""
Provides a data layer for interacting with mobile AL data in CSV format.
"""
import collections
import csv
from datetime import datetime
from typing import Optional, TextIO, OrderedDict, Union, List, Dict, Generator


class MobileData:
    """
    Data wrapper around a mobile AL CSV data file. Allows for opening CSV files and getting their
    data similar to normal file objects. Can also be used for writing data to a file.

    Expects files to be in CSV format, with the first two rows being header rows:
    First: List of comma-separated field names
    Second: List of comma-separated field types matching the names in the previous row. Types:
        - dt: a datetime object
        - f : a float
        - s : a str

    All other rows following must be the same number of items as the headers. (Any missing data
    should be represented by an empty slot. In other words, there should be the same number of
    commas on every line.) Each value is converted to the type specified for its column when
    read.

    Example:

    stamp,x,y,label
    2020-03-24 15:00:00.0000,1.0,-7.3,Example
    2020-03-24 15:00:00.2000,0.7,,

    """

    # Allowed file interaction modes:
    read_modes = ['r']  # modes for reading
    write_modes = ['w', 'a']  # modes for writing
    allowed_file_modes = read_modes + write_modes

    # Allowed field types and their mapping:
    field_type_map = {
        'f' : float,
        's' : str,
        'dt': datetime
    }

    # Format for datetime strings:
    datetime_format = '%Y-%m-%d %H:%M:%S.%f'

    def __init__(self, file_path: str, mode: str):
        """
        Initialize the class with the given file path and mode.
        Note that the file must actually be opened with the `open()` method.
        TODO: Should we change this to open the file here instead?

        Parameters
        ----------
        file_path : str
            Path to the file to open
        mode : str {'r', 'w', 'a'}
            Mode to open the underlying file in (Same as normal file `open()`, though only r/w/a is
            supported (no r+ mode). Also, 'b' mode is not supported)
        """

        self.file_path = file_path

        if mode not in self.allowed_file_modes:
            msg = f"The mode {mode} is not allowed. Must be one of {self.allowed_file_modes}"
            raise ValueError(msg)

        self.mode = mode

        # Handle to underlying file:
        self.f = None  # type: Optional[TextIO]

        # CSV handler for the file:
        self.csv = None  # type: Optional[Union[csv.reader, csv.writer]]

        # OrderedDict of fields and their types (string labels indicating the types)
        # Mapping is field_name->field_type_string
        # The order of the keys in the dict will specify the order of fields in the file
        self.fields = None  # type: Optional[OrderedDict[str, str]]

        # Flag for whether the headers have already been written or not:
        self.headers_written = False

    def open(self):
        """
        Open the underlying file in order to interact with it.
        Also sets up the headers and datatypes for the file based on the first two rows of the file.
        """

        self.f = open(self.file_path, self.mode)

        # Set up the appropriate CSV handler (read or write) for the file:
        if self.mode in self.read_modes:
            self.csv = csv.reader(self.f)

            self.read_headers()  # also read the headers of the file to get fields
        else:
            self.csv = csv.writer(self.f, quoting=csv.QUOTE_MINIMAL)

    def close(self):
        """Close the underlying file."""

        self.f.close()

    def __enter__(self):
        """
        Called when the context is opened (`with`).
        See https://docs.python.org/3/library/stdtypes.html#typecontextmanager

        We will call the `open()` method and return `self`
        """

        self.open()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called when the context is closed. We just call `close()`.
        """

        self.close()

    def read_headers(self):
        """
        Read the field names and types from the headers of the first two rows of the CSV file.
        Sets the headers on this object.
        """

        if self.mode not in self.read_modes:
            msg = f"Mode is {self.mode}, but can only read headers in {self.read_modes} modes."
            raise RuntimeError(msg)

        if self.fields is not None:
            msg = "Fields have already been set - don't read headers."
            raise RuntimeError(msg)

        self.fields = collections.OrderedDict()

        # Read the first two rows (headers) to get field names and types:
        field_names = next(self.csv)
        field_type_strs = next(self.csv)

        if len(field_names) != len(field_type_strs):
            msg = f"{len(field_names)} field names were given, but {len(field_type_strs)} types"
            raise ValueError(msg)

        for i, field_name in enumerate(field_names):
            field_type_str = field_type_strs[i]

            if field_type_str not in self.field_type_map:
                msg = f"The field type '{field_type_str}' is unknown"
                raise ValueError(msg)

            self.fields[field_name] = field_type_str

    def set_fields(self, fields: OrderedDict[str, str]):
        """
        Set the fields based on the provided dictionary mapping field_name->field_type_string.

        Parameters
        ----------
        fields : OrderedDict[str, str]
            An *ordered* dictionary that maps each field name to a string representing its type
            Note that only 'f', 's', and 'dt' (`field`, `str`, `datetime`) types should be used
            The order of the items in the dictionary sets the field order
        """

        for field_name, field_type in fields.items():
            if field_type not in self.field_type_map:
                msg = f"The field type '{field_type}' for field '{field_name}' is unknown"
                raise ValueError(msg)

        self.fields = fields

    def write_headers(self):
        """
        Write the headers to the CSV file. This can only be done once in the file and only for
        files open in write mode.
        Field definitions must have already been set with the `set_fields()` method.
        """

        if self.mode not in self.write_modes:
            msg = f"Mode is {self.mode}, but can only write headers in {self.read_modes} modes."
            raise RuntimeError(msg)

        if self.fields is None:
            msg = "The fields property must be set before writing the headers. Use `set_fields()`."
            raise RuntimeError(msg)

        if self.headers_written:
            msg = "Headers have already been written to file by this object. They can only be written once."
            raise RuntimeError(msg)

        self.csv.writerow(self.fields.keys())
        self.csv.writerow(self.fields.values())

        self.headers_written = True

    def read_row(self) -> Optional[List[Union[float, str, datetime, None]]]:
        """
        Read the next row from the file as a list of fields. If the end of the file has been
        reached, None is returned instead.
        Any fields with missing values will be entered as None.

        Notes
        _____
        We use the `next()` function on the `csv` object to get the next row.
        That is because the underlying `csv` object is an iterator for getting lines.
        The `csv` object raises a `StopIteration` error when the end of the file is reached, so we
        will check for that.

        Returns
        -------
        Optional[List[Union[float, str, datetime, None]]]
            Field values from the row as a list, or None if the end of the file has been reached
            Values are converted to their specified types
        """

        if self.fields is None:
            msg = "The fields property must be set before reading a row."
            raise RuntimeError(msg)

        try:
            row_as_strs = next(self.csv)

            row_vals = list()
            for i, field_type_str in enumerate(self.fields.values()):
                str_val = row_as_strs[i]

                if str_val == '':
                    row_vals.append(None)
                elif field_type_str == 'f':
                    row_vals.append(float(str_val))
                elif field_type_str == 'dt':
                    row_vals.append(datetime.strptime(str_val, self.datetime_format))
                else:
                    row_vals.append(str_val)

            return row_vals
        except StopIteration:
            return None

    def read_all_rows(self) -> List[List[Union[float, str, datetime, None]]]:
        """
        Read all rows from the file as a list of lists of parsed field values.

        Returns
        -------
        List[List[Union[float, str, datetime, None]]]
            A list where each element is a row from the file (see `read_row()` method)
        """

        rows = list()
        while True:
            row = self.read_row()

            if row is None:
                break

            rows.append(row)

        return rows

    @property
    def rows(self) -> Generator[List[Union[float, str, datetime, None]], None, None]:
        """
        Generator method to yield rows from the file in list format.
        Useful with `for row in data.rows` type situations.

        Returns
        -------
        Generator[List[Union[float, str, datetime, None]], None, None]
            A generator that returns the next row of the file in a list
            See `read_row()` for more info on output list format
        """

        if self.mode not in self.read_modes:
            msg = f"Mode is {self.mode}, but can only read rows in {self.read_modes} modes."
            raise RuntimeError(msg)

        if self.fields is None:
            msg = "The fields property must be set before reading a row."
            raise RuntimeError(msg)

        while True:
            row = self.read_row()

            if row is None:
                break

            yield row

    def read_row_dict(self) -> Optional[Dict[str, Union[float, str, datetime, None]]]:
        """
        Read the next row of the file to a dictionary of key->value items. If the end of the file
        has been reached, None is returned instead.

        Returns
        -------
        Optional[Dict[str, Union[float, str, datetime, None]]]
            A dict of field_name->value items for the next row in the file
        """

        row_vals = self.read_row()

        if row_vals is None:
            return None

        return dict(zip(self.fields.keys(), row_vals))

    def read_all_rows_dict(self) -> List[Dict[str, Union[float, str, datetime, None]]]:
        """
        Read all rows of the file to a list of dictionaries, one for each row.

        Returns
        -------
        List[Dict[str, Union[float, str, datetime, None]]]
            List of dictionaries, one for each row in the file
        """

        rows = list()
        while True:
            row = self.read_row_dict()

            if row is None:
                break

            rows.append(row)

        return rows

    @property
    def rows_dict(self) -> Generator[Dict[str, Union[float, str, datetime, None]], None, None]:
        """
        Generator method to yield rows from the file in dictionary format.
        Useful with `for row in data.rows` type situations.

        Returns
        -------
        Generator[Dict[str, Union[float, str, datetime, None]], None, None]
            A generator that returns the next row of the file in a dictionary
            See `read_row_dict()` for more info on output list format
        """

        if self.mode not in self.read_modes:
            msg = f"Mode is {self.mode}, but can only read rows in {self.read_modes} modes."
            raise RuntimeError(msg)

        if self.fields is None:
            msg = "The fields property must be set before reading a row."
            raise RuntimeError(msg)

        while True:
            row = self.read_row_dict()

            if row is None:
                break

            yield row

    def write_row(self, vals: List[Union[float, str, datetime, None]]):
        """
        Write a list of field values to the file.

        TODO: Should we remove the len and self.fields set checks, to increase speed?

        Parameters
        ----------
        vals
            List of field values (in original types). Note that the length must match the number
            of fields specified on this object.
        """

        if self.fields is None:
            msg = "The fields property must be set before writing a row. Use `set_fields()`"
            raise RuntimeError(msg)

        if len(vals) != len(self.fields):
            msg = f"{len(vals)} values given in row, but there are {len(self.fields)} fields."
            raise ValueError(msg)

        vals_str = list()
        for i, field_type_str in enumerate(self.fields.values()):
            field_val = vals[i]

            if field_val is None:
                vals_str.append('')
            elif field_type_str == 'dt':
                vals_str.append(field_val.strftime(self.datetime_format))
            else:
                vals_str.append(str(field_val))

        self.csv.writerow(vals_str)

    def write_row_dict(self, vals_dict: Dict[str, Union[float, str, datetime, None]]):
        """
        Write a dictionary of field values to the file.

        Parameters
        ----------
        vals_dict : Dict[str, Union[float, str, datetime, None]]
            A dict of field_name->value items for the next row in the file
            Any keys in the dictionary not in the fields list will not be included
            Any fields in the fields list without keys in the dictionary will be written as empty
        """

        if self.fields is None:
            msg = "The fields property must be set before writing a row. Use `set_fields()`"
            raise RuntimeError(msg)

        vals_list = list()
        for field_name in self.fields.keys():
            if field_name in vals_dict:
                vals_list.append(vals_dict[field_name])
            else:
                vals_list.append(None)

        self.write_row(vals_list)

    """
    Methods for reading/writing to a file in one method call (opens file and does all work then
    closes it all in one call).
    """

    @staticmethod
    def read_rows_from_file(file_name: str) -> List[List[Union[float, str, datetime, None]]]:
        """
        Read all rows from the file with the given file name. Returns a list of rows as lists.
        """

        with MobileData(file_name, 'r') as in_file:
            return in_file.read_all_rows()

    @staticmethod
    def read_rows_from_file_dict(file_name: str) \
            -> List[Dict[str, Union[float, str, datetime, None]]]:
        """
        Read all rows from the file with the given file name. Returns a list of rows as dicts.
        """

        with MobileData(file_name, 'r') as in_file:
            return in_file.read_all_rows_dict()

    @staticmethod
    def write_rows_to_file(
            file_name: str,
            fields: OrderedDict[str, str],
            rows_to_write: List[List[Union[float, str, datetime, None]]],
            mode: str = 'w'
    ):
        """
        Write all rows in the given list to the file with the given name.

        Parameters
        ----------
        file_name : str
            Path to the file to write to
        fields : OrderedDict[str, str]
            Ordered dictionary mapping of field_name->field_type (as str) to use
            See more info on `set_fields()`
        rows_to_write : List[List[Union[float, str, datetime, None]]]
            List of rows (as lists) to write to the given file
            Should match the fields and order provided in `fields` parameter
        mode : {'w', 'a'}, default 'w'
            The mode to open the file in (defaults to write mode ('w'))
            If opened in write mode, the headers will be written to the file at the start
            If in append mode, headers will not be written as they are assumed to already be in file
        """

        if mode not in MobileData.write_modes:
            msg = f"Provided mode '{mode}' is not allowed - must be one of {MobileData.write_modes}"
            raise ValueError(msg)

        with MobileData(file_name, mode) as out_file:
            out_file.set_fields(fields)

            if mode == 'w':
                out_file.write_headers()

            for row in rows_to_write:
                out_file.write_row(row)

    @staticmethod
    def write_rows_to_file_dict(
            file_name: str,
            fields: OrderedDict[str, str],
            rows_to_write: List[Dict[str, Union[float, str, datetime, None]]],
            mode: str = 'w'
    ):
        """
        Write all rows in the given list to the file with the given name. Rows must be provided as
        dictionaries of field_name->value mapping

        Parameters
        ----------
        file_name : str
            Path to the file to write to
        fields : OrderedDict[str, str]
            Ordered dictionary mapping of field_name->field_type (as str) to use
            See more info on `set_fields()`
        rows_to_write : List[Dict[str, Union[float, str, datetime, None]]]
            List of rows (as dicts) to write to the given file
            Should be field_name->value mapping
        mode : {'w', 'a'}, default 'w'
            The mode to open the file in (defaults to write mode ('w'))
            If opened in write mode, the headers will be written to the file at the start
            If in append mode, headers will not be written as they are assumed to already be in file
        """

        if mode not in MobileData.write_modes:
            msg = f"Provided mode '{mode}' is not allowed - must be one of {MobileData.write_modes}"
            raise ValueError(msg)

        with MobileData(file_name, mode) as out_file:
            out_file.set_fields(fields)

            if mode == 'w':
                out_file.write_headers()

            for row in rows_to_write:
                out_file.write_row_dict(row)
