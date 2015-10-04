"""Module for dealing with a very simple sqlite bug-tracking database

The database is just a table with seven columns as follows:

* The five JOEL test columns:
    * reproduction_steps
    * expected_behavior
    * observed_behavior
    * assigned_to
    * fixed
* Identifier:
    * bug_name
* The two following date columns, which are handled automatically
    * date_created
    * date_fixed


NO OTHER COLUMNS should be relied on. This is made as a basic way to level up in the JOEL test for software development.

No featuritis!!!

If you want to add more columns to the table, that is fine, but do not rely on this module.

Ok, now let's look at how to use this

Detailed usage:
================

What is below assumes you have a configuration file. Named .kansha.default in the base folder of the kansha package.

This configuration file must have, at minimum, a [bug_db] section defined, within which is a `schema_file` and a `file` specified. The `file` option specifies the file where your database is stored.

Make a bug database
-------------
   
    > import kanconfig
    > configs=kanconfig.kansha_configs()
    > schema_file=configs.config.get("bug_db","schema_file")
    > db_file=configs.config.get("bug_db","file")
    > schema_filename=kanbugs.default_bug_db()
    > kanbugs.build_db(db_file,schema_filename)



Create a connection
------------------

Connect to the default BugDB as follows:

    > bdb=kanbugs.default_BugDB()

This will create a connection to the bug database defined in your .kansha.default config file

If you have some different bug database, you can use the following sequence:

The main way of using this module is via the BugDB class.

    > bugdb=kanbugs.BugDB(DB_FILENAME)

DB_FILENAME can be retrieved from your configuration file if you wish:

    > DB_FILENAME=kanbugs.default_bug_db()


List all the unfixed bugs
-----------

Use the list_bugs method

    > bugdb.list_bugs()


Create a new bug via prompts
----------------------------
 
    > bugdb.new_bug()


You can include values in the input to this method to avoid prompting

    > bugdb.new_bug(reproduction_steps="...",expected_behavior="...",observed_behavior="...",assigned_to="...",bug_name="...")

`reproduction_steps` can be a list or text.


Fix a bug
--------------

    > bugdb.fix_bug([bug_name="..."])

If no bug_name is input, then you can choose from the list


Retrieve details about a bug
-------------------------

    > bugdb.bug_details([bug_name="..."])

OR
 
    > bugdb.bug_details(["id=ID"])
 

Dipslay details about a bug
----------------------

    > bugdb.bug_details_display([bug_name="..."])

OR
 
    > bugdb.bug_details_display(["id=ID"]) 

"""

import os

import sqlite3
import logging
import datetime
from kansha import kanio,kanconfig

