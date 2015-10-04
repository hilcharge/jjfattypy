"""Unit tests for the kanbugs database"""

import unittest
from kansha import kanbugs,kanconfig
import datetime
import os

class TestBugDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.configs=kanconfig.kanConfig(os.path.join(os.path.dirname(__file__),"..",".kansha.default"))        
        cls.db_file=cls.configs.config.get("bug_db","test_file")
        cls.schema_file=cls.configs.config.get("bug_db","schema_file")

        #remove the existing test file
        if os.path.isfile(cls.db_file):
            os.remove(cls.db_file)

        #create the new file
        kanbugs.build_db(cls.db_file,cls.schema_file)

        #initialize the bug database
        cls.BugDB=kanbugs.BugDB(cls.db_file)

    @classmethod
    def tearDownClass(cls):
        cls.BugDB.cxn.close()

        os.remove(cls.db_file)
            

    def test_new_bug(self):
        lastrowid=self._insert_data()

        self.assertGreaterEqual(lastrowid,0)

    def test_fix_bug(self):
        newid=self._insert_data()
        
        self.BugDB.fix_bug(rowid=newid)

        q="SELECT {} FROM {} WHERE ROWID=? AND {}=0".format(self.BugDB.NAME_COLUMN,self.BugDB.BUG_TABLE,self.BugDB.FIXED_COLUMN)
        params=(newid,)
        cur=self.BugDB.cxn.cursor()
        cur.execute(q,params)
        rows=cur.fetchall()
        self.assertEqual(len(rows),0)                


    def test_bug_details(self):
        newid=self._insert_data()    

        return_struct=self.BugDB.bug_details(rowid=newid)
        inserted=self._default_insert_data()        

        return_struct_subset={k:return_struct[k] for k in inserted}
        inserted["date"]=datetime.date.today()
        return_struct_subset["date"]=return_struct[self.BugDB.CREATED_DATE_COLUMN].date()

        self.assertTrue(inserted,return_struct_subset)
        

    def _insert_data(self):
        input_data=self._default_insert_data()

        lastrowid=self.BugDB.new_bug(**input_data)

        return lastrowid

    def _default_insert_data(self):
        
        return {self.BugDB.NAME_COLUMN:"test_bug",
              self.BugDB.XB_COLUMN:"dont suc",
              self.BugDB.OB_COLUMN:"totally sucks",
              self.BugDB.ASS_COLUMN:"sucker #1",
              self.BugDB.STEPS_COLUMN:"1. Open program\n2. Do anything"}
            
if __name__=='__main__':
    unittest.main()
