# Mobile AL Data Layer

This library provides a data layer to interact with Mobile AL data files in CSV format. It allows
for reading and writing data in a CSV file to Python lists and dictionaries. It provides some
functions similar to the normal Python file object, such as `open()` and `close()` methods and
the ability to use it as a context manager and iterator to loop through rows in the file.

## CSV Data Format

The code expects files to be in CSV format, with the first two rows being header rows:
First: List of comma-separated field names
Second: List of comma-separated field types matching the names in the previous row. Types:
 - `dt`: a datetime object
 - `f` : a float
 - `s` : a str

All other rows following must be the same number of items as the headers. (Any missing data
should be represented by an empty slot. In other words, there should be the same number of
commas on every line.) Each value is converted to the type specified for its column when
read.

Example:

```
stamp,x,y,label
dt,f,f,s
2020-03-24 15:00:00.0000,1.0,-7.3,Example
2020-03-24 15:00:00.2000,0.7,,
```

## Dependencies:
None. Though only tested in newer versions of Python 3 so you may experience issues with older
versions (e.g. before Python 3.5).

## Usage:

The `MobileData` class is the core of the library, and allows interacting with a mobile AL CSV file.
The class keeps an underlying file reference and Python `csv` reader or writer for accessing it.
Based on the fields and their types set in the file headers or provided by you, it will convert each
row's data to/from the specified field types. That is, when reading a CSV file each row's fields
will be converted to their respective normal Python types, and they are converted back to string
format for writing to the CSV file. Missing values are also allowed, and are represented as `None`
values when reading a row (and should be set to `None` where you want missing values when writing).

You will need to first initialize an instance of the `MobileData` class and pass in the file name
to use and the mode (`'r'` (read), `'w'` (write), or `'a'` (append)). Then, you can either open and
close the file manually with (`open()` and `close()`) or use the object as a context manager to let
it handle the open/close for you:

```
with MobileData('input.csv', 'r') as f:
    # Do stuff with f
    # Takes care of open/close automatically
```

### Reading:

You can read from an existing CSV file by using read mode (`'r'`). When a file is opened to read,
the class will automatically read the two header lines to determine the fields in the file. Then,
you can read each line one-at-a-time as either a Python `list` (`read_row()`) or a `dict`
(`read_row_dict()`). You can also read *all* rows at once into a list using `read_all_rows()` or
`read_all_rows_dict()`. Finally, the class has generator properties for all rows as `list`
(`rows`) or `dict` (`rows_dict`) that can be used with `for in` constructs.

Note that the single-row methods (`read_row()` and `read_row_dict()`) will return `None` when the
end of the file is reached. This is analogous to the Python file handle's `readline()` returning
an empty string (`''`) at EOF. Also note that the internal file handle inside the class keeps track
of its state, so if you mix different ways of accessing data on the same object(e.g. reading a 
single row and then reading all rows) the results may be somewhat unexpected.

Finally, you may also get the fields and their types read from the file by accessing the `fields`
property of the object.

#### Examples: 
```
data = MobileData('input.csv', 'r')
data.open()  # automatically reads the header fields from file

while True:
    row = data.read_row()  # read a row as list; row values are converted to specific types
    
    if row is None:  # check for EOF
        break
        
data.close()
```

```
with MobileData('input.csv', 'r') as data:  # context manager handles open/close for you
    for row in data.rows_dict:  # iterate through all rows as dictionaries
        print(row)  # should be a dictionary
```

### Writing:

Opening a file in write (`'w'`) or append (`'a'`) modes allows you to write Python data to the file.
Note however that you will need to manually call methods to set the field types and write the 
headers to the file before writing any data. (If appending, you may not need to write headers but
still need to set fields on the object.)

To do so, call the `set_fields()` method on your object, passing in an `OrderedDict` object whose
keys are the field names and values are the field type strings (`'dt'`, `'f'`, or `'s'`). Once you
have added this, you can then write the headers by calling `write_headers()`. At this point the
object and underlying file are ready for writing rows of data.

To write a row, you can either use the `write_row()` method (which expects a `list` of objects for
the row) or `write_row_dict()` (which uses a dictionary of `field`->`value` mappings). In either
case, only fields set in the `set_fields()` step previously will be written to the row, even if
there are extra values in the `list`/`dict`. Further, any fields specified but *not* included in
the object to write will be set as `None`. In the case of `write_row()`, you should ensure your
`list` object matches up with the same field ordering as the fields you specified (using `None` for
any empty field values) to ensure the correct values and types are used.

When writing either a `list` or a `dict`, note that the values will be treated as being of the
specified types set in the `fields` object you assigned. Incorrect/undefined behavior may result if
a value of the wrong type is passed for a field.

#### Examples: 
```
data = MobileData('ouptut.csv', 'w')
data.open()

fields = OrderedDict({'stamp': 'dt', 'x': 'f', 'y': 'f', 'label': 's'})  # corresponds to example file above

data.set_fields(fields)  # set the fields on the object
data.write_headers()  # write the headers to the file

# Write the rows in the file example above:
data.write_row([datetime(2021, 3, 24, 15, 0, 0, 0), 1.0, -7.3, 'Example'])
data.write_row([datetime(2021, 3, 24, 15, 0, 0, 200000), 0.7, None, None])
        
data.close()
```

```
with MobileData('ouptut.csv', 'r') as data:  # context manager handles open/close for you
    # Set fields and write headers:
    fields = OrderedDict({'stamp': 'dt', 'x': 'f', 'y': 'f', 'label': 's'})  # corresponds to example file above
    
    data.set_fields(fields)  # set the fields on the object
    data.write_headers()  # write the headers to the file
    
    # Write second row of example file; note that dict order does not matter
    # Fields will be written in order specified in set_fields():
    data.write_row_dict({
        'stamp': datetime(2021, 3, 24, 15, 0, 0, 200000),
        'y': None,
        'x': 0.7,
        'other': 23.0  # will be ignored, not in fields list set above
    })  # note no 'label' field - will be written as empty value to CSV
```
