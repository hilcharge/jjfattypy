"""Various functions for performing normal input and output,
 file input and output,
finding files in directories, and parsing data"""

import sys
import pprint
import glob
import logging
import os.path
import datetime
import os
import re
import csv
from subprocess import Popen,PIPE
import shlex
import dateutil.parser
import zipfile
import getpass
import shutil
import string
import random
import traceback

def is_in_parentheses(inword):
    """returns True if inword is consists of one big parenthesized inner block
    
    e.g. inword("(I am a block)")==True
    inword("(I am)(Two Blocks)")==False
    
    """
    if not re.match(r"\(.*\)$",inword):
        return False
    else:
        inner=first_parenthesized(inword)
        if "({})".format(inner)==inword:
            return True
        else:
            return False
        
def first_parenthesized(inword):
    """return the first parenthesized item, or None if there is no closing parentheses"""
    
    s=[]
    inside=""         
    started=False
    for c in inword:        
        if c=="(" and not started:                
            s.append(c)
            started=True
        elif c=="(":
            s.append(c)
            inside+=c
        elif c==")":
            try:
                s.pop()
            except:
                logging.error("Unbalanced parentheses")                
                return None
            if len(s)==0:
                return inside
            else:
                inside+=c
        else:
            inside+=c
            
    if len(s)>0:
        logging.error("Unbalanced parentheses")

def regex_to_fullwidth(regex,s_format=False):
    """convert a regular expression to using only fullwidth characters"""
    ignore_chars=r"([{|+?&.,^<-=:!\/*}]) " #characters to ignore when converting to full width
    return_regex=jctconv.h2z(regex,ascii=True,ignore=ignore_chars)
    if s_format:
        p=re.compile(r"\)ｓ(\d+\,)",re.UNICODE)
        for m in p.finditer(return_regex):            
            return_regex=return_regex.replace(m.group(0),")s%s"%m.group(1))             
            
    return return_regex

def clean_regex(inregex,external_parentheses=0):    

    outregex=rm_qmarks(inregex)
    outregex=rm_extra_regex_buffers(outregex)
    outregex=rm_empty_parentheses(outregex)
    outregex=remove_extra_external_parentheses(outregex,external_parentheses)
    return outregex

def rm_qmarks(inregex):
    #    pat=r'\\\?+'
    #    outregex=re.sub(pat,"\?",inregex)
    outregex=re.sub(r'\?+','?',inregex)
    return outregex

def rm_extra_regex_buffers(inregex):
    """remove cases where a .{x,y} is immediately followed by another .{a,b}
    """
    pat=r'(\.\{\d+\,\d+\}\??)+'
    #search_pat=re.compile(r'(\.\{\d+\,\d+\}\??)+')

    replace_pat=r'^(\.\{\d+\,\d+\}\??)'
    outregex=inregex
    for m in re.finditer(pat,inregex):
        replace_target=m.group(0)
        replace_target_pat=re.escape(replace_target)        
        first_buffer=re.match(replace_pat,replace_target).group(0)
        outregex=re.sub(replace_target_pat,first_buffer,outregex)

    return outregex

def remove_extra_external_parentheses(string,max_remaining=0):
    """Remove all unnecesary parenetheses from the OUTSIDE of the string.
    Leave `max_remaining` number of external parenetheses on the outside
    """
    count=0
    while True:
        #get the first item in parentheses from within the given string
        parenthetic=next_parenthetic(string)
        #print("Parenthetic: ", parenthetic)
        #if the item in parentheses, parenthetic, wrapped in parenetheses, is the same as string, 
        #then replace string with parenthetic, and try running it again
        if "(%s)"%parenthetic==string:            
            string=string.replace(string,parenthetic)
            count+=1
        else:
            #if the parenthetic is different, then the game is over
            break
   
    for i in range(0,max_remaining):
        if i >= count:
            break
        else:
            string="(%s)"%string
    return string

def next_parenthetic(string):
    s=[]
    parent=string
    ps=""
    in_p=False
    for char in string:
        if char=="(":
            s.append(char)
            if not in_p:
                in_p=True            
                continue
        elif char==")":
            s.pop()
            if len(s)==0:
                return ps
        if in_p:
            ps+=char

def rm_empty_parentheses(intext):
    """remove empty parentheses"""
    emp="()"    
    if emp in intext:
        intext=intext.replace(emp,"")
        return rm_empty_parentheses(intext)
    else:
        return intext

