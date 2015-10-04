Jjfattypy
============

fattyconfig
-----------

Based on configparser

To use, do the following:

>>>myconfigs=fattyconfig.fattyConfig(configfile)
>>>backup_dir=myconfigs.config.get("dir","backup")


fattylog
---------
based on python's standard logging package

Set a log file:
>>>logdir=fattylog.logdir(folder="") # returns either the given log directory, or a default "MY_LOG_DIR" environment variable
>>>fattylog.setlog(filename,verbose,ft='%(asctime)s [%(levelname)s] %(message)s')


fattyio
--------
Various functions for input, output, and directories

>>>wait=fattyio.wait(text="Press any key to continue")

>>>icsv,ifh=fattyio.open_reader_csv(infilename)

>>>fattyio.combine_files(file_list,outfilename,separator,outputencodings,return_enc="utf8") ### combines the input files into a single file with outfilename, separates them by separator, and makes an output file for each of the given output encodings. It returns the filename of return_enc

>>>full_date_dir=fattyio.make_date_folder_in(base_dir)

## list of files of the given types.
## if nocheck is set to 0, you will be prompted whether the file list is acceptable
>>>list_of_files=fattyio.files_in_dir(dir,nocheck=0,file_types=["csv","tsv"])


## Convert a list of excel files into corresponding .tsv files
>>>list_of_tsv_files=excel_to_tsv(list_of_excel_files)


## Display text 
## Actually this is much worse than print, but it may change in the future
>>>fattyio.display(text)

## Use pprint
>>>fattyio.pdisplay(some_variable)


## Prompt for a value
>>>value= fattyio.fattyprompt(display_text,default_value="sometext")

## Prompt for an integer
>>>myinteger=fattyio.intprompt(display_text,default_int=0)

## display header
>>> header("MY HEADER")
*************
MY HEADER
*************



##smaller header
>>> min_header("Small header")
******* Small header *********

#prompt for a file in a folder
>>> filename=prompt_file(folder,default_file,nocheck=0)
## take default automatically if default is given, if nocheck is set to 1


## Number one most useful for scripting, maybe
>>> answer= query_yes_no("Do you love me?",default="no")


## 
>>>fattyio.display_numbered_list(title="My list",items=["book","movie"])
#==========
#My list
#==========
#1)book
#2)movie
#----------

#return an index of a given value in an input list
>>>list_index=prompt_from_list_i(["book","movie"],default=0,autdef=0) 
#dont prompt if autodef is 1


#prompt for a value from a list. Adding a new item is ok if new_ok is set to 1
>>>chosen_item=prompt_from_list(["book","movie"],new_ok=1)


#Prompt from a range
>>>chosen_int=select_from_range(start,end,default=0)


# Get multiple values from a list
>>>subset=prompt_for_many_from_list(myarray,list_desc="My list description",new_ok=0)


fattydb
----------------
Functions and classes for dealing with database connections
Currently, this only works for mysql

## a simple mysql.connector.connect object
>>> dbconnection=make_db_connect(user,host,password,database,dbsys)

## delete everything from a table
>>> fattydb.delete_all_from_table(dbconnect,table)

## put date in proper format for mysql datetime
>>> input_datetime_param=mysql_datetimeformat(indatetime,offset_secs=60,return_obj=0)
## returns either an object or string for mysql input. For good comparisons, you can change the offset time

## or do the same but for strictly date
>>> input_dateformat(intime,offset_secs=60)


## Now the real useful stuff


A dbconnect class
>>> dbconnect=fattydb.DBConnect(user,host,password,database,dbsys,noconnect=0)
## if noconnect is 1, just return a value of whether the input params are ok

>>> dbconnect.close_cnx()

## backup the database
>>> dbconnect.backup_db(backup_dir)

## insert to multiple tables
## this requires specific format of input structure
>>> dbconnect.insert_to_multiple_tables(table_data,skip_check_tables=[])
## table_data=[
		  {"table": tablename,
		   "values": {"field1": value1, "field2":value2},
		   "unique_keys": [unique_key1,unique_key2], #will check these columns for the identical values
		   "foreign_keys": [ 
				       {"field": field_in_tablename,
					 "table": table_being_references},
					{"field": field2_in_tablename,	
					 "table": second_table_being_referenced
					]

>>> existing_id=dbconnect.check_unique_keys(table,unique_key_values,text_cols,primary_key="")
## unique_key_values={ field1: value1,field2:value2}
## text_columns can check different character sets or collations if one fails (it will only check binary though so maybe not so useful)


## execute select query		    
>>> return_cursor=dbconnect.select_query(tables,columns,where_values,text_cols=[])

## load data into tables 
## (This is currently very primitive)
>>> dbconnect.load_data_into_tables(filename,table,field_terminator,lineterminator,col_list)

## set_date_fieldname_re:
>>> is_a_datefield= dbconnect.is_datefield("goto_datetime")
## this relies on the datefield having a datetime indicator, or "nengappi" for those japanese fields



fattytime
--------

only a couple functions right now:
>>>is_inrange=fattytime.time_in_range(intime, starttime,endtime,offset=seconds_number)

>>>is_midnight=fattytime.is_midnight(indatetime) # yes if the time is 0,0,0
