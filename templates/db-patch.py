##
## This is used for loading the latest data into the topic-cutter mfs_mnt database
## it uses the configuration file my.conf in the folder specified by the TC_BASE environment variable
## call: python load-latest-data.py 
## 
#generic python modules
import csv
import fattyio
import pprint
import os
import glob
import sys,getopt
import datetime
import logging
#can be used regardless of system
from jjfattypy import fattylog,fattyconfig,fattydb

class MyScript():

    def set_all_patches(self,allpatches):
        self.all_patches=allpatches
        
    def set_patch_name(self,patchname):
        self.patch_name=patchname

    def set_force(self,force):
        self.force=force
    def set_user(self,user):
        if user == "":
            user=self.configs.config.get(self.config_section,"user_admin")
        self.user=user
    def set_password(self,pw):
        if pw == "":
            if not self.user==self.configs.config.get(self.config_section,"user_admin"):
                pw=fattyio.prompt_password("Enter password for user %s@%s"%(self.user,self.host))
            else:
                pw=self.configs.config.get(self.config_section,"password_admin")
        self.password=pw
    def set_db(self,db):
        if db == "":
            db=self.configs.config.get(self.config_section,"database") or self.configs.config.get(self.config_section,"dbase") or self.configs.config.get(self.config_section,"db")
        self.db=db
    def set_host(self,h):
        if h == "":
            h=self.configs.config.get(self.config_section,"host")        
        self.host=h
    def set_dbsys(self,dbsys):
        if dbsys=="":
            dbsys="mysql"
        self.dbsys=dbsys    

    def set_configs(self,config_filename="",config_section="main-db"):
        #This sets the config file for the script
        self.configs=fattyconfig.config_opts(config_filename)
        if config_section=="":
            config_section="main-db"
        self.config_section=config_section
        self.patch_dir=self.configs.config.get("dir","db_patches")        
         
    def set_log(self,verbose=0,logfilename=""):        
        #Sets the log file for the script
        #after setting this, you can use the standard logging lib
        #i.e. logging.info("This is a message")
        #If no log filename was given, create one using the script name and date time. This is safest, try not to add your own logfile
        tc_config.set_tc_log(self.configs,verbose,logfilename)

        logging.info("Script: %s"% __file__)
                
    def do_stuff(self):
        #here is where the main actions of the program take place
        #files=makedict.open_files(c        

        dbconnect=fattydb.DBConnect(self.user,self.host,self.password,self.db,self.dbsys,noconnect=1)
        input_patches=[]
        if self.all_patches:
            input_patches=glob.glob(os.path.join(self.patch_dir,"*.sql"))
        else:
            infile=os.path.join(self.patch_dir,self.patch_name+".sql")
            if os.path.isfile(infile):
                
                input_patches.append(infile)
            else:
                logging.error("Unable to find specified patch file %s.sql"%self.patch_name)
                sys.exit(2)
                
        successes=0
        for ifile in input_patches:
            this_success=dbconnect.load_db(ifile,force=self.force)
            successes+=this_success            
            
        if not successes==len(input_patches):
            logging.error("There was at least one error when processing the patches")
        else:
            logging.info("Database patches loaded successfully")

        return 0        

def main(argv):
    # default base dir for ami-angel combined system is based on environment variable
    #try getting args, or else print proper usage
    usage_str="""db-patch.py -v -h -s <host> -d <database> -u <user> -p <password> -c <config file> -e <config-section> -l <logfile> -a
    db-patch.py -v -h -s <host> -d <database> -u <user> -p <password> -c <config file> -e <config-section> -l <logfile> -n <patch-name>

    This script loads patches into the database. The default input database is into the [main-db] section of the database, but different sections can be specified via the -e option. 
    You MUST specify either the -a option OR the -n <patch-name> option.
    You may NOT specify both the -a and -n options
    The folder of the patches is the db_patches option in the [dir] section.

    -v: verbose
    -h: help
    -f: force: dont prompt for confirmation for loading data
    -c,--configfile: specify configuration file
    -l,--logfile: specify logfile
    -s,--host: specify host of the database
    -e: --configsection: specify config-section specifying the database details
    -d,--database: specify database to be backed up
    -u,--user: specify user (must have almost full rights to recreate the db)
    -p,--password: specify password    
    -a,--all-patches: install all patches in the patch directory 
    -n,--patch-name: specify the name of the patch, which is the same as the filename
    
    Configuration files:

    [dir]
    db_patches -- directory where the patches can be found

    [<some>-db] section:
    host
    database
    admin_user
    admin_password
    """
    verbose=0
    database=""
    user=""
    password=""
    host=""
    logfile=""
    myscript=MyScript()
    configfile=""
    force=0
    dbsys="mysql"
    configsection=""
    ifile=""
    allpatches=False
    patchname=""
    try:
        opts,args=getopt.getopt(argv,"hvfpan:s:e:d:u:c:l:",["patch-name=","host=","database=","configsection=","user=","password=","configfile=","logfile="])
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
        elif opt in ("-i", "--ifile"):
            ifile=arg
        elif opt in ("-u","--user"):
            user=arg
            fattyio.display("User: "+user)
        elif opt in ("-p","--password"):
            password=arg
            if password=="":
                password=fattyio.prompt_password()
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
        elif opt in ("-e","--configection"):
            configsecton=arg
        elif opt in ("-l","--logfile"):
            logfile=arg 
        elif opt in ("-a","--all-patches"):
            allpatches=True
        elif opt in ("-n","--patch-name"):
            patchname=arg

    if (not (allpatches or patchname != "")) or (allpatches and patchname != ""):
        fattyio.display(usage_str)
        sys.exit(2)


    myscript.set_configs(configfile,configsection)
        #now set the logfile using the logs config in the [dir] section of the config file
    myscript.set_log(verbose,logfile)
    
    myscript.set_all_patches(allpatches)
        
    myscript.set_patch_name(patchname)
    myscript.set_force(force)
#    myscript.set_infile(ifile)
    myscript.set_db(database)
    myscript.set_host(host)
    myscript.set_user(user)
    myscript.set_password(password)
    myscript.set_dbsys(dbsys)
        
    #your log is now set and you should be ready to go, to use logging throughout your     
    logging.info("I am still working")
    #    logging.info("Obtaining input and output directory for dictionary creation")

    myscript.do_stuff()
    

if __name__=="__main__":
    main(sys.argv[1:])
