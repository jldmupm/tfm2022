import time
import datetime

import pandas as pd

date_now = datetime.datetime.utcnow()

def unixTimeMillis(dt):
    '''Convert datetime to unix timestamp.'''
    return int(time.mktime(dt.timetuple()))

def unixToDatetime(unix):
    '''Convert unix timestamp to datetime.'''
    return pd.to_datetime(unix,unit='s')

def getMarks(start, end, Nth=100):
    '''Returns the marks for labeling. 
Every Nth value will be used.
    '''
    result = {}
    for i, date in enumerate(pd.date_range(start=start,end=end, freq='W')):
        if(i % Nth == 0):
            # Append value to dict
            result[unixTimeMillis(date)] = str(date.strftime('%Y-%m-%d'))

    return result
