# CSV Combine

Script to combine multiple files matching glob in a folder to one single big file.
The common head will be determined automatically based on the number of identical lines of 
the first two files.

The default script uses binary mode to write files - so no encoding problems should occur.

The header will be always taken from the first file.

Missmatches in headers will be logged.

Usage:
`./csv_combine target.csv source1.csv othersources/*.csv`

It is possible to add a verbose parameter as well as --fix-header-lines parameter.
The --fix-header-lines will force the number of header lines instead of determine it with the first two files.

```
$ python csv_combine.py --help
usage: csv_combine.py [-h] [-n FIX_HEADER_LINES] [-v]
                      target_file [source [source ...]]

Combine different csv files but keep the header The header will be determined
automatically be comparing the numberof identical lines of the first two
files.Mismatches of headers will be logged.

positional arguments:
  target_file           Path to combination file
  source                Source files - unix globbing supported (= * and ?
                        allowed)

optional arguments:
  -h, --help            show this help message and exit
  -n FIX_HEADER_LINES, --fix-header-lines FIX_HEADER_LINES
                        Set the number of of head lines instead of determining
                        it by comparingthe first two files.
  -v, --verbose         increase output verbosity


```

