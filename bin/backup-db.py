##
#generic python modules
import csv
import fattyio
import pprint
import os
import sys,getopt
import datetime
import logging
from configparser import NoOptionError
import shutil
#can be used regardless of system
from jjfattypy import fattylog,fattyconfig,fattydb

class MyScript():

    def set_force(self,force):
        self.force=force
    def set_user(self,user):
        if user == "":
            user=self.configs.config.get("backup-db","user")
        self.user=user
    def set_password(self,pw):
        if pw == "":
            pw=self.configs.config.get("backup-db","password")
        self.password=pw
    def set_db(self,db):
        if db == "":
            db=self.configs.config.get("backup-db","db")
        self.db=db
    def set_host(self,h):
        if h == "":
            h=self.configs.config.get("backup-db","host")        
        self.host=h
    def set_dbsys(self,dbsys):
        if dbsys=="":
            dbsys="mysql"
        self.dbsys=dbsys    
    def set_backup_dir(self,backup_dir):
        backup_dir_date=fattyio.make_date_folder_in(backup_dir)
        self.backup_dir=backup_dir_date
    def set_configs(self,config_filename=""):
        #This sets the config file for the script
        self.configs=fattyconfig.config_opts(config_filename)
        #self.configs=tc_config.config_opts(config_filename)
    def set_backup_only(self,backup_only):
        self.backup_only=backup_only
        
    def set_log(self,logdir,verbose=0,logfilename=""):        
        #Sets the log file for the script
        #after setting this, you can use the standard logging lib
        #i.e. logging.info("This is a message")
        #If no log filename was given, create one using the script name and date time. This is safest, try not to add your own logfile
        if logfilename=="":
            logfilename=os.path.basename(__file__)+"-"+datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")+".log"
        fulllog=""
        logdir=logdir.replace(r"\\","//")
        print("log dir:",logdir)
        #if no log directory was given, make one using the standard
        if logdir=="":
            logdir=fattylog.logdir()
        else:            
            date_logdir=fattyio.make_date_folder_in(logdir)
            fulllog=os.path.join(date_logdir,logfilename)
            #fulllog=date_logdir+"//"+logfilename
            
        #start the log
        
        fattylog.setlog(fulllog,verbose)
        #tell the user where the log file is
        #        fattyio.display("Log file: %s"%fulllog)        
        #insert name of script into log
        logging.info("Script: %s"% __file__)
        
    def get_backup_dets(self):
        #get db connect info for backup db
        backup_dets={}
        #set relevant section of config
        csec="test-db"
        try:            
            backup_dets["user"]=self.configs.config.get(csec,"user")
            backup_dets["password"]=self.configs.config.get(csec,"password")
            backup_dets["database"]=self.configs.config.get(csec,"database")
            backup_dets["host"]=self.configs.config.get(csec,"host")
            backup_dets["dbsys"]=self.configs.config.get(csec,"dbsys")
        except:
            logging.error("Unable to retrieve necessary config info for test db, exiting")
            sys.exit()
        return backup_dets
        
    def do_stuff(self):
        #here is where the main actions of the program take place
        #files=makedict.open_files(c

        dbconnect=fattydb.DBConnect(self.user,self.host,self.password,self.db,self.dbsys,noconnect=1)
        success=dbconnect.backup_db(self.backup_dir)        
        if success:
            logging.info("Successfully backed up db into file %s"%dbconnect.get_backup_file())
            fattyio.display("Successfully backed up db %s into file %s"%(self.db,dbconnect.get_backup_file()))
            fattyio.display("Attempting to load database into test db")
            #if it was successful, try reloding the db into the test db
            #if it is not a backup only mode, rebuild the database as a test database
            self.create_second_backup(dbconnect.get_backup_file())
            if not self.backup_only:
                print("Backing up")
                self.create_test_db(dbconnect.get_backup_file())              
        else:
            logging.error("There was at least one error when processing the database installation")

        return 0        
    def create_second_backup(self,backup_file):
        try:
            if not fattyio.map_network_drive(
                self.configs.config.get("backup_2","backup_2_base_drive"),
                self.configs.config.get("backup_2","backup_2_base")
            ):
                logging.warning("Not creating backup because no network drive is available")
                return False
            if os.path.exists(self.configs.config.get("backup_2","backup_2_dir")):            
            
                logging.info("Second backup directroy %s exists, copying the backup file there into %s"%(self.configs.config.get("backup_2","backup_2_dir"),self.configs.config.get("backup_2","backup_2_file")))
                shutil.copy(backup_file,self.configs.config.get("backup_2","backup_2_file"))

                if os.path.isfile(self.configs.config.get("backup_2","backup_2_file")):
                    logging.info("Second backup file created")
                else:
                    logging.warning("Unable to find second backup file")
            else:
                logging.info("Unable to find the backup folder %s"%self.configs.config.get("backup_2","backup_2_dir"))
            fattyio.rm_network_drive(self.configs.config.get("backup_2","backup_2_base_drive"))
        except NoOptionError:
            logging.warning("Required configuration options in backup_2 secion not set")
        
        
        
        
    def create_test_db(self,backup_file):
        bdb_dets=self.get_backup_dets()
        fattyio.display("Trying to build test database %s from the backup file"%bdb_dets["database"])
        backup_dbconnect=fattydb.DBConnect(bdb_dets["user"],bdb_dets["host"],bdb_dets["password"],bdb_dets["database"],bdb_dets["dbsys"],noconnect=1)
        #now load the backed up data into the test db
        success_reload=backup_dbconnect.load_db(fullpath=backup_file,force=self.force)
        logging.info("Finished attempting to load database")
        if success_reload:
            logging.info("Successfully loaded test database %s"%bdb_dets["database"])
            fattyio.display("Successfully built database")
        else:
            logging.error("Errors occurred while loading test database %s, check log for details" %bdb_dets["database"])                  
        return success_reload


