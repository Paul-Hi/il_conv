"""
File:   configs.py
Desc:   Object loading and holding configured information.

Copyright (C) 2022 Paul Himmler, Peter Himmler
Apache License 2.0
"""

import configparser
from typing import List
from resources import resource_path
from pathlib import Path

info = {
    'COLUMN_TIMEDATE': ('Date&Time', 'datetime;%Y-%m-%d %H:%M:%S'),
    'COLUMN_ISSUES_ID': ('Issues ID', 'string'),
    'COLUMN_SEVERITY': ('Severity', 'string'),
    'COLUMN_MESSAGEEXT': ('Ext Info', 'string'),
    'COLUMN_SOURCE_FILE': ('File impacted', 'string'),
    'COLUMN_SOURCE_LINE': ('Line impacted', 'int'),
    'COLUMN_SOURCE_COLUMN': ('Col impacted', 'int'),
    'COLUMN_COMMAND': ('Full Cmd', 'string'),
    'COLUMN_DIAG_MSG_NUMBER': ('DiagMsg Number', 'string'),
    'COLUMN_ISSUE_ID': ('issue_id', 'string'),
    'COLUMN_ISSUE_SIL': ('issue_sil', 'string'),
    'COLUMN_ISSUE_SUMMARY': ('issue_summary', 'string'),
    'COLUMN_ISSUE_CREATION': ('issue_created', 'datetime;%Y-%m-%d'),
    'COLUMN_ISSUE_UPDATE': ('issue_updated', 'datetime;%Y-%m-%d'),
    'COLUMN_ISSUE_COMPONENT': ('issue_component', 'string'),
    'COLUMN_AFFECTED_TOOLCHAINS': ('affected_toolchains', 'string'),
    'COLUMN_ISSUE_INSPECTOR': ('issue_inspector', 'string')
}
'''Information regarding all possible columns'''


def get_defaultcfg() -> str:
    '''Reads and returns the default configuration file

    Returns:
        str: The text of the default config file
    '''

    defaultcfg = resource_path("res/default.cfg")
    assert(Path(defaultcfg).is_file())
    input: str
    with open(defaultcfg, "r") as input_file:
        input = input_file.read()
    return input


class Config(object):
    '''The Config objects loads a configuration and stores the configurated informations.
        The size of all stored rows is always smaller than MAX_PAGE_SIZE bytes.

    Attributes:
        config (ConfigParser): The configuration parser
        headings (List[str]): The headings of the configurated columns
        types (List[str]): The types of the configurated columns
        relative_source_path (str): A path that should be cut from file names in the output table

    '''

    def __init__(self, config_file=None):
        self.config = configparser.ConfigParser()

        # try first with passed configuration file
        if config_file and Path(config_file).is_file():
            self.config.read(config_file)
        else:
            # fallback to default configuration
            self.config.read_string(get_defaultcfg())

        self.headings = [None] * len(info)
        self.types = [None] * len(info)
        self.relative_source_path = ''
        self.__column_setup()
        self.__format_options()

    def __column_setup(self):
        '''Loads all column data from the configuration.'''
        column_setup = self.config['column_setup']
        for k in column_setup:
            if column_setup.get(k) == 'disabled':
                continue

            idx = column_setup.getint(k)
            key = k.upper()
            if key in info:
                col_info = info[key]
                if idx > len(info):
                    print('Index', idx, 'for column', key, 'is out of bounds!')
                    continue
                if self.headings[idx] != None:
                    print('Index', idx, 'for column', key,
                          'is already taken by', self.headings[idx] + '!')
                    continue
                self.headings[idx] = col_info[0]
                self.types[idx] = col_info[1]

        # pack - if there is some slot not filled somehow
        self.headings = [h for h in self.headings if h != None]
        self.types = [t for t in self.types if t != None]

    def __format_options(self):
        '''Loads all format options from the configuration.'''
        format_options = self.config['format_options']
        self.relative_source_path = format_options['relative_source_path']

    def get_column_names(self) -> List[str]:
        '''Returns the configurated column heading names.

        Returns:
            List[str]: The configurated column heading names

        '''

        return self.headings

    def get_column_types(self) -> List[str]:
        '''Returns the configurated column types.

        Returns:
            List[str]: The configurated columntypes

        '''

        return self.types

    def cut_path(self, file_path: str) -> str:
        '''Returns the configurated relative source path.

        Returns:
            str: The configurated path to be cut from the file names

        '''

        return file_path.replace(self.relative_source_path, '')
