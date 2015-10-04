import csv
from . import fattyio
# import mysql.connector
import sys
import logging
import subprocess
import os.path
from pprint import pformat
import shlex
import os
import re
import datetime
from dateutil import parser
import sqlite3
# from mysql.connector.constants import ClientFlag

def make_db_connect(db,dbsys,infile=0):
    #connect to a database using the given info
    if not dbsys=="sqlite3":
        fattyio.display("Please set your dbsys to be sqlite3, or use the full current branch of fattypy other databases not currently supported")
        return 0
    cnx=None
    conn=sqlite3.connect(db)
    if not infile:
        cnx=mysql.connector.connect(user=u,password=pw,host=h,database=db)
    else:
        cnx=mysql.connector.connect(user=u,password=pw,host=h,database=db,client_flags=[ClientFlag.LOCAL_FILES])
        
    if not cnx:
        return 0
    else:
        return cnx

def delete_all_from_table(db_connect,table):
    cursor=db_connect.cursor()
    logging.info("Deleting all data from %s"%table)
    delete_q="""DELETE FROM %s"""%table
    cursor.execute(delete_q)
    cursor.close()

def mysql_datetimeformat(indatetime,offset_secs=60,return_obj=0):
    dformat="%Y-%m-%d %H:%M:%S"
    logging.debug("Converting in-time %s to object"%indatetime)
    datetime_obj=parser.parse(indatetime)
    
    adjusted_datetime_obj=datetime_obj-datetime.timedelta(seconds=offset_secs)

    mysql_datetime=adjusted_datetime_obj.strftime(dformat)    

    if return_obj:
        return adjusted_datetime_obj
    else:
        return mysql_datetime
    

def mysql_dateformat(indatetime,offset_secs=60):
    outformat="%Y-%m-%d"
    d_obj=parser.parse(indatetime)

    adjusted_d_obj=d_obj-datetime.timedelta(seconds=offset_secs)
    mysql_date=adjusted_d_obj.strftime(dformat)

    return mysql_date

