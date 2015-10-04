import datetime
import logging
from . import kanio
from dateutil import parser

def time_in_range(intime,starttime,endtime,offset=datetime.timedelta(seconds=60)):
    st=None
    et=None
    t=None
    
    if type(starttime) is str:
        st=make_date_obj(starttime)
    else:
        st=starttime

    if type(endtime) is str:
        et=make_time_obj(endtime)
    else:
        et=starttime

    if type(intime) is str:
        t=make_time_obj(intime)
    else:
        t=intime

    if not(t and st and et):
        return 0
        
    if st.time()==datetime.time(0,0,0):
        return 0
    else:
        time_diff=st-et    
        adjusted_start=st-offset
        adjusted_end=et-offset
        in_range = adjusted_start <= t <= adjusted_end

        return in_range

def is_midnight(indatetime):
    logging.debug("Converting in-time %s to object"%indatetime)
    datetime_obj=parser.parse(indatetime)
    time=datetime_obj.time()
    
    midnight=datetime.time(0,0)
    
    return time==midnight


def make_time_obj(time_str,format="%Y/%m/%d %H:%M"):
#    timeobj=dateutil.parser.parse(time_str)
    backup_formats=["%Y-%m-%d %H:%M"]
    timeobj=None
    try:
        timeobj=datetime.datetime.strptime(time_str,format)
    except ValueError:
        for f in backup_formats:
            try:
                timeobj=datetime.datetime.strptime(time_str,f)
            except ValueError:
                pass
    return timeobj