def parenthetic_contents(string):
    """ generate parenthesized contents in string as pairs (level, contents)"""
    """ list(parenthetic_contents('(a(b(c)(d)e)(f)g)')
    [(2,'c'),(2,'d'),(1,'b(c)(d)e'),(1,'f'),(0,'a(b(c)(d)e)(f)g']"""

    stack=[]
    for i,c in enumerate(string):
        if c=="(":
            stack.append(i)
        elif c==')' and stack:
            start=stack.pop()
            #print(string[start+1:i])
            yield (len(stack),string[start+1:i])


def copytree(src,dst,symlinks=False,ignore=None):
    """Copy a directory and all its subdirectories"""

    for item in os.listdir(src):        
        s=os.path.normpath(os.path.join(src,item))
        d=os.path.normpath(os.path.join(dst,item))
        if os.path.isdir(s):
            copytree(s,d,symlinks,ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s,d)
                print("Copying")


def random_string(size=20,chars=string.ascii_uppercase+string.digits):
    """return a random string of <size> length"""
    return ''.join(random.choice(chars) for _ in range(size))

def map_network_drive(drive,target):
    """map a network drive <drive> to the target folder <target>"""
    if os.path.exists(drive):
        logging.error("Cannot map an existing drive %s"%drive)        
        return True
    os.system(r"NET USE %s %s"%(drive,target))
    if os.path.exists(drive):
        logging.info("drive found")
        return True
    else:
        logging.info("Unable to map drive")
        return False

def replace_string_in_list(mylist,orig,new):
    """replace a string in a list, which may also be a list of lists"""
    for i,item in enumerate(mylist):
        if type(item)==list:
            return replace_string_in_list(item,orig,new)
        elif type(item)==str:

            mylist[i]=item.replace(orig,new)
            
    return mylist

def rm_network_drive(drive):
    """remove a network drive of letter <drive>""" 
    os.system(r"NET USE %s /DELETE"%drive)
    logging.info("Removed network drive %s"%drive)

def prompt_password(prompt=""):    
    """prompt for a password. Better to just use getpass"""
    if prompt=="":
        return getpass.getpass()
    else:
        return getpass.getpass(prompt=prompt)

def zip_a_dir(directory,outfilename="",outdir=""):
    """zip directory
    by default, output it in the parent folder of the directory
    i.e. zip_a_dir("C:\\myfolder\\target")
    will make C:\\myfolder\\target.zip
    the path of the new zipfile is returned"""

    if not os.path.isdir(directory):
        logging.error("Tried to use zip_a_dir on something other than directory (%s)"%str(directory))
    if outfilename=="":
        outfilename=os.path.basename(directory)+".zip"
    if not os.path.splitext(outfilename)[1]==".zip":
        outfilename=outfilename+".zip"    
    if outdir=="":
        outdir=os.path.dirname(directory)
    fulloutfilename=os.path.join(outdir,outfilename)
    logging.info("Creating zipfile: %s based on directory %s"%(fulloutfilename,directory))
    with zipfile.ZipFile(fulloutfilename,"w") as ziph:
        for root,dirs,files in os.walk(directory):
            for fn in files:
                ziph.write(os.path.join(root,fn),os.path.relpath(os.path.join(root,fn),os.path.join(directory,"..")))

    return fulloutfilename


def reps_int(string):
    """True is string is an integer"""
    try:
        int(string)
        return True
    except ValueError:
        return False

def dirint(mydir):
    """return an integer value fo the given directory name, useful for folders based on dates"""
    return int(os.path.basename(mydir))

def newest_file_in(dirname,filetype="",exclude_files=[]):
    """return the newest file in <dirname> which is not a directory"""
    filetypes_msg=""
    if filetype:
        filetypes_msg="(Filetype: %s)"%filetype
    else:
        filetypes_msg="(All filetypes)"
    display("Searching for newewst file in %s %s"%(dirname,filetypes_msg))
    if exclude_files:
        display("(Not including the following: %s"%str([os.path.basename(f) for f in exclude_files]))    

    files=[os.path.normpath(myfile) for myfile in files_in_dir(dirname) if os.path.isfile(myfile) and not os.path.normpath(myfile) in [os.path.normpath(x) for x in exclude_files]]
    
    if filetype !="":
        files=[f for f in files if re.match(r'\.%s$'%filetype,f)]
    if not len(files):
        logging.error("No files found in the given directory %s"%dirname)
        return 0
    else:
        sorted_files=sorted(files,key=os.path.getmtime)
        #print("Hello")
        return sorted_files[-1]        

