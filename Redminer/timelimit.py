import time
import threading
from threading import Thread

class TimeLimitExpired(Exception): 
    pass

def timelimit(timeout, func, args=(), kwargs={}):
    """ Run func with the given timeout. If func didn't finish running
        within the timeout, raise TimeLimitExpired
    """
    class FuncThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.result = None

        def run(self):
            self.result = func(*args, **kwargs)

        def _stop(self):
            if self.isAlive():
                Thread._Thread__stop(self)

    it = FuncThread()
    it.start()
    it.join(timeout)
    if it.isAlive():
        it._stop()
        raise TimeLimitExpired
    else:
        return it.result

    def long_running_function1():
        print "long_running_function1"
        time.sleep(2)
        
if __name__ == '__main__':   
    timelimit(1,long_running_function1)