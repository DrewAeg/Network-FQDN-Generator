# Built-in modules
import csv
import os
import logging
import argparse
import tkinter as tk
from tkinter import filedialog


class OpenFile():
    """A collection of tools asking users which files to open."""

    @staticmethod
    def gui_ask_open_csv():
        defaultextension=".csv"
        filetypes=(("Comma Separated", "*.csv") , ("All Files", "*.*"))
        file_path = OpenFile.gui_ask_open_file(defaultextension,filetypes)
        return file_path


    @staticmethod
    def process_csv(csv_file_path):
        csv_file = open(csv_file_path, 'r')
        csv_contents = csv.reader(csv_file, delimiter=',')
        mycsv = list(csv_contents)
        return mycsv


    @staticmethod
    def gui_ask_open_xls():
        defaultextension=".xlsx"
        filetypes=(("Microsoft Excel 2010", "*.xls") ,("Microsoft Excel", "*.xlsx"), ("All Files", "*.*"))
        file_path = OpenFile.gui_ask_open_file(defaultextension,filetypes)
        return file_path


    @staticmethod
    def gui_ask_open_file(defaultextension=".txt", filetypes=(("Text", "*.txt") , ("All Files", "*.*"))):
        """   defaultextension is looking for a [dot]code file type as a string.  example:
            * defaultextension=".csv"
        filetypes is looging for a tuple, containing tuple pairs of ("description","*.code") pairs.  example:
            * filetypes=(("Comma Separated", "*.csv") , ("All Files", "*.*"))
        
        Builds a dialogue box and make sure the window comes to the front of the desktop
        """
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost',True)
        # Ask the user for the file location
        file_path = tk.filedialog.askopenfilename(defaultextension=defaultextension, filetypes=filetypes )
        # Kill the tk window
        root.destroy()
        return file_path


class NewLineFormatter(logging.Formatter):

    def __init__(self, fmt, datefmt=None):
        """
        Init given the log line format and date format
        """
        logging.Formatter.__init__(self, fmt, datefmt)


    def format(self, record):
        """
        Override format function
        """
        msg = logging.Formatter.format(self, record)

        if record.message != "":
            parts = msg.split(record.message)
            msg = msg.replace('\n', '\n' + parts[0])

        return msg


def setup_logger(log_level='WARNING', log_type='console'):
    # Global Log Formats
    log_format = '%(asctime)s :: %(process)s:%(thread)d :: %(levelname)s :: %(filename)s-%(lineno)s :: %(message)s'

    # Create a new formatter
    formatter = NewLineFormatter(fmt=log_format)

    log_level = log_level.upper()
    if log_type == 'file':
        dir_path = os.path.dirname(os.path.realpath(__file__))
        # NOTE TO SELF:
        # os.path.realpath(path) (returns "the canonical path of the specified filename, eliminating any symbolic links encountered in the path")
        log_file = f'{dir_path}\\logs\\automation.log'
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logging.basicConfig(filename=log_file, format=formatter, level=log_level)
        print(f"Log file located here:\n\
        {log_file}\n")
    else:
        logging.basicConfig(format=formatter, level=log_level)

    logger = logging.getLogger()
    logger.handlers[0].setFormatter(formatter)

    return logger


def table_to_dictionary(table):
    """Takes a table with a top row for column names, and converts table entries to dictionaries."""
    columns = table[0]
    del table[0]
    results = []
    for row in table:
        results.append(dict(zip(columns,row)))
    return results


class SaveFile():
    """A collection of use used for asking users where to save files"""
    @staticmethod
    def gui_ask_save_csv(output_data: list):
        """Pops up a TK interface window that ask where to save a csv-formatted file.

        Input data must be comma-deliminated.  Each row should be a string.

        This fuction assumes you have a header row and at least one row of data.  
        """
        while True:
            try:
                #  Build a dialogue box and make sure the window comes to the front of the desktop
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost",True)
                #  Ask the user for the file name using a dialogue box
                output_file = tk.filedialog.asksaveasfilename(defaultextension=".csv", filetypes=( ("Comma Separated", "*.csv"),("All Files", "*.*") ))
                #  Kill the tk window
                root.destroy()

                #  Open the file and dump the contents of result_table into it
                with open(output_file, "w", newline="") as out_file:    # newline="" is required with python3 to avoid a "double newline"
                    writer = csv.writer(out_file, delimiter=",") 
                    for row in output_data:
                        writer.writerow(row)
            except Exception as error:
                print(error)
                print("\n :: Choose a new location :: ")
            else:
                break

        print("\n\nOutput file can be found here:\n   ",output_file)

        print("\n\n\nPress ENTER to continue.")
        input()


def argument_parser():
    parser = argparse.ArgumentParser(
        #formatter_class=_CustomFormatter,
        fromfile_prefix_chars='@',
        description="An application which helps you build FDQNs from a spreadsheet.",
    )
    parser.add_argument('--log_level',
        dest="log_level",
        type=str.lower,
        default="warning",
        choices=['critical', 'error', 'warning', 'info', 'debug'],
        help="Sets the logging level for the application.",
    )
    parser.add_argument('--log_type', 
        dest="log_type", 
        type=str.lower,
        default="file",
        choices=['console', 'file', 'disabled'],
        help="Sets the logging type for the application",
    )
    return parser