def find_newest_date_dir(base_dir):
    """return the path of the newest directory, based on its name, i.e. 2015 is newer than 2014 even if 2014 was modified later"""
    #find the most recent date dir within the given base_dir
    #
    dirs=[mydir for mydir in glob.glob(os.path.join(base_dir,"*")) if os.path.isdir(mydir) and reps_int(os.path.basename(mydir))]
    if len(dirs)==0:
        return base_dir
    else: 
        sorted_dirs=sorted(dirs,key=dirint)
        return find_newest_date_dir(sorted_dirs[-1])

def wait(text="Press enter key to continue...",msg="Ctrl-C to end script"):
    """wait until the user does something"""
    anykey=fattyprompt(text,default=msg)
    return 0

def make_time_obj(time_str,format="%Y/%m/%d %H:%M"):
    """make a time object from a string"""
    timeobj=dateutil.parser.parse(time_str)

    return timeobj

def delete_files_from_dir(dirname,filetypes=[],force=0,backup=1,short_output=False):
    """delete all files from a directory, having specified filetypes"""
    if not os.path.isdir(dirname):
        return 0
        
    files=[]
    if len(filetypes)==0:
        files.extend(os.listdir(dirname))
    else:
        os.chdir(dirname)
        for filetype in filetypes:            
            files.extend(glob.glob("*.%s"%filetype))
            
    if not force:
        force=query_yes_no("Are you sure want to delete all the following files:%s"%str(files),default="no")
    
    if force:
        explain="Removing files in %s"%dirname
        if short_output:
            if len(filetypes):
                explain+=" (File types: %s) "%",".join(filetypes)
            else:
                explain+=" (All file types) "
        display(explain)
        for f in files:
            if not short_output:
                display("Removing %s"%f)
            os.remove(f)
        return 1
    else:
        logging.info("NOT deleting files from directory %s"%dirname)
        return 0
        
def convert_file_to(infilename,delimiter="\t",encoding="utf8"):
    
    (basename,ext)=os.path.splitext(infilename)
    
    newfile=basename+"-%s"%encoding+".%s"%ext
    
    ifh=open(infilename)
    
    ofh=open(newfile,"w",encoding=encoding)

    for line in ifh:
        ofh.write(row)

    return newfn
    

def fatty_csv_dets(filename,delimiters=["\t",",","^I",";"],encodings=["sjis","utf8","utf16","cp932"],close=False):
    """return various details and data based on a given filename, this is a brute force approach when encodings are an issue, make a file with each of them"""
    ifh_dets={}
    delimter=delimiters[0]
    header=[]
    for enc in encodings:                
        try:
            ifh_dets["fh"]=open(filename,encoding=enc)
            ifh_dets["csv"]=csv.reader(ifh_dets["fh"])          
            ifh_dets["filename"]=filename
            header=next(ifh_dets["csv"])
            ifh_dets["encoding"]=enc
            if len(header)==1:
                logging.warning("Header length of one, trying different delimiters")
                for dl in delimiters:
                    th=list(header)[0].split(dl)
                    if len(th)>1:
                        ifh_dets["delimiter"]=dl                        
                        ifh_dets["fh"].seek(0)
                        ifh_dets["csv"]=csv.reader(ifh_dets["fh"],delimiter=dl)
                        break
            ifh_dets["encoding"]=enc
            logging.debug("Header: %s"%str(header))
                    
        except UnicodeDecodeError:
            logging.info("Unable to use encoding %s, trying next"%enc)
        else:
            ifh_dets["encoding"]=enc
            logging.info("Using %s encoding"%enc)
                            
            break
    if close:
        ifh_dets["fh"].close()
    return ifh_dets

def date_filename(base="",date_form="%Y-%m-%d-%H%M%S",ext="csv",datetimeobj=None):
    """return a filename with the datetime"""
    datefilename=""
    actual_ext=""
    if not base=="":
        try:             
            requested_ext=os.path.splitext(base)[1][1:]
            base=os.path.splitext(base)[0]            
        except IndexError:
            logging.info("Using default output filetype")
            actual_ext=ext
        else:
            actual_ext=requested_ext
    if actual_ext=="":
        actual_ext=ext
    if not datetimeobj:
        if not base =="":
            datefilename=base+"-"
        datefilename+=datetime.datetime.now().strftime(date_form)+"."+actual_ext
    else:
        datefilename=base+"-"+datetimeobj.strftime(date_form)+"."+actual_ext
        
    return datefilename

