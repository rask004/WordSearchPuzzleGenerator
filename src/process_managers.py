import multiprocessing as mp


class WriterProcessManager:
    """Manages a separate process, used to write to a text file."""
    __slots__ = ('_queue', '_fname','_fmode','_process')
    END_MSG_WRITE = '!!EOF'

    def __init__(self, filename:str, mode:str='a'):
        """Create new Process, with a file name to write to, and the writing mode.
        filename:       name of file to write to.
        mode:           writing mode, either 'w' or 'a'. Default is 'a'."""
        ctx = mp.get_context('spawn')
        self._queue:mp.Queue[str] = ctx.Queue()
        self._fname = filename
        if mode != 'a':
            mode = 'w'
        self._fmode = mode
        self._process = ctx.Process(target=self._process_write_to_file)
        self._process.start()
        # print("Starting Process")

    def add(self, item):
        """Queue something for the process to write.
        item:       Data to write to file.

        Notes:      Data is always parsed as a string, but attempting to queue non-string data can
            have unpredictable effects.
                    The WriterProcess will halt if <WriterProcessManager.END_MSG_WRITE> is queued or .halt() method invoked."""
        if self._queue is not None:
            self._queue.put(str(item))
            # print("Queued Item:", item)

    def _process_write_to_file(self):
        """Process function for writing text to file.

        Notes:      Will run as an infinite loop until otherwise halted or an Exception occurs. See the .halt() method for halting the process."""
        while True:
            try:
                # print("Queue size:", self._queue.qsize())
                if not self._queue.empty():
                    next_item = self._queue.get()

                    if next_item == self.END_MSG_WRITE:
                        with open(self._fname, self._fmode) as fp:
                            fp.flush()
                        break
                    with open(self._fname, self._fmode) as fp:
                        fp.write(next_item)
                        # print("Writing Item:", next_item)
            except Exception:
                break
        # print(">>> End of Process Func")

    def halt(self):
        """Halts the Process."""
        self.add(self.END_MSG_WRITE)
        self._process.join()
