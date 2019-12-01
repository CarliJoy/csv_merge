#!/usr/bin/env python3
from glob import glob
from typing import List, IO, Union
import logging
from textwrap import indent


logger = logging.getLogger("csv_combine")


def get_files(globbing: Union[List[str], str]) -> List[str]:
    """
    Get all files in start_path folder that match globbing
    The files are sorted
    """
    if isinstance(globbing, list):
        result: List[str] = []
        for file_glob in globbing:
            result += get_files(file_glob)
        return sorted(result)
    return sorted(glob(globbing))


class ReaderError(ValueError):
    pass


class Reader:
    CHUNK_SIZE: int = 1024  # for binary read - how big should be the chunk size of each read attempt
    encoding: str

    def __init__(self, encoding="bytes"):
        """

        :param encoding: Encoding name or bytes for binary mode
        """
        self.encoding = encoding

    def open(self, filename, writing: bool = False) -> IO:
        mode: str = "w" if writing else "r"
        if self.encoding == "bytes":
            mode += "b"
            return open(filename, mode=mode)
        else:
            return open(filename, mode=mode, encoding=self.encoding)

    def get_header(self, file1, file2) -> List[Union[bytes, str]]:
        """
        Get all lines that are identical in the start of the two filed
        They are most likely the header
        """
        header: List[Union[bytes, str]] = []
        with self.open(file1) as f1:
            with self.open(file2) as f2:
                line1 = f1.readline()
                line2 = f2.readline()
                if line1 == line2:
                    header.append(line1)

        return header

    def combine(self, globbing: str, outfile: str):
        line_count = 0
        file_count = 0
        files = get_files(globbing)
        if outfile in files:
            raise ReaderError("You are trying to write into on of the source files. This is not supported!")
        if len(files)<2:
            raise ReaderError("You need to combine at least two files!")
        header = self.get_header(files[0], files[1])

        # Give the user some hints what is happening - nicely formatted
        logger.info(f"Got header comparing matching start lines of '{files[0]}' and '{files[1]}'")
        header_representation = indent("\n".join(repr(line) for line in header), ' '*4)
        logger.debug(f'Header is:\n{header_representation}')

        with self.open(outfile, True) as out_file:
            for line in header:
                out_file.write(line)
            for file in files:
                file_count += 1
                with self.open(file) as in_file:
                    for header_line in range(len(header)):
                        line = in_file.readline()
                        if line != header[header_line]:
                            logger.warning(f"Not header line {header_line} not matching in file '{file}'. "
                                           f"File was still included but header line was ignored.")
                            logger.debug(f"Got: {line}")
                            logger.debug(f"Expected: {header[header_line]}")
                    for line in in_file:
                        line_count += 1
                        out_file.write(line)
        logger.info(f"Combined {file_count} files with a total of {line_count} lines.")


if __name__ == "__main__":
    # Show Info on console
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("target_file", help="Path to combination file")
    parser.add_argument("source", nargs='*', help="Source files - unix globbing supported (= * and ? allowed)")
    args = parser.parse_args()
    reader = Reader()
    try:
        reader.combine(args.source, args.target_file)
    except ReaderError as e:
        logger.exception(f"Could not combine files: {e}")
