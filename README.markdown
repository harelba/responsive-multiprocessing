# Responsive Multiprocessing in python

## Overview
Multiprocess jobs using a closed pool, with easy ongoing messaging back to the main process.

Ongoing logging is built in on the subprocess side. The main process side should just provide a callback and wire the logged messages to their favourite logging mechanism.

Useful for making use of multiple cores, while having visibility about progress.

## Usage
Call `multiprocessWithMessaging` with the following parameters:


`process_count` - The number of processes in the pool

`func` - The function that actually executes the job that needs to be done. Should accept a keyword param called msg_handler, which can be used in order to send messages back to the main process. Logging support is built in. Use msg_handler.info() and similar methods

`func_args_list` - A list of lists, each containing a "job definition" for the func

`msg_handler` - A callback that will get the messages from the sub processes. Signature is (pid,msg_type,msg). Logging messages have a msg_type value 'log', and each message contains the tuple (timestamp,level,text). Defaults to None.

`log_handler` - A callback specific for logging messages. Expected signature is (pid,level,text). If not provided, Logging messages will be just sent as regular messages with msg_type 'log' and a message in the format (timestamp,level,text). Defaults to None.

`traceback_handler` - A callback for traceback propagation from the child processes to the main process. Defaults to default_traceback_handler, which just prints the traceback to standard error. Callback signature is (pid,timestamp,traceback). 

`check_interval` - The interval between checks that all jobs have been finished. Defaults to 0.1 - Unless it's a special case, there is no need to specify it.

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

## Generic message passing to the main process
The module is capable of generic message passing to the main process. The logging capabilities shown above are just a special common case.

In order to pass arbitrary messages back to the main process, just use msg_handler.send_message(msg) in the subprocess function, and provide a msg_handler callback to multiprocessWithMessaging(). 

The msg_handler callback signature should be (pid,msg_type,msg).

### Example
Let's assume that a subprocess wants to send a progress indication to the main process (a number from 0 to 1). 

    def msg_handler(pid,msg_type,msg):
        print "Got message %(msg)s from pid %s" % (msg,pid)
        # break down the message to its parts
        progress,text = msg
        print "Progress is %s" % progress

    def my_func(...,msg_handler):
        ...
        msg_handler.send_message((0.4,"another part of the message"))
        ...

    multiprocessWithMessaging(4,my_func,...,msg_handler=msg_handler)

### Another Example
Another example could be an ongoing aggregation of the processing duration of all the subprocesses.

    total_duration = 0
    def msg_handler(pid,msg_type,msg):
        duration = msg
        total_duration += duration    

    def my_func(...):
        start_time = time.time()
        ...
        duration = time.time() - start_time
        msg_handler.send_message((duration,))

    multiprocessWithMessaging(8,my_func,...,msg_handler=msg_handler)

    print "Total processing duration is %4.3f seconds" % total_duration 


Note that this will provide *ongoing* duration aggregation. You could send the duration as part of the function return value, and calculate the total duration from the results, but that would mean having the total duration only at the end of the entire processing.

## Contact
Any feedback would be much appreciated. 

Harel Ben-Attia, harelba@gmail.com, @harelba on Twitter
