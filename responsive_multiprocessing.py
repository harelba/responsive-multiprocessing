#!/usr/bin/python

# Multiprocess jobs using a closed pool, with easy ongoing messaging back to the main process.
#
# Ongoing logging is built in on the subprocess side. The main process side should just provide a callback
# and wire the logged messages to their favourite logging mechanism.
#
# Useful for making use of multiple cores, while having visibility about progress
#
# Author: Harel Ben-Attia (@harelba)

import os,sys
import time
from multiprocessing import Pool,Queue,Manager,active_children
import traceback
import subprocess
import threading
import glob

class SubProcessMessageHandler(object):
	def __init__(self,queue):
		self.queue = queue

	def send_message(self,msg):
		self.queue.put((os.getpid(),'generic',msg))

	def info(self,text):
		self._log(time.time(),"info",text)

	def error(self,text):
		self._log(time.time(),"error",text)

	def _log(self,timestamp,level,text):
		self.queue.put((os.getpid(),'log',(timestamp,level,text)))

class MainProcessMessageHandler(threading.Thread):
	def __init__(self,queue,msg_handler=None,log_handler=None):
		threading.Thread.__init__(self)
		self.queue = queue
		self.daemon = True
		self.msg_handler = msg_handler
		self.log_handler = log_handler

	def run(self):
		while True:
			try:
				pid,msg_type,msg = self.queue.get()
				if msg_type == 'log' and self.log_handler is not None:
					timestamp,level,text = msg
					self.log_handler(pid,level,text)
				else:
					if self.msg_handler is not None:
						self.msg_handler(pid,msg_type,msg)
			except (KeyboardInterrupt, SystemExit):
				raise
			except EOFError:
				break
			except:
				traceback.print_exc(file=sys.stderr)

def multiprocessWithMessaging(process_count, func, func_args_list,msg_handler=None,log_handler=None,check_interval=0.1):
	""" 
	Multiprocess jobs using a closed pool, with easy ongoing messaging back to the main process.

	Ongoing logging is built in. 

	process_count - The number of processes in the pool
	func - The function that actually executes the job that needs to be done. Should accept a keyword param called msg_handler,
	       which can be used in order to send messages back to the main process. Logging support is built in. Use msg_handler.info()
               and similar methods
	func_args_list - A list of lists, each containing a "job definition" for the func
	msg_handler - A callback that will get the messages from the sub processes. Signature is (pid,msg_type,msg).
	                Logging messages have a msg_type value 'log', and each message contains the tuple (timestamp,level,text)
	log_handler - A callback specific for logging messages. Expected signature is (pid,level,text). If not provided, Logging messages will be just sent as regular messages with msg_type 'log' and a message in the format (timestamp,level,text). 
	check_interval - The interval between checks that all jobs have been finished. Usually, no need to specify it.
	"""
	m = Manager()
	queue = m.Queue()
	main_process_msg_handler = MainProcessMessageHandler(queue,msg_handler,log_handler)
	main_process_msg_handler.start()

	pool = Pool(processes=process_count)
	results = []
	for func_args in func_args_list:
		msg_handler = SubProcessMessageHandler(queue)
		results.append(pool.apply_async(func,func_args,kwds={ 'msg_handler' : msg_handler }))
	pool.close()
	# Manager is also an active child, and running pool.join() before the queue is consumed can cause a deadlock
	# appearantly
	while len(active_children()) != 1:
		time.sleep(.1)
	pool.join()
	r = []
	for result in results:
		r.append(result.get())
	return r
	