def open_reader_csv(ifile):
    """open a csv reader object, but try various encodings"""

    ifh=open(ifile)
    icsv=csv.reader(ifh)
    #try default encoding, but if it fails go to unicode
    try:
        row=next(icsv)                            
    except UnicodeDecodeError:
        logging.info("Default decoding did not work when reading input file, attemping unicode")
        for enc in ["utf8","utf16","sjis","cp932"]:
            ifh.close()
            ifh=open(ifile,encoding=enc)
            icsv=csv.reader(ifh)
            try:                    
                row=next(icsv)
            except UnicodeDecodeError:
                logging.info("Input file does not seem to have %s encoding"%enc) 
                continue
            else:
                logging.info("Input file does not seem to have %s encoding"%enc) 
            break
    ifh.seek(0)
    return (icsv,ifh)

def combine_files(files,ofilename,separator,outputencodings=["utf8","sjis","utf16"],return_enc="utf8"):
    """make an output file, which is a combination of the <files> list, in each of the specified encodings"""
    filecount=0
    ofhs=[]
    ocsvs=[]
    ofile_base,ext=os.path.splitext(ofilename)
    ofns=[]
    rfn=""
    file_dets=[]
    for enc in outputencodings:
        ofn="%s_%s%s"%(ofile_base,enc,ext)
        ofns.append(ofn)
        ofh=open(ofn,"w",encoding=enc)
        ofhs.append(ofh)
        ocsvs.append(csv.writer(ofh,lineterminator="\n",delimiter=separator))        
        file_dets.append({"fh":ofh,"enc":enc})
        if enc==return_enc:
            rfn=ofn
    dame_enc=[]
    total_rows=0
    rownum=0
    for ifile in files:
        if not os.path.isfile(ifile):
            logging.info("Given input file for combination: %s is not a file, skipping"%ifile)
            continue
        indir=os.path.dirname(os.path.realpath(ifile))
        os.chdir(indir)
        rownum=0
        icsv,ifh=open_reader_csv(ifile)
        
        for row in icsv:
            #if its the first row of the non-first file, skip it
            if rownum==0 and filecount!=0:
                rownum+=1
                continue
                #otherwise write the row
            if not len(row)==0:
                #write a row in each output file                
                for i,ocsv in enumerate(ocsvs):
                    #skip if the encoding doesnt work
                    if file_dets[i]["enc"] in dame_enc:
                        continue
                    #try to write the row
                    try:
                        ocsv.writerow(row)                        
                    except UnicodeEncodeError:
                        logging.error("Unable to use the encoding %s to write this row, assuming all rows in the file should not be written to this encoding"%file_dets[i]["enc"])
                        dame_enc.append(file_dets[i]["enc"])                     
                rownum+=1
            total_rows+=rownum
        filecount +=1
        logging.info("Finished file %s"%ifile)            
        ifh.close()
    logging.info("Finished all files, total of %d input lines wrote to outputfiles %s" % (rownum,str(ofns)))
    if len(dame_enc)>0:
        logging.info("The following encodings were not able to be fully written in the combination file: %s"%str(dame_enc))
    for ofh in ofhs:
        ofh.close()                                    
    return rfn

def make_date_folder_in(base_dir,zero_padded=True):
    """make a date folder in <base_dir>, return the full path"""
    now=datetime.datetime.now()
    #split base 
    #basedirs=re.split(r'\\',base_dir)

    #base_dir=os.path.join("/",*basedirs)
    #base_dir="/".join(basedirs)
    base_dir=base_dir.replace(r"\\","//")
    if not os.path.exists(base_dir):
        logging.critical("Given directory %s not a directory, exiting"%base_dir)
        sys.exit() 
        #this fails for unknonw reasons
        #os.path.join should work, but it doesnt, so sdly this is using slashes. This must be avoided in the future
    year_dir=""
    month_dir=""
    date_dir=""
    if zero_padded:
        year_dir=os.path.join(base_dir,now.strftime("%Y"))
        month_dir=os.path.join(year_dir,now.strftime("%m"))
        date_dir=os.path.join(month_dir,now.strftime("%d"))
    else:        
        year_dir=os.path.join(base_dir,str(now.year))        
        month_dir=os.path.join(year_dir,str(now.month))
        date_dir=os.path.join(month_dir,str(now.day))

    if not os.path.exists(year_dir):        
        os.makedirs(year_dir)
    if not os.path.exists(month_dir):
        os.makedirs(month_dir)
    if not os.path.exists(date_dir):
        os.makedirs(date_dir)
        logging.info("Created folder: %s"% date_dir)
    else:
        logging.info("Found folder: %s"% date_dir)

    return date_dir

