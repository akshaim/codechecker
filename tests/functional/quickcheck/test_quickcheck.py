# -----------------------------------------------------------------------------
#                     The CodeChecker Infrastructure
#   This file is distributed under the University of Illinois Open Source
#   License. See LICENSE.TXT for details.
# -----------------------------------------------------------------------------

"""This module tests the CodeChecker quickcheck feature."""

import glob
import os
import re
import subprocess
import unittest

from subprocess import CalledProcessError

from libtest import env


class QuickCheckTestCase(unittest.TestCase):
    """This class tests the CodeChecker quickcheck feature."""

    @classmethod
    def setup_class(cls):
        """Setup the class."""

        # Get an environment with CodeChecker command in it.
        cls.env = env.codechecker_env()

        cls.test_dir = os.path.join(
            os.path.dirname(__file__), 'quickcheck_test_files')

        # Change working dir to testfile dir so CodeChecker can be run easily.
        os.chdir(cls.test_dir)

    def __check_one_file(self, path):
        """
        Test quickcheck output on a ".output" file.

        The first line of the '.output' file contains the build command of the
        corresponding test file.
        The second line is to be omitted.
        From the third line onward, the file contains the output of the
        build command found in the first line.
        """
        with open(path, 'r') as ofile:
            lines = ofile.readlines()

        command, correct_output = (lines[0].strip(), ''.join(lines[2:]))

        try:
            output = subprocess.check_output(
                ['bash', '-c', command], env=self.env, cwd=self.test_dir)

            # Skip the analyzer version info between these two lines
            # it might be different in the test running environments.
            skip_version_after = "[] - Using analyzer:"
            skip_version_before = "[] - Static analysis is starting"
            skipline = False

            post_processed_output = []
            for line in output.splitlines(True):
                # replace timestamps
                line = re.sub(r'\[\d{2}:\d{2}\]', '[]', line)
                if line.startswith(skip_version_before):
                    skipline = False
                if not skipline:
                    post_processed_output.append(line)
                if line.startswith(skip_version_after):
                    skipline = True

            print("Test output file: " + path)
            self.assertEqual(''.join(post_processed_output), correct_output)
            return 0
        except CalledProcessError as cerr:
            print("Failed to run: " + ' '.join(cerr.cmd))
            print(cerr.output)
            return cerr.returncode

    def test_quickcheck_files(self):
        """Iterate over the test directory and run all tests in it."""
        for ofile in glob.glob(os.path.join(self.test_dir, '*.output')):
            self.assertEqual(self.__check_one_file(ofile), 0)