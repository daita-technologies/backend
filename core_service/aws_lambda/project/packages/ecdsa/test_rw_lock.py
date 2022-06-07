# Copyright Mateusz Kobos, (c) 2011
# https://code.activestate.com/recipes/577803-reader-writer-lock-with-priority-for-writers/
# released under the MIT licence

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import threading
import time
import copy
from ._rwlock import RWLock


class Writer(threading.Thread):
    def __init__(self, buffer_, rw_lock, init_sleep_time, sleep_time, to_write):
        """
        @param buffer_: common buffer_ shared by the readers and writers
        @type buffer_: list
        @type rw_lock: L{RWLock}
        @param init_sleep_time: sleep time before doing any action
        @type init_sleep_time: C{float}
        @param sleep_time: sleep time while in critical section
        @type sleep_time: C{float}
        @param to_write: data that will be appended to the buffer
        """
        threading.Thread.__init__(self)
        self.__buffer = buffer_
        self.__rw_lock = rw_lock
        self.__init_sleep_time = init_sleep_time
        self.__sleep_time = sleep_time
        self.__to_write = to_write
        self.entry_time = None
        """Time of entry to the critical section"""
        self.exit_time = None
        """Time of exit from the critical section"""

    def run(self):
        time.sleep(self.__init_sleep_time)
        self.__rw_lock.writer_acquire()
        self.entry_time = time.time()
        time.sleep(self.__sleep_time)
        self.__buffer.append(self.__to_write)
        self.exit_time = time.time()
        self.__rw_lock.writer_release()


class Reader(threading.Thread):
    def __init__(self, buffer_, rw_lock, init_sleep_time, sleep_time):
        """
        @param buffer_: common buffer shared by the readers and writers
        @type buffer_: list
        @type rw_lock: L{RWLock}
        @param init_sleep_time: sleep time before doing any action
        @type init_sleep_time: C{float}
        @param sleep_time: sleep time while in critical section
        @type sleep_time: C{float}
        """
        threading.Thread.__init__(self)
        self.__buffer = buffer_
        self.__rw_lock = rw_lock
        self.__init_sleep_time = init_sleep_time
        self.__sleep_time = sleep_time
        self.buffer_read = None
        """a copy of a the buffer read while in critical section"""
        self.entry_time = None
        """Time of entry to the critical section"""
        self.exit_time = None
        """Time of exit from the critical section"""

    def run(self):
        time.sleep(self.__init_sleep_time)
        self.__rw_lock.reader_acquire()
        self.entry_time = time.time()
        time.sleep(self.__sleep_time)
        self.buffer_read = copy.deepcopy(self.__buffer)
        self.exit_time = time.time()
        self.__rw_lock.reader_release()


class RWLockTestCase(unittest.TestCase):
    def test_readers_nonexclusive_access(self):
        (buffer_, rw_lock, threads) = self.__init_variables()

        threads.append(Reader(buffer_, rw_lock, 0, 0))
        threads.append(Writer(buffer_, rw_lock, 0.2, 0.4, 1))
        threads.append(Reader(buffer_, rw_lock, 0.3, 0.3))
        threads.append(Reader(buffer_, rw_lock, 0.5, 0))

        self.__start_and_join_threads(threads)

        ## The third reader should enter after the second one but it should
        ## exit before the second one exits
        ## (i.e. the readers should be in the critical section
        ## at the same time)

        self.assertEqual([], threads[0].buffer_read)
        self.assertEqual([1], threads[2].buffer_read)
        self.assertEqual([1], threads[3].buffer_read)
        self.assertTrue(threads[1].exit_time <= threads[2].entry_time)
        self.assertTrue(threads[2].entry_time <= threads[3].entry_time)
        self.assertTrue(threads[3].exit_time < threads[2].exit_time)

    def test_writers_exclusive_access(self):
        (buffer_, rw_lock, threads) = self.__init_variables()

        threads.append(Writer(buffer_, rw_lock, 0, 0.4, 1))
        threads.append(Writer(buffer_, rw_lock, 0.1, 0, 2))
        threads.append(Reader(buffer_, rw_lock, 0.2, 0))

        self.__start_and_join_threads(threads)

        ## The second writer should wait for the first one to exit

        self.assertEqual([1, 2], threads[2].buffer_read)
        self.assertTrue(threads[0].exit_time <= threads[1].entry_time)
        self.assertTrue(threads[1].exit_time <= threads[2].exit_time)

    def test_writer_priority(self):
        (buffer_, rw_lock, threads) = self.__init_variables()

        threads.append(Writer(buffer_, rw_lock, 0, 0, 1))
        threads.append(Reader(buffer_, rw_lock, 0.1, 0.4))
        threads.append(Writer(buffer_, rw_lock, 0.2, 0, 2))
        threads.append(Reader(buffer_, rw_lock, 0.3, 0))
        threads.append(Reader(buffer_, rw_lock, 0.3, 0))

        self.__start_and_join_threads(threads)

        ## The second writer should go before the second and the third reader

        self.assertEqual([1], threads[1].buffer_read)
        self.assertEqual([1, 2], threads[3].buffer_read)
        self.assertEqual([1, 2], threads[4].buffer_read)
        self.assertTrue(threads[0].exit_time < threads[1].entry_time)
        self.assertTrue(threads[1].exit_time <= threads[2].entry_time)
        self.assertTrue(threads[2].exit_time <= threads[3].entry_time)
        self.assertTrue(threads[2].exit_time <= threads[4].entry_time)

    def test_many_writers_priority(self):
        (buffer_, rw_lock, threads) = self.__init_variables()

        threads.append(Writer(buffer_, rw_lock, 0, 0, 1))
        threads.append(Reader(buffer_, rw_lock, 0.1, 0.6))
        threads.append(Writer(buffer_, rw_lock, 0.2, 0.1, 2))
        threads.append(Reader(buffer_, rw_lock, 0.3, 0))
        threads.append(Reader(buffer_, rw_lock, 0.4, 0))
        threads.append(Writer(buffer_, rw_lock, 0.5, 0.1, 3))

        self.__start_and_join_threads(threads)

        ## The two last writers should go first -- after the first reader and
        ## before the second and the third reader

        self.assertEqual([1], threads[1].buffer_read)
        self.assertEqual([1, 2, 3], threads[3].buffer_read)
        self.assertEqual([1, 2, 3], threads[4].buffer_read)
        self.assertTrue(threads[0].exit_time < threads[1].entry_time)
        self.assertTrue(threads[1].exit_time <= threads[2].entry_time)
        self.assertTrue(threads[1].exit_time <= threads[5].entry_time)
        self.assertTrue(threads[2].exit_time <= threads[3].entry_time)
        self.assertTrue(threads[2].exit_time <= threads[4].entry_time)
        self.assertTrue(threads[5].exit_time <= threads[3].entry_time)
        self.assertTrue(threads[5].exit_time <= threads[4].entry_time)

    @staticmethod
    def __init_variables():
        buffer_ = []
        rw_lock = RWLock()
        threads = []
        return (buffer_, rw_lock, threads)

    @staticmethod
    def __start_and_join_threads(threads):
        for t in threads:
            t.start()
        for t in threads:
            t.join()