class DBConnect:
    
    def __init__(self,u='',h='',pw="",db="",dbsys="mysql",noconnect=0):
        #initialize the info for dbconnection
        self.user=u
        self.host=h
        if not pw=="":
            self.password=pw     
        else:
            pw=fattyio.prompt_password("Enter password for %s@%s"%(u,h)) 
            self.password=pw
        if not db=="":
            self.database=db
        else:
            self.database=fattyio.fattyprompt("Enter database to use")
        self.dbsys=dbsys
        if not dbsys=="sqlite3":
            logging.critical("Please set your dbsys to be sqlite3, other databases not currently supported")
            sys.exit()
            
        else:
            logging.info("Creating database connection for user %s with password ***** to database %s@%s, a %s connection"%(u,h,db,dbsys))

        cnx=sqlite3.connect(db)
        if not cnx:
            logging.critical("Unable to create database connection using given details, exiting")
            sys.exit()
        else:
            logging.info("Successfully created connection")    
        if not noconnect:
            self.cnx=cnx
            self.cursor=cnx.cursor()
        else:
            cnx.close()

        self.set_date_fieldname_re()
    
    def close_cnx(self):
        self.cnx.close()
        
    def backup_db(self,backup_dir):
        #backup a database by using mysqldump
        if not os.path.isdir(backup_dir):
            logging.critical("Specified backup %s not a directory"%backup_dir)
            sys.exit()
            
        logging.info("Backing up database into directory %s"% backup_dir)
        time=datetime.datetime.now().strftime("%H%M%S")
        #filename=os.path.join(backup_dir,"%s.sql"%time)
        filename=backup_dir+"//%s.backup"%time
        dump_full=shutil.copy(self.database,filename)
        output,error=subprocess.Popen(shlex.split(dump_full),stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
        output,error=fattyio.parse_byte_strings(output,error)
        logging.info("Error: %s"%error)
        logging.info("Output: %s"%output)                    
        success=0 
        error_str=str(error)
        if not ("err" in error_str or "Err" in error_str or "ERR" in error_str):
            success=1
        else:
            success=0
        self.backup_file=filename
        return success

    def get_backup_file(self):            
        #return the backupfile for this db
        backup_file=""
        try:
            backup_file=self.backup_file
            return backup_file
        except AttributeError:
            logging.error("No backup file exists attribute exists for this database")
            return 0

    def load_db(self,fullpath="",mode="single_file",force=0,charset=""):
        #load  db from a given file
        load_db_str=""
        input_dir,filename=os.path.split(fullpath)
        #check if input path is directory
        if not os.path.isdir(input_dir):
            logging.critical("Specified input dir %s not a directory"%input_dir)
            sys.exit()
        logging.info("Loading database from directory %s"% input_dir)
        #if mode is single file, and there is a give filename, check if it exists
        #clean the path
        if mode== "single_file" and filename!="":
            if os.path.exists(fullpath):
                logging.info("Input file %s exists"%fullpath) 
                #if the file exists, create the call string
                #if self.host=="localhost":
                fullpath=mysql_path_format(fullpath)
                if charset:
                    charset="--default-character-set=%s"%charset
                
                if self.dbsys=='mysql': 
                    load_db_str='mysql -h %s -u %s -p%s --execute="source %s" %s %s'%(self.host,self.user,self.password,fullpath,charset,self.database)
                elif self.dbsys=='sqlite3':
                    load_db_str='sqlite3 {}'.format(self.database)
            else:
                #otherwise send an error
                logging.critical("Given input file %s does not exist" % fullpath)
                return False
                sys.exit()
        #multifile mode is not supported yet
        #it is better to load tables one at a time
        elif "mode"=="multifile":
            logging.error("Multi-file database loading is not currently supported,exiting")
            return False
        #if the load is not being forced, ask user for confirmation
        #NOTE: Please do not use force unless necessary in automated creation
        if not force:
            if not fattyio.query_yes_no("Are you sure you want to execute the file %s into the database %s"%(fullpath,self.database),default="no"):
                logging.info("Aborting database load at request of user")
                sys.exit()
        logging.info("Executing mysql command to execute commands into db %s based on input file %s"%(self.database,fullpath))
        ifh=open(fullpath,'r')
        output,error=subprocess.Popen(shlex.split(load_db_str),stdin=ifh,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
        logging.info("Error:%s"%error)
        logging.info("Output:%s"%output)                    
        error_str=str(error)
        if not ("error" in error_str or "Error" in error_str or "ERROR" in error_str):
            return 1
        else:
            return 0
        
    def insert_to_multiple_tables(self,table_data,skip_check_tables=[],skip_all_indicator_tables=[],return_id_tables=[]):
        #insert a single row to multiple tables as needed
        #table data is a dictionary as follows:
        # table_data[0]=
        #{"table":tablename,
        #"values":{field: value},
        #"unique_keys": [unique_key1,unique_key2],
        #"foreign_keys":[
        #{"field": field1, "table": table1},
        #{"field": field2, "table": table2} 
        # ]
        # will not search for existing records in 
        # will break if existing data found in skip_all_indicator_tables
        # the unique key is any value, or combination of values if multiple keys are given, that should be checked when used to search for existing records
        # the foreign key is the column 
        #will return the found id of return_id_table, if given
        return_ids={}
        foreign_keys={}
        logging.debug("Inserting process of inserting data into multiple tables (if existing record doesnt exist)")
        logging.debug("Basing inserts on the following data: %s"%pformat(table_data))
        skipped_tables=[]
        inserted_tables=[]
        for insert_data in table_data:
            
            table=insert_data["table"]
            #field: value
            values=insert_data["values"]            
            #insert a row
            unique_keys=insert_data["unique_keys"]
            unique_keys_values={key: values[key] for key in unique_keys}
            #check if there is an existing entry for this entry
            #check against all info if no unique value is given
            if len(unique_keys)==0:                
                unique_keys_values={key:values[key] for key in values}
                #add a value for the foreign key field if there 
                for fk in [f for f in insert_data["foreign_keys"] if not f["field"] in values]:                    
                    unique_keys_values[fk["field"]]=foreign_keys[fk["table"]] 
                   
            primary_key=""
            if "primary_key" in insert_data:
               primary_key=insert_data["primary_key"] 
            existing_key=None
            if not table in skip_check_tables:
                existing_key=self.check_unique_keys(table,unique_keys_values,text_cols=insert_data["text_cols"],primary_key=primary_key)
            else:
                logging.debug("Not searching for existing value of %s"%table)
            if existing_key in ("",0,"Null",None):
                #there is no existing record
                #insert a new record, but first get foreign key values
                fk_info=insert_data["foreign_keys"]
                #if there is a foreign key, set the value for it
                for fk in fk_info:
                    fk_field=fk["field"]
                    fk_table=fk["table"]
                    try:
                        if not fk_field in values:
                                values[fk_field]=foreign_keys[fk_table]
                    except KeyError:
                        logging.error("Unable to set foreign key data for field %s because no available data found")
                        fattyio.display("Unable to locate foreign key data for the field %s pointing to the %s table"%(fk_field,fk_table))
                inserted_id=self.insert_row_to_table(table,values)
                if table in return_id_tables:
                    return_ids[table]=inserted_id
                #set the foreign key for the current table
                foreign_keys[table]=inserted_id    
                inserted_tables.append(table)
            else:
                #there is already an existing entry, so just set the foreign key entry in case this comes up later
                foreign_keys[table]=existing_key            
                skipped_tables.append(table)                
                if table in return_id_tables:
                    return_ids.append(existing_key)
                logging.debug("Skipping insert to table %s due to existing record with key %s"%(table,pformat(existing_key)))
                if table in skip_all_indicator_tables:
                    logging.debug("Skipping all further entries")
                    break
            #if theres a foreign key
        if len(skipped_tables)>0:
            logging.debug("Skipped tables: %s due to existing records"%pformat(skipped_tables))
        if len(inserted_tables)>0:
            logging.info("Inserted data to tables: %s"%str(inserted_tables))
            logging.debug("Committing all inserts to the database")
            self.cnx.commit()        
        if len(return_id_tables) > 0:
            return return_ids
        
    def insert_row_to_table(self,table,values,commit=0):
        logging.debug("Inserting data into table %s"%table)
        insert_query=" ".join(["INSERT INTO %s"%table,"(%s)"%",".join(values.keys()),"VALUES(%s)"%",".join(["%s" for col in values.keys()])])

        vals=[values[key] for key in values]

        logging.debug("Executing query %s with params %s"%(pformat(insert_query),pformat(vals)))
        #execute_query
        cursor=self.cnx.cursor()
        cursor.execute(insert_query,vals)

        inserted_id=cursor.lastrowid
        if inserted_id:
           # logging.info("Inserted the data to table: %s, last row id %s"%(table,str(inserted_id)))
            if commit:
                logging.info("Committing the changes to the db")
                self.cnx.commit()        
            else:
                logging.debug("Not committing changes")
        else:
            logging.warning("No new row number returned, seems the attempt to insert data failed")
        cursor.close()
        return inserted_id

    def check_unique_keys(self,table,unique_keys_values,text_cols=[],primary_key=""):
        #return 0 if there is no existing row based on the given dictionary of keys and values
        #unique_keys_values is a dictionary of fields->values to check in database
        #otherwise, return the id of the existing row
        id_col=""
        if primary_key=="":
            id_col=table+"_id"
        else:
            id_col=primary_key
        id=0
        cols=[id_col]
        where_values={key: unique_keys_values[key] for key in unique_keys_values}
        tables=[table]
        
        results_cursor=self.select_query(tables,cols,where_values,text_cols=text_cols)
        #logging.info("Checking table %s for existing values: %s"%(table,str(where_values)))        
        results=[]
        for row in results_cursor:
            results.append(row)
        if len(results)>1:
            logging.warning("More than one existing record found to match the unique identifiers %s om table %s, this should be checked and corrected"%(str(results),table))            
            try:
                id=int(results[0][0])
            except ValueError:
                id=results[0][0]
            logging.info("Using first id found, %s"%str(id))
        elif len(results)==1:
            try:
                id=int(results[0][0])
            except ValueError:
                id=results[0][0]
            logging.debug("One result found, using id %s as id"%str(id))    
        elif len(results)==0:
            id=0
            logging.debug("No results found matching the records")
        results_cursor.close()
        return id    

    def select_query(self,tables,cols,where_values,text_cols=[]):
        #return the results from a query 
        logging.debug("Preparing query of table %s, columns %s with conditions %s"%(pformat(tables),pformat(cols),pformat(where_values)))
        select_q="""SELECT """+",".join(cols)+""" FROM """+",".join(tables)
        cond_parts=[]
        #for i,cond in enumerate(
        cond_str=" AND ".join([key+"=%s" for key in where_values])
        full_select_q =select_q+""" WHERE %s"""%cond_str
        params=tuple(where_values[key] for key in where_values)
        
        cursor=self.cnx.cursor()
        logging.debug("Executing query %s based on parameters %s"%(full_select_q,pformat(params))) 
#        logging.info("Number of conditions: %d"%len(conds))
#        logging.info("Number of parameters: %d"%len(params))

        try:
            cursor.execute(full_select_q,params)
        except mysql.connector.errors.DatabaseError as de:
            logging.warning("Unable to execute select query %s"%str(de))
            fattyio.display("Database error: %s"%str(de))
            fattyio.display("Params: %s"%str(params))
            #collation="utf8_general_ci"
#            logging.info("Trying different collation: %s"%collation)
            conds=[col+"=BINARY %s" for col in text_cols if col in where_values]
            for t in where_values:
                if t in text_cols:
                    continue
                else:
                    conds.append(t+"=%s")            
            full_cond=" AND ".join(conds)
            full_select_q=select_q+" WHERE %s "%full_cond
            logging.info("Trying new query: %s based on parameters %s"%(full_select_q,str(params)))
            logging.info("Number of conditions: %d"%len(conds))
            logging.info("Number of parameters: %d"%len(params))
            cursor.execute(full_select_q,params)
            
        return cursor

    def load_data_into_tables(self,fn,table,fieldterminator=",",lineterminator="\r\n",ignore_lines=1,col_list=[]):
        load_q="""LOAD DATA LOCAL INFILE '%s' INTO TABLE %s"""%(fn,table)
        load_q = load_q+"""\nFIELDS TERMINATED BY '%s' """%fieldterminator        
        load_q = load_q+"""\nLINES TERMINATED BY '%s'"""%lineterminator
        load_q= load_q+"""\nIGNORE %d LINES"""%ignore_lines
        if len(col_list)>0:
            load_q = load_q+"""\n(%s)"""%",".join(col_list)
        
        cursor=self.db_connect.cursor()        
        cursor.execute(load_q)


    def set_date_fieldname_re(self):
        self.date_fieldname_re=[]
        for pat in ["date","datetime","nengappi"]:
            self.date_fieldname_re.append(re.compile(r".*"+pat+"$"))
        
        
    def is_datefield(self,field):
        #return yes if the field is a date or datetime field
        
        for pat in self.date_fieldname_re:
            if pat.match(field):
                return 1
        
        return 0
                                    
def mysql_path_format(path):
    path=os.path.normpath(path)    
    #replace backslashes with forward slashes
    #
    return path.replace("\\","/")
