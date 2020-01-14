#!/usr/bin/env python3
import logging
from glob import glob
from textwrap import indent
from typing import List, IO, Union, Optional, Callable

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


def print_status(count, count_max):
    if print_status.first_run:
        # Make sure that we write on a new line running the first time
        print_status.first_run = False
        print("\n")
    len_max = len(str(count_max))
    format_string = f"Read {{:0{len_max}}}/{count_max}"
    print(format_string.format(count), end="\r", flush=True)
    if count == count_max:
        #  Last count should reset everything
        print_status.first_run = True
        print("\n", flush=True)


print_status.first_run = True


class ReaderError(ValueError):
    pass


class Reader:
    # for binary read - how big should be the chunk size of each read attempt
    CHUNK_SIZE: int = 1024
    encoding: str

    def __init__(
        self,
        encoding="bytes",
        status_update_function: Optional[Callable[[int, int], None]] = None,
    ):
        """
        :param encoding: Encoding name or bytes for binary mode
        :param status_update_function: if given it is called on every finished run reading
                                       a file with parameters
                                       (current_file_number, max_file_number)
        """
        self.encoding = encoding
        self.status_func = status_update_function

    def open(self, filename, writing: bool = False) -> IO:
        mode: str = "w" if writing else "r"
        if self.encoding == "bytes":
            mode += "b"
            return open(filename, mode=mode)
        else:
            return open(filename, mode=mode, encoding=self.encoding)

    def get_header(self, file1: str, file2: str) -> List[Union[bytes, str]]:
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

    def get_header_by_lines(self, file1: str, line_count: int) -> List[Union[bytes, str]]:
        header: List[Union[bytes, str]] = []
        with self.open(file1) as f1:
            for line_number in range(line_count):
                line1 = f1.readline()
                header.append(line1)
        return header

    def combine(
        self, globbing: str, outfile: str, force_header_line_number: Optional[int] = None
    ):
        line_count = 0
        files = get_files(globbing)
        if outfile in files:
            raise ReaderError(
                "You are trying to write into on of the source files. This is not supported!"
            )
        if len(files) < 2:
            raise ReaderError("You need to combine at least two files!")

        headers: List[List[str]] = []  # header[number][line_number] = line
        header_files: List[List[str]] = []  # header[number][file_number] = file_name

        if force_header_line_number is None:
            headers.append(self.get_header(files[0], files[1]))
            header_files.append([files[0], files[1]])
            logger.info(
                f"Got header comparing matching start lines of '{files[0]}' and '{files[1]}'. "
                f"Header is {len(headers[0])} lines long."
            )
        else:
            headers.append(self.get_header_by_lines(files[0], force_header_line_number))
            header_files.append([files[0]])
            logger.info(
                f"Read {force_header_line_number} lines of header from '{files[0]}'."
            )
        header_length = len(headers[0])  # define how many lines long is the header

        # Give the user some hints what is happening - nicely formatted
        header_representation = indent(
            "\n".join(repr(line) for line in headers[0]), " " * 4
        )
        logger.debug(f"Header is:\n{header_representation}")

        with self.open(outfile, True) as out_file:
            for line in headers[0]:
                out_file.write(line)
            for file_count, file in enumerate(files):
                with self.open(file) as in_file:
                    # Read and compare headers
                    current_header = []
                    for line_number in range(header_length):
                        current_header.append(in_file.readline())
                    current_compare_header = "\n".join(
                        [repr(line) for line in current_header]
                    )
                    for number, defined_header in enumerate(headers):
                        # Try to find head in already
                        if (
                            "\n".join([repr(line) for line in defined_header])
                            == current_compare_header
                        ):
                            header_files[number].append(file)
                            break
                    else:
                        headers.append(current_header)
                        header_files.append([file])
                    for line in in_file:
                        line_count += 1
                        out_file.write(line)
                if self.status_func is not None:
                    self.status_func(file_count + 1, len(files))
        logger.info(f"Combined {file_count+1} files with a total of {line_count} lines.")

        if len(headers) > 1:
            logger.warning(
                f"Not all file had the same headers. In total {len(headers)} different headers were "
                f"found in {file_count} files."
            )
            logger.info("These headers are:")
            for number, header in enumerate(headers):
                header_representation = indent(
                    "\n".join(repr(line) for line in header), " " * 4
                )
                logger.info(
                    f"Header {number+1} for {len(header_files[number])} files: \n{header_representation}"
                )
                file_list = "\n * ".join(sorted(header_files[number]))
                logger.debug(
                    f"Header {number+1} has was found in the following files: \n * {file_list}"
                )


if __name__ == "__main__":
    # Show Info on console
    import argparse

    parser = argparse.ArgumentParser(
        description="Combine different csv files but keep the header\n"
        "\n"
        "The header will be determined automatically be comparing the number"
        "of identical lines of the first two files."
        "Mismatches of headers will be logged."
    )
    parser.add_argument(
        "-n",
        "--fix-header-lines",
        type=int,
        default=None,
        help="Set the number of of head lines instead of determining it by comparing"
        "the first two files.",
    )
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument("target_file", help="Path to combination file")
    parser.add_argument(
        "source",
        nargs="*",
        help="Source files - unix globbing supported (= * and ? allowed)",
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    reader = Reader(status_update_function=print_status)
    try:
        reader.combine(
            args.source, args.target_file, force_header_line_number=args.fix_header_lines
        )
    except ReaderError as e:
        logger.exception(f"Could not combine files: {e}")
