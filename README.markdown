# Responsive Multiprocessing in python

## Overview
Multiprocess jobs using a closed pool, with easy ongoing messaging back to the main process.

Ongoing logging is built in on the subprocess side. The main process side should just provide a callback and wire the logged messages to their favourite logging mechanism.

Useful for making use of multiple cores, while having visibility about progress

## Usage
Just call `multiprocessWithMessaging(process_count, func, func_args_list,msg_handler=None,check_interval=0.1,log_handler=None)`

## Example
I've used it to check multiple gzip files for corruption.

First, let's define the actual function that does the checking. Note that it gets a filename and a msg_handler.
The msg_handler is used inside the function in order to perform logging.

    def check_file(filename,msg_handler):
        msg_handler.info('starting check for file %s' % filename)
        success = check_file(filename)
	if not success:
	        msg_handler.error('File %s is corrupt' % filename)
		return (False,filename)
	else:
		msg_handler.info('File %s is ok' % filename)
		return (True,filename)

Next, we'll define our logging function, which in this case will just delegate to print:

    def log(pid,level,text):
        print "pid-%(pid)s %(level)s %(text)s" % vars()

And now let's actually perform the processing:

    # Get the list of files that need to be processed
    files_to_process = glob.glob('*.gz')
    # Split the file names so each is in its own list
    jobs_to_run = [[f] for f in files_to_process]
    results = multiprocessWithMessaging(8,check_file,jobs_to_run,log_handler=log)

The first parameter is just the amount of processes that should be used for processing.
The second parameter is the name of our checking function.
The third parameter is a list of "jobs" that need to be executed. In our case, it's just one job per filename.
The fourth parameter is just the logging callback

Note that the function will not return until all jobs have been performed. After execution is finished, the results variable will contain the list of return values from check_file(). In that case, it will be a list of tuples (success,filename).


## Contact
Any feedback would be much appreciated. 

Harel Ben-Attia, harelba@gmail.com, @harelba on Twitter
