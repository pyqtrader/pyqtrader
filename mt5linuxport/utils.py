import os, sys, subprocess, psutil,time
from datetime import datetime
from pytz import timezone, UnknownTimeZoneError

import numpy as np

import cfg
from uitools import simple_message_box

from _debugger import *

# This wrapper class intercepts method calls, 
# checks if the method returns a numpy array with a "time" column,
# and if so, performs the timeshift operation before returning the array.
# timeshift- standard time shift between UTC and market times in hours
class MT5TimeshiftWrapper:
	def __init__(self, original_object, timeshift:int=None):
		self.original_object = original_object
		if timeshift is None:
			# EET - normal standard market timezone
			self.timeshift=MT5TimeshiftWrapper.get_timezone_shift("EET","UTC")*3600
		else:
			self.timeshift = timeshift*3600

	def __getattr__(self, attr):
		original_attr = getattr(self.original_object, attr)
		if callable(original_attr):
			def wrapped(*args, **kwargs):
				result = original_attr(*args, **kwargs)
				if isinstance(result, np.ndarray) and 'time' in result.dtype.names:
					result['time'] += self.timeshift
				return result
			return wrapped
		else:
			return original_attr

	@staticmethod
	def get_timezone_shift(timezone_1, timezone_2):
		"""
		This function calculates the time difference between two timezones in hours.

		Args:
			timezone_1 (str): The first timezone name (e.g., 'US/Eastern').
			timezone_2 (str): The second timezone name (e.g., 'Asia/Tokyo').

		Returns:
			float: The time difference between the two timezones in hours (positive or negative).

		Raises:
			ValueError: If any of the provided timezones are invalid.
		"""
		try:
			tz_obj_1 = timezone(timezone_1)
			tz_obj_2 = timezone(timezone_2)
		except UnknownTimeZoneError:
			raise ValueError("Invalid timezone provided")

		# Get the UTC offset for each timezone in seconds
		utc_offset_1 = tz_obj_1.utcoffset(datetime.now()).total_seconds() / 3600
		utc_offset_2 = tz_obj_2.utcoffset(datetime.now()).total_seconds() / 3600

		# Calculate the time difference in hours
		time_diff = utc_offset_2 - utc_offset_1
		return int(time_diff)

	# Overrides copy_rates_from_pos(), copy_rates_from(), and copy_rates_from_range()
	# from MetaTrader5() object. View MetaTrader documentation for description of the arguments. 
	# The original fuctions can also be used directly
	def load_rates(self, symbol="EURUSD", timeframe=3600, 
					date_from=None, date_to=None,
					count=None, start_pos=None):

		assert sum(x is not None for x in [date_from, date_to, count, start_pos])==2,\
		"Exactly two of date_from, date_to, count, and start_pos must be provided"

		assert not (date_from and start_pos),\
		"date_from requires count or date_to as the second argument"

		start_pos = start_pos if start_pos is not None else 0

		# Logic for date_from requests
		if date_from:
			date_to = date_to if date_to is not None else int(time.time())
			period = 1 + (date_to - date_from) // timeframe
			count=min(period, count) if count else period

			start_pos=period-count if period-count>0 else 0

		# Timeframe in mt5 format
		tf=mt5_timeframe(self,cfg.tf_to_label(timeframe))

		result=None
		check=None
		error_message="No errors identified"
		for i in range(7):
			# call copy_rates_from_pos() with the calculated start_pos and count
			result = self.original_object.copy_rates_from_pos(symbol, tf, start_pos, count)

			# Ensure result is valid i.e. a numpy array
			if not isinstance(result, np.ndarray):
				continue

			result['time'] += self.timeshift

			check=self.validate_result(result,timeframe,date_from,start_pos)
			if check:
				break

			time.sleep(2)
		
		if check is False:
			result=None
			error_message="mt5 terminal timeseries data is obsolete"
		elif result is None:
			error_message=f"mt5 object error {self.original_object.last_error()}"

		return result, error_message

	# Checks whether mt5 has up-to-date timeseries data
	def validate_result(self, result, timeframe, date_from, start_pos):

		if date_from:
			check= (0<=result['time'][0]-date_from<timeframe)
		else:
			current_time=int(time.time())
			check= (0<=(current_time-start_pos*timeframe)-result['time'][-1]<timeframe)
		
		return check

def start_server(python_exe_path):
		
	try:
		dirpath=os.path.dirname(__file__)
		subprocess.run(f"python3 {dirpath}/mt5linuxport/__main__.py '{python_exe_path}' &", shell=True)
	except Exception as e:
		print(f"Error running server: {repr(e)}")
		simple_message_box(f"Error running server: {repr(e)}")

def check_server_running(string=None):
	string=string if string else 'mt5linuxport/server'
	for proc in psutil.process_iter():
		if proc.status() != psutil.STATUS_ZOMBIE:
			for part in proc.cmdline():
				if string in part:
					return proc.pid
	return False

#Stops server non-graciously; not recommended for use
def stop_server(string=None):
	server_pid=check_server_running(string)
	if server_pid:
		subprocess.run(f"kill {server_pid}",shell=True)
		print(f"Server process {server_pid} killed")

def manage_server():
	if "start" in sys.argv:
		start_server()
	elif "stop" in sys.argv:
		stop_server()
	elif "check" in sys.argv:
		print(check_server_running())
	else:
		stop_server()

def mt5_object():
	
	Platform=sys.platform
	mt5=None
	if Platform.startswith('linux'):
		print(f"{Platform=}")
		try:
			from .mt5linuxport import MetaTrader5
		except:
			from mt5linuxport import MetaTrader5
		
		max_attempts=10
		attempt=1
		while attempt<=max_attempts:
			try:
				mt5=MetaTrader5()
				break
			except Exception as e:
				print(f"Attempt {attempt} failed: {repr(e)}")
				if attempt == max_attempts:
					print(f"{max_attempts=} exceeded")
					return None

				time.sleep(5)
				attempt += 1


	elif Platform in ('win32','cygwin','msys'):
		print(f"{Platform=}")
		# import MetaTrader5 as mt5
	
	mt5=MT5TimeshiftWrapper(mt5)

	return mt5

def mt5_server(python_exe_path):
	attempt=0
	while not check_server_running() and attempt<5:
		start_server(python_exe_path)
		time.sleep(3)
		attempt+=1
	
	mt5=mt5_object()
	
	return mt5

def mt5_timeframe(mt5=None,timeframe='H1'):
    mt5=mt5 if mt5 else mt5_object()

	# Assuming the timeframe_str is something like "H1"
    timeframe_attr = f"TIMEFRAME_{timeframe}"
    if hasattr(mt5, timeframe_attr):
        timeframe_value = getattr(mt5, timeframe_attr)
        # Now you can use timeframe_value in your MetaTrader5 library calls
        # For example:
        # mt5.copy_rates_from_pos(symbol, timeframe_value, start_pos, count)
        return timeframe_value
    else:
        raise ValueError("Invalid timeframe string")

if __name__=="__main__":
	manage_server()

	# Example usage
	# timezone_1 = 'EET'
	# timezone_2 = 'Europe/Moscow'

	# try:
	# 	shift = MT5TimeshiftWrapper.get_timezone_shift(timezone_1, timezone_2)
	# 	print(f"The time difference between {timezone_1} and {timezone_2} is {shift:.2f} hours.")
	# except ValueError as e:
	# 	print(e)