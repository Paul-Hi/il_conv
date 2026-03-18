import sys
import time
import unittest


class PerTestTextResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self._test_start_time = None

    def startTest(self, test):
        super().startTest(test)
        self._test_start_time = time.perf_counter()

    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        duration = time.perf_counter() - self._test_start_time
        self.stream.writeln(f"OK {self.getDescription(test)} ({duration:.3f}s)")

    def addFailure(self, test, err):
        unittest.TestResult.addFailure(self, test, err)
        duration = time.perf_counter() - self._test_start_time
        self.stream.writeln(f"FAILED {self.getDescription(test)} ({duration:.3f}s)")
        self.stream.writeln(self._exc_info_to_string(err, test))

    def addError(self, test, err):
        unittest.TestResult.addError(self, test, err)
        duration = time.perf_counter() - self._test_start_time
        self.stream.writeln(f"FAILED {self.getDescription(test)} ({duration:.3f}s)")
        self.stream.writeln(self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        unittest.TestResult.addSkip(self, test, reason)
        duration = time.perf_counter() - self._test_start_time
        self.stream.writeln(f"OK {self.getDescription(test)} - skipped: {reason} ({duration:.3f}s)")

    def addExpectedFailure(self, test, err):
        unittest.TestResult.addExpectedFailure(self, test, err)
        duration = time.perf_counter() - self._test_start_time
        self.stream.writeln(f"OK {self.getDescription(test)} - expected failure ({duration:.3f}s)")

    def addUnexpectedSuccess(self, test):
        unittest.TestResult.addUnexpectedSuccess(self, test)
        duration = time.perf_counter() - self._test_start_time
        self.stream.writeln(f"FAILED {self.getDescription(test)} - unexpected success ({duration:.3f}s)")

    def printErrors(self):
        pass


class PerTestTextRunner(unittest.TextTestRunner):
    resultclass = PerTestTextResult

    def __init__(self):
        super().__init__(verbosity=0)


def main() -> int:
    suite = unittest.defaultTestLoader.discover("tests")
    result = PerTestTextRunner().run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())