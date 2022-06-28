"""
File:   tables.py 
Desc:   Over-engineered abstraction to store 2d table data

Copyright (C) 2022 Paul Himmler
Apache License 2.0
"""

import sys
import itertools
from typing import Iterator

Row = dict
'''The Row is a dictionary holding all items of the row'''

MAX_PAGE_SIZE = 16384
'''Maximum size in bytes for one page'''


class Page(object):
    '''The Page object stores rows.
        The size of all stored rows is always smaller than MAX_PAGE_SIZE bytes.

    Attributes:
        rows (List[Row]): The list of stored rows
        binary_size (int): The accumulated binary size of the stored Rows

    '''

    def __init__(self):
        self.rows = []
        self.binary_size = 0

    def append(self, row: Row) -> bool:
        '''Adds a row to the page

        Args:
            row (Row): The row to add

        Returns:
            bool: True on success else False (page is full)
        '''

        row_size = sys.getsizeof(row)
        if self.binary_size + row_size > MAX_PAGE_SIZE:
            return False
        self.rows.append(row)
        self.binary_size += row_size
        return True

    def get_row(self, idx) -> Row:
        '''Retrieves a row from the page for a given index

        Args:
            idx (int): The index of the row to retrieve

        Returns:
            Row: The row at idx
        '''

        return self.rows[idx]

    def __iter__(self) -> Iterator:
        '''
        Returns:
            Iterator: An iterator yielding the rows of the page
        '''

        return iter(self.rows)


class Table(object):
    '''The Table object stores pages.

    Attributes:
        pages (List[Page]): The list of stored pages
        row_count (int): Total number of rows in this table

    '''

    def __init__(self):
        self.pages = [Page()]
        self.row_count = 0

    def append(self, row: Row):
        '''Appends a row to the table

        Args:
            row (Row): The row to append
        '''

        # Check if page has still room for row
        # In case it has, append the row
        # In case it has not, add a new page and append the row
        if not self.pages[-1].append(row):
            new_page = Page()
            new_page.append(row)
            self.pages.append(new_page)

        self.row_count += 1

    def extend(self, table: "Table"):
        '''Extends the table with another one.
            Adds every row from the other table to this one.

        Args:
            table (Table): The table to extend this one with
        '''

        for row in table:
            self.append(row)

    def __clear(self):
        '''Recreates the table'''
        self.__init__()

    def get_sorted(self, key: str) -> "Table":
        '''Returns a new Table with all rows in every page in the table sorted by a certain key

        Args:
            key (str): The key to sort by

        Returns:
            Table: The new table with sorted rows

        '''

        all_rows = list(itertools.chain(*[page.rows for page in self.pages]))
        all_rows.sort(key=lambda d: d.get(key, ""))

        sorted_table = Table()
        for row in all_rows:
            sorted_table.append(row)

        return sorted_table

    def remove_duplicates(self):
        '''Removes all duplicates in all rows in every page in the table'''

        all_rows = list(itertools.chain(*[page.rows for page in self.pages]))
        all_rows = [dict(row_tuple)
                    for row_tuple in {tuple(row.items()) for row in all_rows}]
        self.__clear()

        for row in all_rows:
            self.append(row)

    def __iter__(self) -> Iterator:
        '''
        Returns:
            Iterator: An iterator yielding the rows of all pages in the table
        '''

        for page in self.pages:
            for row in page:
                yield row
