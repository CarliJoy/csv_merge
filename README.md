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
