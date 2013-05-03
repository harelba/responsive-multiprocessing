# Responsive Multiprocessing in python

## Overview
Multiprocess jobs using a closed pool, with easy ongoing messaging back to the main process.

Ongoing logging is built in on the subprocess side. The main process side should just provide a callback and wire the logged messages to their favourite logging mechanism.

Useful for making use of multiple cores, while having visibility about progress

## Usage
Call `multiprocessWithMessaging(process_count, func, func_args_list,msg_handler=None,log_handler=None,check_interval=0.1)`

`process_count` - The number of processes in the pool

`func` - The function that actually executes the job that needs to be done. Should accept a keyword param called msg_handler, which can be used in order to send messages back to the main process. Logging support is built in. Use msg_handler.info() and similar methods

`func_args_list` - A list of lists, each containing a "job definition" for the func

`msg_handler` - A callback that will get the messages from the sub processes. Signature is (pid,msg_type,msg). Logging messages have a msg_type value 'log', and each message contains the tuple (timestamp,level,text)

`log_handler` - A callback specific for logging messages. Expected signature is (pid,level,text). If not provided, Logging messages will be just sent as regular messages with msg_type 'log' and a message in the format (timestamp,level,text). 

`check_interval` - The interval between checks that all jobs have been finished. Usually, no need to specify it.

## Example
The original reason this module has been written was to parallelize checking a set of gzip files for corruption, so let's look at it as an example use case.

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

Next, we'll define our logging function, which in this case will just delegate to print. Notice that it gets the pid of the process doing the logging.

    def log(pid,level,text):
        print "pid-%(pid)s %(level)s %(text)s" % vars()

And now let's actually perform the processing:

    # Get the list of files that need to be processed
    files_to_process = glob.glob('*.gz')
    # Split the file names so each is in its own list (Each one is a separate "job" that needs to be run)
    jobs_to_run = [[f] for f in files_to_process]
    results = multiprocessWithMessaging(8,check_file,jobs_to_run,log_handler=log)

The first parameter is just the amount of processes that should be used for processing.
The second parameter is the name of our checking function.
The third parameter is a list of "jobs" that need to be executed. In our case, it's just one job per filename.
The fourth parameter is just the logging callback

Note that the function will not return until all jobs have been performed. 

After execution is finished, the results variable will contain the list of return values from check_file(). In that case, it will be a list of tuples (success,filename).


## Contact
Any feedback would be much appreciated. 

Harel Ben-Attia, harelba@gmail.com, @harelba on Twitter