def parse_byte_strings(*args):
    """replace byte strings with proper strings"""
    try:
        return [str("\n".join(arg.decode("utf8").split("\r\n"))) for arg in args]
    #    return output_strs
    except UnicodeDecodeError:
        for enc in ["sjis","cp932","utf16"]:
            try:
                return  [str("\n".join(arg.decode("sjis").split("\r\n"))) for arg in args]
            except UnicodeDecodeError:
                logging.info("Failed to decode using %s"%enc)
    return args
    
def files_in_dir(direc,nocheck=1,file_types=[],exclude_files=[]):    
    """return a list of all files in the given directory
    replace any backslashes with forward slashes
    """
    
    base_str=direc
    glob_str=""
    files=[]
    if not os.path.isdir(direc):
        logging.debug("Given path %s is not a directory"%direc)
        return []
    if len(file_types)==0:
        glob_str=os.path.join(base_str,"*")    
        files.extend([f for f in glob.glob(glob_str) if not (f in exclude_files)])
    else:
        #for each file type, extend glob
        for thistype in file_types:
            globstr=os.path.join(base_str,"*.%s"%thistype)
            logging.debug("Glob str: %s"%globstr)
            files.extend([f for f in glob.glob(globstr) if not (f in exclude_files)])
            logging.debug("Available files: %s","/n"+"\n".join(files))
            logging.info("Found %i files"%len(files))                          
    if len(files) == 0:
        logging.debug("Unable to find any files in given directory")

#    display("Dir:"+direc)
    if not nocheck:
        while not query_yes_no("Is the following list of files ok?\n"+", ".join(files),default="y"):
            files=glob(fattyprompt("enter a new directory:",default=direc)+"//*")
    
    files = [ afile.replace("////","//") for afile in files]
        
    return files

def excel_to_tsv(excel_files):
    """transform each file in <excel_files> to a tsv file, return the list of tsv files"""
    vbs_base='cscript.exe "%s"'%(os.path.join(os.getenv("HOME_BIN"),"Excel2tsv.vbs"))
    if len(excel_files)==0:
        display("No input excel files for conversion")
        logging.warning("No input files excel files given for tsv conversion")
        return 0
    for thisfile in excel_files:
        #skip if not a real file
        if not os.path.isfile(thisfile):
            logging.info("Given input file for combination: %s is not a file, skipping"%thisfile)
            continue
        else:
            thisdir=os.path.dirname(os.path.realpath(thisfile))
            os.chdir(thisdir)
        base_file=os.path.basename(thisfile)
        vbs_call='%s "%s"'%(vbs_base,thisfile)
        logging.info("Executing visual basic call")
        logging.debug(vbs_call)
        output,error=Popen(shlex.split(vbs_call),stdout=PIPE,stderr=PIPE).communicate()
        logging.info("Output: "+str(output))
        if error:
            logging.info("Error: "+str(error))
        else:
            logging.info("Converted the excel file to a tsv")

    inputdir=os.path.dirname(excel_files[0])
    tsv_files=glob.glob(os.path.join(inputdir,"*.txt",))        

    return tsv_files

def display(*args):
    """print each arg"""
    for a in args:
        print(a)
        
    return None

def pdisplay(*args):
    """pretty print the variable"""
    for a in args:
        pprint.pprint(a)
    return None
    
def fattyprompt(text,default=""):
    """prompt for input, with default value"""
    return input(text+" [%s]> " % default) or default
    
def intprompt(text,default_int=0):
    """return an integer from the user"""
    while 1:
        userin=fattyprompt(text) or default_int
        try:
            returnint=int(userin)
        except ValueError:
            display("Enter an integer!")
        else:
            return returnint
    
def header(text,string=False):
    """print a header formatted string"""
    ostring="***********************\n"
    ostring+=text
    ostring+="\n***********************\n"

    if string:
        return ostring
    else:
        print(ostring)
    