class BugDB:    

    #define the columns
    STEPS_COLUMN="reproduction_steps"
    XB_COLUMN="expected_behavior"
    OB_COLUMN="observed_behavior"
    ASS_COLUMN="assigned_to"
    FIXED_COLUMN="fixed"
    NAME_COLUMN="bug_name"
    CREATED_DATE_COLUMN="date_created"
    DATE_FIXED_COLUMN="date_fixed"

    BUG_COLUMN_LIST=(    STEPS_COLUMN,
                         XB_COLUMN,
                         OB_COLUMN,
                         ASS_COLUMN,
                         NAME_COLUMN,
    )                              

    BUG_TABLE="bugs"
    
    def __init__(self,filename,**kwargs):
        self.cxn=sqlite3.connect(filename,detect_types=sqlite3.PARSE_DECLTYPES)
        self.cxn.row_factory=sqlite3.Row


    def list_bugs(self):
        """list all active bugs
        """
        q="SELECT {},{},{},{},{},{} FROM {} WHERE {} IS NOT ?".format(
            BugDB.NAME_COLUMN,
            BugDB.STEPS_COLUMN,
            BugDB.XB_COLUMN,
            BugDB.OB_COLUMN,
            BugDB.ASS_COLUMN,
            BugDB.CREATED_DATE_COLUMN,
            BugDB.BUG_TABLE,
            BugDB.FIXED_COLUMN
        )

        params=(1,)
        with self.cxn:
            cur=self.cxn.cursor()
            print(q)
            print(params)
            for row in cur.execute(q,params):
                print("*******************")
                for k in row.keys():
                    print()
                    print("{}".format(k))
                    print("----------")
                    print("{}".format(row[k]))
                print("*******************")                    
                                        

    def new_bug(self,**kwargs):
        """register a new bug, return the ROWID

        Keyword args:
        the column names of the database and their values
        """
        params={}

        try:
            force=kwargs["force"]
        except KeyError:
            force=False

        for column_name in BugDB.BUG_COLUMN_LIST:            
            try:
                params[column_name]=kwargs[column_name]
            except KeyError:
                if not force:
                    params[column_name]=kanio.kanprompt("Enter value for {}".format(column_name))

        if not len(params):
            logging.error("No data given about bug, not inserting it")
            return None
        else:
            #prepare the date data
            params[BugDB.CREATED_DATE_COLUMN]=datetime.datetime.now()
        
        
        q="""INSERT INTO {} ({})
        VALUES ({})""".format(self.BUG_TABLE,",".join(params.keys()),",".join([":{}".format(k) for k in params.keys()]))        

        cur=self.cxn.cursor()
        cur.execute(q,params)
        
        self.cxn.commit()

        return cur.lastrowid

    def fix_bug(self,**kwargs):
        """update the database to specify that the bug is fixed,

        Keyword args:
        bug_name OR id

        If no keyword argument is given, then you will be prompted to choose one       

        """

        params={}

        if "rowid" in kwargs:
            params["ROWID"]=kwargs["rowid"]
        if self.NAME_COLUMN in kwargs:
            params[self.NAME_COLUMN]=kwargs[self.NAME_COLUMN]
        

        q="""UPDATE {} SET {} WHERE {}""".format(
            self.BUG_TABLE,
            ",".join(["{}=1".format(self.FIXED_COLUMN),"{}=:datefixed".format(self.DATE_FIXED_COLUMN)]),
            " AND ".join(["{}=:{}".format(k,k) for k in params])
        )
        params["datefixed"]=datetime.datetime.now()

        cur=self.cxn.cursor()
        cur.execute(q,params)
        self.cxn.commit()

        
        
    def bug_details(self,**kwargs):
        """retrieve a data structure specifying details about a bug

        Keyword args:
        bug_name or id

        If no keyword argument is given, then you will be prompted to choose one               
        """
        params={}
        bug_dets={}

        if "rowid" in kwargs:
            params["ROWID"]=kwargs["rowid"]
        if self.NAME_COLUMN in kwargs:
            params[self.NAME_COLUMN]=kwargs[self.NAME_COLUMN]

        q="SELECT {},{},{},{},{},{},{} FROM {} WHERE {}".format(                               
            BugDB.NAME_COLUMN,
            BugDB.STEPS_COLUMN,
            BugDB.XB_COLUMN,
            BugDB.OB_COLUMN,
            BugDB.ASS_COLUMN,
            BugDB.CREATED_DATE_COLUMN,
            BugDB.FIXED_COLUMN,
            BugDB.BUG_TABLE,
            " AND ".join(["{}=:{}".format(p,p) for p in params])
        )
        row={}
        with self.cxn:
            cur=self.cxn.cursor()
            cur.execute(q,params)
            row=cur.fetchone()
            
        return {k:row[k] for k in row.keys()}

    def bug_details_display(self,**kwargs):
        """retrieve a data structure specifying details about a bug

        Keyword args:
        bug_name or id
        
        If no keyword argument is given, then you will be prompted to choose one               
        """

        params={}

        if "rowid" in kwargs:
            params["rowid"]=kwargs["rowid"]
        if self.NAME_COLUMN in kwargs:
            params[self.NAME_COLUMN]=kwargs[self.NAME_COLUMN]

        q="SELECT {},{},{},{},{},{} FROM {} WHERE {}".format(
            BugDB.NAME_COLUMN,
            BugDB.STEPS_COLUMN,
            BugDB.XB_COLUMN,
            BugDB.OB_COLUMN,
            BugDB.ASS_COLUMN,
            BugDB.CREATED_DATE_COLUMN,
            BugDB.BUG_TABLE,
            " AND ".join(["{}=:{}".format(p,p) for p in params])
        )

        with self.cxn:
            cur=self.cxn.cursor()
            cur.execute(q,params)
            row=cur.fetchone()
            print("*******************")
            for k in row.keys():
                print("")
                print("{}".format(k))
                print("----------")
                print("{}".format(row[k]))
                print("")
            print("*******************")                    
                        
def build_db(db_filename,input_filename):
    if not os.path.isfile(input_filename):
        return None

    conn = sqlite3.connect(db_filename)
    cur=conn.cursor()
    with open(input_filename) as ifh:
        print("Making new bug db: {}".format(db_filename))
        sql=ifh.read()
        cur.executescript(sql)
        conn.commit()

    conn.close()

    if os.path.isfile(db_filename):        
        print("Database created!")
        return True
    else:
        logging.error("No database created!")
        return False
    
def default_bug_db():
    """return the filename of the default bug database, this is based on relative directories"""

    configs=kanconfig.kansha_configs()

    try:
        db_file=os.path.normpath(configs.config.get("bug_db","file"))
        return db_file
    except configparser.NoOptionError:
        return None

def default_BugDB():
    db_file=default_bug_db()
    
    return BugDB(db_file)