def main(argv):
    # default base dir for ami-angel combined system is based on environment variable
    #try getting args, or else print proper usage
    usage_str="""backup-db.py -v -h -s <host> -d <database> -u <user> -p <password> -c <config file> -l <logfile> 
    -v: verbose
    -h: help
    -f: force: dont prompt for confirmation for creating new test db
    -b: backup-only, i.e. don't attempt to create a new test database
    -c,--configfile: specify configuration file
    -l,--logfile: specify logfile
    -s,--host: specify host]
    -d,--database: specify database to be backed up
    -u,--user: specify user
    -p,--password: specify password    

    This file makes a backup file of the specified database, by default set to the database in the [backup-database] section of the configuration file
    
    Also, by default this will load the backup into the database specified by the [test-section] of the database    
    
    Configuration files:
    This script is best used with a configuration file which specifies the database details. 
    All databases must be created before executing the script.
    Please only give minimum privileges to the users involved in these processes.
    Please ensure your configuration file is only readable by the user, as the password is stored in plaintext.
    If you are aware of a better way of storing the password, please inform Colin.
    """
    verbose=0
    database=""
    user=""
    password=""
    host=""
    logfile=""
    myscript=MyScript()
    configfile=""
    mode="overwrite"
    backup_base=""
    backup_only=0 # no test-db
    force=0
    dbsys="mysql"
    try:
        opts,args=getopt.getopt(argv,"hvfbs:d:u:p:c:l:",["host=","database=","user=","password=","configfile=","logfile="])
    except getopt.GetoptError:
        fattyio.display(usage_str)
        sys.exit(2)

    for opt,arg in opts:
        if opt== "-h":
            fattyio.display(usage_str)
            sys.exit()
        elif opt == "-v":
            verbose=1
        elif opt=="-f":
            force=1
        elif opt=="-b":
            backup_only=1
        
        elif opt in ("-u","--user"):
            user=arg
            fattyio.display("User: "+user)
        elif opt in ("-p","--password"):
            password=arg
            if password=="":
                fattyio.display("No password giving, exiting")
            else:
                fattyio.display("Password set")
        elif opt in ("-s","--host"):
            host=arg
            fattyio.display("Host: "+host)
        elif opt in ("-d","--database"):
            database=arg
            fattyio.display("Database: "+ database)
        elif opt in ("-c","--configfile"):
            configfile=arg            
        elif opt in ("-l","--logfile"):
            logfile=arg 

    myscript.set_configs(configfile)
    myscript.set_log(myscript.configs.config.get("dir","logs"),verbose,logfile)
    myscript.set_force(force)
    myscript.set_user(user)
    myscript.set_password(password)
    myscript.set_db(database)
    myscript.set_host(host)
    myscript.set_backup_dir(myscript.configs.config.get("dir","backup_db"))
    myscript.set_backup_only(backup_only)
    myscript.set_dbsys(dbsys)
        
    #your log is now set and you should be ready to go, to use logging throughout your     
    logging.info("I am still working")
    #    logging.info("Obtaining input and output directory for dictionary creation")

    myscript.do_stuff()
    

if __name__=="__main__":
    main(sys.argv[1:])