def min_header(text,string=False):
    """print small header"""
    ret_string="***** %s ******"% text
    if string:
        return ret_string
    else:
        print(ret_string)

def prompt_file(def_folder,def_file="",nocheck=0,exclude_files=[],file_title=""):
    """prompt for a file in the given directory. Can be forced to choose default if nocheck is set"""
    full_filename=os.path.join(def_folder,def_file)
    if nocheck:
        if os.path.isfile(def_file):
            return def_file
        else:
            return full_filename

    if not os.path.isfile(full_filename):
        full_filename=prompt_from_list(files_in_dir(def_folder,exclude_files=exclude_files),new_ok=0,title=file_title)

    q_prompt="Is %s OK as a file?"
    if file_title:
        q_prompt+="(%s)"%file_title    
        
    if query_yes_no("Is %s OK as a file?" % full_filename):
        return full_filename        
    else:
        done=0
        while not done:
            full_filename=os.path.join(def_folder,input("Enter the file relative to the default folder: %s" % def_folder))
            done= query_yes_no("is %s OK as a file?" %full_filename)
        return full_filename


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
                             
                             
def display_numbered_list(title="",items=[]):
    """display  a numbered list for array"""
    if title != "":
        print('========')
        print(title+':')
        print('========')
    else:
        print('--------------------------------')
    for i,item in enumerate(items):
        print(i+1,')',item)
    print('--------------------------------')
    return 0
    
def prompt_from_list_i(alist, title="value", default_i=0,autodef=0):
    """return the index of a selected in the alist][
    if autodef is 1, dont actually prompt the user if theres a default"""
    if not autodef or not (0 <= default_i < len(alist)):
        display_numbered_list("Select a choice for a %s"% title,alist)
        choice=select_from_range(1,len(alist),default=default_i)-1
        return choice
    else:
        return default_i
        
def prompt_from_list(mylist,default="",new_ok=1,autodef=0,title=""):
    """return the value from a list
    display_numbered_list("",categories)
    if autodef is 1, dont actually prompt the user if theres a default"""
    if default in mylist:
        default_int=mylist.index(default)
        return mylist[prompt_from_list_i(mylist,title,default_int,autodef)]
    elif (default != "" and not (default in mylist) and new_ok):
        mylist.append(default)
        return mylist[prompt_from_list_i(mylist,title,len(mylist)-1,autodef)]
    else:
        display("Unable to choose default (%s), please choose different value" % default)
        return mylist[prompt_from_list_i(mylist,title)]
    
        
def select_from_range(start,end,default=0):
    """return a number that is within the range (inclusive) of start and range"""
    while 1:
        userin=intprompt("Choose your value [%s]" % str(default+1),default_int=default+1)
        if start <= userin <= end:
            return userin

def prompt_for_many_from_list(myarray,list_desc="",new_ok=0):
    """return an array which is a subset of the given input array"""
    header("Choose a subset of the following %s:"%list_desc)
    orig=list(myarray)
    finished=0
    return_list=[]
    # if the length of input array is 0
    if len(myarray)==0:
        return return_list
    #until the user confirms he is done, prompt for new values
    #at least one value must be returned
    #

    while not finished:
        desired_item=prompt_from_list(myarray,myarray,new_ok)
        return_list.append(desired_item)
        myarray.remove(desired_item)
        display("Current list: "+", ".join(return_list))
        # if length of input array has been reduced to 0, its time to wrap things up
        if len(myarray)==0:
            finished=query_yes_no("Is the above list acceptable (no more values to choose from")
            #if not finished, revert to original list
            if not finished:
                display("OK, reverting to original array")
                myarray=list(orig)
        else:            
            finished=query_yes_no("Is the list above acceptable? (You can choose more items)")
        
    
    return return_list

def fatty_dircheck(direc,default):
    """return a directory that is either the given directory, or the default directory if the given directory doesnt exist"""
    if direc=="":
        direc=default
        logging.info("No output directory specified, assuming configured value %s"%direc)        
    elif not os.path.isdir(outputdir):
        direc=default
        logging.info("Specified directory does not seem to exist, assuming default value %s"%default)

    return direc
        
def clean_directory(path):
    """DONT USE THIS. replace bad backslashes
    this is bad form Dont use it"""
    newpath=path.replace("\\","//")
    newpath=newpath.replace("////","//")
    return newpath
