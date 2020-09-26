
import os
import os.path
import uuid

from collections import OrderedDict
import datetime as dt
import json
from django.conf import settings as django_settings


from api.models import JournalEntryLine

class Grader:

    DEFAULT_IGNORE_CASE = False
    DEFAULT_IGNORE_MEMO = False
    DEFAULT_IGNORE_DATE = False
    DEFAULT_IGNORE_PERIOD_BOUNDARIES = False

    def __init__(self, test_company_data:dict, control_company_data:dict, **settings):
        """ Settings
                ignore_case
                ignore_memo
                ignore_date
                ignore_period_boundaries
        """
        self.settings = settings
        self.test_company_data = test_company_data
        self.control_company_data = control_company_data
    
        self.file_uid = str(uuid.uuid4()).replace("-", "")

        self.test_file = os.path.join(
            django_settings.TMP_DIR_PATH, f'test_{self.file_uid}.json')

        self.control_file = os.path.join(
            django_settings.TMP_DIR_PATH, f'control_{self.file_uid}.json')

        self.diff_file = os.path.join(
            django_settings.TMP_DIR_PATH, f'diff_{self.file_uid}.json')


    def generate_git_diff(self) -> str:
        """Convert test and control data to human readable JSON, then take the GIT DIFF between the 2 JSON blobs
        """

        test_str = self._decoded_company_data_to_comparison_json(
            self.test_company_data)
        control_str = self._decoded_company_data_to_comparison_json(
            self.control_company_data)
        
        with open(self.test_file, "w") as f:
            f.write(test_str)
        with open(self.control_file, "w") as f:
            f.write(control_str)
        
        os.system(f"git diff -U8 --no-index {self.control_file} {self.test_file} > {self.diff_file}")
        with open(self.diff_file) as f:
            diff_str = f.read()
        
        self._delete_tmp_files()
        return diff_str
        

    def _delete_tmp_files(self):
        try:
            os.remove(self.test_file)
        except IOError:
            pass
        try:
            os.remove(self.control_file)
        except IOError:
            pass
        try:
            os.remove(self.diff_file)
        except IOError:
            pass

    def _clean_str(self, inp:str) -> str:
        """ Cast string to lower if class is set to case insensitive mode.
        """
        if self.settings.get('ignore_case', self.DEFAULT_IGNORE_CASE):
            return inp.lower()
        return inp


    def _decoded_company_data_to_comparison_json(self, company_data:dict) -> str:
        """ Given a dict of decoded company data, create a human readable JSON string which can be DIFFed against another JSON blob
            {
                "Comapny Name":"Foo Bar",
                "Periods": [
                    {
                        "Start":"Jan 1, 2020",
                        "End":"Mar 31, 2020",
                        "Journal Entries":[
                            {
                                "Date":"Jan 5, 2020",
                                "Memo":"foo bar"
                                "Debits":[
                                    {
                                        "Account":"(1600) Inventory",
                                        "Amount":7500
                                    }
                                ],
                                "Credits":[
                                    {
                                        "Account":"(1000) Cash",
                                        "Amount":7500
                                    }
                                ]
                                "Cash Flow Classifications":{
                                    "Operating Activities":0,
                                    "Investment Activities":0,
                                    "Financing Activities":0
                                }
                            }
                        ]
                    }
                ]
            }
        """
        # map account id to a human readable string
        account_map = {
            a['id']: {'name':self._clean_str(f"({a['number']}) {a['name']}"), 'number':a['number']}
        for a in company_data['accounts']}

        # Map Cashflow worksheet entries to journal entry ids
        # {je_slug:{"operations": 0, "investments": 0, "finances":0}}
        cfws_map = {}
        for cfws in company_data['cash_flow_worksheets']:
            cfws_rows = json.loads(cfws['data'])
            for cfws_row in cfws_rows:
                cfws_map[cfws_row['journal_entry']] = cfws_row


        prepped_data = OrderedDict()
        prepped_data['Company Name'] = self._clean_str(company_data['company']['name'])
        prepped_data['Periods'] = []

        for period_data in company_data['periods']:
            period_id = period_data['id']

            prepped_period_data = OrderedDict()
            if not self.settings.get("ignore_period_boundaries", self.DEFAULT_IGNORE_PERIOD_BOUNDARIES):
                prepped_period_data['Start'] = period_data['start_str']
                prepped_period_data['End'] = period_data['end_str']
            
            prepped_period_data['Jounral Entries'] = []
            
            jounral_entries = [je for je in company_data['journal_entries'] if je['period_id'] == period_id]
            jounral_entries.sort(key=lambda je: dt.datetime.strptime(je['date_str'], "%Y-%m-%d"))
            for je in jounral_entries:
                je_id = je['id']
                je_slug = je['slug']
                prepped_je_data = OrderedDict()

                if not self.settings.get("ignore_date", self.DEFAULT_IGNORE_DATE):
                    prepped_je_data['Date'] = je['date_str']
                if not self.settings.get("ignore_memo", self.DEFAULT_IGNORE_MEMO):
                    prepped_je_data['Memo'] = self._clean_str(je['memo'])
                
                # Add Debit/Credit Lines, sorted by account number
                prepped_je_data['Debits'] = []
                prepped_je_data['Credits'] = []

                je_lines = [jel for jel in company_data['journal_entry_lines'] if jel['journal_entry_id'] == je_id]
                je_lines.sort(key=lambda r: account_map[r['account_id']]['number'])

                for jel in je_lines:
                    key = "Debits" if jel['type'] == JournalEntryLine.TYPE_DEBIT else "Credits"
                    prepped_je_data[key].append(
                        OrderedDict(
                            Account=account_map[jel['account_id']]['name'],
                            Amount=jel['amount']
                        ))

                # Add cash flow worksheet entry for this Journal Entry.
                cf_data = cfws_map.get(je_slug)
                cashflow_ws_entry = OrderedDict()
                cashflow_ws_entry["Operating Activities"] = cf_data['operations'] if cf_data else 0
                cashflow_ws_entry["Investment Activities"] = cf_data['investments'] if cf_data else 0
                cashflow_ws_entry["Financing Activities"] = cf_data['finances'] if cf_data else 0
                prepped_je_data['Cash Flow Classifications'] = cashflow_ws_entry

                prepped_period_data['Jounral Entries'].append(prepped_je_data)

            prepped_data['Periods'].append(prepped_period_data)
                

        return json.dumps(prepped_data, indent=3)

