"""
File:   issuedb.py 
Desc:   Script function to parse Tasking Issue Portal

Copyright (C) 2022 Paul Himmler, Peter Himmler
Apache License 2.0
"""

import requests
import ssl
from bs4 import BeautifulSoup
import issue_store as ist
from issue_store import Issuestore, Portalissue


def populatIssueDBFromFile(file: str, tc_version: str, verbose=False) -> Issuestore:
    '''Populates the issue database with issues loaded from a file

    Args:
        file (str): The file to load the issues from
        tc_version (str): The toolset/compiler toolchain version to lookup
        verbose (bool): Create verbose output during processing

    Returns:
        Issuestore: Dictionary of entries
    '''

    input = ''

    if file != None:
        if verbose:
            print("... fetching data from local testdata. " + file + '\n')
        with open(file) as fp:
            input = fp.read()

    return _populateDB(input, tc_version, verbose)


def populateDBFromIssuePortal(user: str, password: str, tc_version: str, verbose=False) -> Issuestore:
    '''Populates the issue database with issues loaded the issue portal

    Args:
        user (str): User email for login
        password (str): User password for login
        tc_version (str): The toolset/compiler toolchain version to lookup
        verbose (bool): Create verbose output during processing

    Returns:
        Issuestore: Dictionary of entries
    '''

    #
    # Workaround SSL issues
    # [SSL: WRONG_SIGNATURE_TYPE] wrong signature type error.
    #
    class TLSAdapter(requests.adapters.HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            ctx = ssl.create_default_context()
            ctx.set_ciphers('DEFAULT@SECLEVEL=1')
            kwargs['ssl_context'] = ctx
            return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)

    with requests.Session() as s:
        s.mount('https://', TLSAdapter())
        s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'

        print('FETCHING from ', ist.LOGIN_URL, '\n')
        res = s.get(ist.LOGIN_URL)

        soup = BeautifulSoup(res.text, 'html.parser')
        payload = {i['name']: i.get('value', '')
                   for i in soup.select('input[name]')}
        # what the above line does is parse the keys and values available in the login form
        # print(payload)

        payload['login_username'] = user
        payload['secretkey'] = password

        payload['just_logged_in'] = '1'
        payload['issueid'] = ''
        payload['project'] = ist.PROJECT
        payload['version'] = tc_version

        # when you print this, you should see the required parameters within payload
        # print(payload)

        r = s.post(ist.LOGIN_REDIRECT_URL, data=payload)

        input = r.text
        # print (input)

        # as we have already logged in, the login cookies are stored within the session
        # in our subsequesnt requests we are reusing the same session we have been using from the very beginning
        # r = s.get('https://issues.tasking.com/?project=TCVX&version=v6.3r1')

    return _populateDB(input, tc_version, verbose)


def _populateDB(input: str, tc_version: str, verbose) -> Issuestore:
    '''Populates the issue database with issues loaded from HTML input

    Args:
        input (str): HTML input to load issues from
        tc_version (str): The toolset/compiler toolchain version to lookup
        verbose (bool): Create verbose output during processing

    Returns:
        Issuestore: Dictionary of entries
    '''

    issuedict = Issuestore()

    if verbose:
        print("... populate issue portal database")
    if (not input):
        if verbose:
            print("ERR: Got no input to  populate issue portal database!")
        return issuedict

    soup = BeautifulSoup(input, 'html.parser')
    htmltable = soup.body.find("table", attrs={"class": "table-issue-summary"})
    trows = htmltable.find_all('tr')

    headerrow = [th.get_text(strip=True)
                 for th in trows[0].find_all('th')]  # header row
    if len(headerrow) == 0:
        headerrow = [th.get_text(strip=True) for th in trows[0].find_all(
            "td", attrs={"class": "heading"})]  # header row

    if len(headerrow) > 0:
        trows = trows[1:]  # skip header row if any

#    if verbose:
 #       print(headerrow)
 #       print('\n')

    # we use standardize column names and don't care what is written on web/file

    for row in trows:
        # Here we need manually sort what we get from website to sorting order in the namedTuple ()
        #  hardcoded :-|
        #  Website order
        # <td class="td-issue-id">
        # <td class="td-issue-sil">
        # <td class="td-issue-component">
        # <td class="td-issue-affected-toolchains">
        # <td class="td-issue-summary">
        # <td class="td-issue-inspector">
        # <td class="td-issue-date"> CREATED
        # <td class="td-issue-date"> UPDATE
        # SEE issue_store.HEADER_ENTRIES / TYPES
        #             'issue_id',
        #            'issue_sil',
        #            'issue_summary',
        #            'issue_created',
        #            'issue_updated',
        #            'issue_component',
        #            'affected_toolchains',
        #            'issue_inspector'

        col = [td.get_text(strip=True) for td in row.find_all(
            'td', attrs={"class": "td-issue-id"})]
        if len(col) == 1:
            cols = col
        else:
            cols = ['n/a']
        col = [td.get_text(strip=True) for td in row.find_all(
            'td', attrs={"class": "td-issue-sil"})]
        if len(col) == 1:
            cols += col
        else:
            cols += ['n/a']
        col = [td.get_text(strip=True) for td in row.find_all(
            'td', attrs={"class": "td-issue-summary"})]
        if len(col) == 1:
            cols += col
        else:
            cols += ['n/a']
        # NOTE here we get 2 --> as we have created/update one after the other in nameTuple we are fine
        col = [td.get_text(strip=True) for td in row.find_all(
            'td', attrs={"class": "td-issue-date"})]
        if len(col) == 2:
            cols += col
        elif len(col) == 1:
            cols += col + ['n/a']
        else:
            cols += ['', '']

        col = [td.get_text(strip=True) for td in row.find_all(
            'td', attrs={"class": "td-issue-component"})]
        if len(col) == 1:
            cols += col
        else:
            cols += ['n/a']

        col = [td.get_text(strip=True) for td in row.find_all(
            'td', attrs={"class": "td-issue-affected-toolchains"})]
        if len(col) == 1:
            cols += col
        else:
            cols += ['n/a']

        col = [td.get_text(strip=True) for td in row.find_all(
            'td', attrs={"class": "td-issue-inspector"})]
        if len(col) == 1:
            cols += col
        else:
            cols += ['n/a']

        if verbose:
            #print( "COLS\n " + str(cols) )
            # TODO THIS CHECK BETTER as here we now have already correct data
            if ist.HEADER_ENTRIES_NO != len(cols):
                print("WARN:There might be a inconsistent rows within issue table row!")

        entry = Portalissue(*cols)
        # print(entry)
        issuedict[entry.issue_id] = entry

    return issuedict


'''
How to use returned issue dict?

db = populateDBFromIssuePortal( "filename.html" , false);
entry = d.get("TCVX-37419")
if entry:
    # follwing fields are filled from Wbsite/File
    entry.issue_id
    entry.issue_sil
    entry.issue_component
    entry.affected_toolchains,
    entry.issue_summary
    entry.issue_inspector
    entry.issue_created
    entry.issue_updated
...
'''
