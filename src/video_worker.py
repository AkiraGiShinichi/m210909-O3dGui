"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = aztermis.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This skeleton file can be safely removed if not needed!

References:
    - https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import logging
import sys
from typing import Tuple

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication

from aztermis import __version__

__author__ = "akiragishinichi"
__copyright__ = "akiragishinichi"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from aztermis.skeleton import fib`,
# when using this Python module as a library.


# def fib(n):
#     """Fibonacci example function

#     Args:
#       n (int): integer

#     Returns:
#       int: n-th Fibonacci number
#     """
#     assert n > 0
#     a, b = 1, 1
#     for i in range(n - 1):
#         a, b = b, a + b
#     return a


class VideoWorkerThread(QThread):
    frame_data_updated = Signal(np.ndarray)
    frame_data_invalid = Signal(str)
    is_running = False

    def __init__(
        self,
        frame_size: Tuple[int, int] = (640, 480),
        fps: int = 30,
        camera_id: int = 0,
    ) -> None:
        """Initialize video worker

        :param fps: frame per second, defaults to 25
        :type fps: int, optional
        :param frame_size: (width, height) of frame, defaults to (640, 480)
        :type frame_size: tuple(int, int), optional
        """
        super().__init__()
        print("\n  VideoWorkerThread - initializing..")
        self._fps = fps
        self._frame_size = frame_size
        self._delay = int(1000 / self._fps)
        self._camera_id = camera_id

        self._initialize_capture()

    def _initialize_capture(self):
        """Initialize video capture"""
        print("\n  VideoWorkerThread - initialize_capture")
        self._capture = cv2.VideoCapture(self._camera_id)
        self._capture.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._frame_size[0])
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._frame_size[1])
        print(f"Camera expected resolution: {self._frame_size}")
        w = self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Camera actual resolution: {(w, h)}")
        # TODO: raise error or smt when config FRAME_SIZE not success
        self._capture.set(
            cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc("M", "J", "P", "G")
        )

    def _capture_frame(self):
        """Capture a frame"""
        if self.is_running:
            if self._capture.isOpened():
                ret_val, self.frame = self._capture.read()
                if ret_val:
                    self.frame_data_updated.emit(self.frame)
                    return True
                else:
                    self.frame_data_invalid.emit("Can not capture frame.")
            else:
                self.frame_data_invalid.emit("Video capture is not opened yet.")
        else:
            self.frame_data_invalid.emit("Worker is not running yet.")
        return False

    def run(self):
        """Run workers"""
        print("\n  VideoWorkerThread - run")
        self.is_running = True
        while self.is_running:
            ret_val = self._capture_frame()
            if not ret_val:
                self.is_running = False
                print(
                    "\n  VideoWorkerThread - run: Error occured. Worker stop running."
                )
                break
            cv2.waitKey(self._delay)

    def stop_thread(self):
        """Stop worker running & worker thread"""
        print("\n  VideoWorkerThread - stop_thread")

        self.is_running = False
        self.wait()
        self._capture.release()

        QApplication.processEvents()

    def open_camera_config(self):
        self._capture.set(cv2.CAP_PROP_SETTINGS, 1)


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version="Aztermis {ver}".format(ver=__version__),
    )
    parser.add_argument(dest="n", help="n-th Fibonacci number", type=int, metavar="INT")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args):
    """Wrapper allowing :func:`fib` to be called with string arguments in a CLI fashion

    Instead of returning the value from :func:`fib`, it prints the result to the
    ``stdout`` in a nicely formatted message.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    _logger.debug("Starting crazy calculations...")
    # print("The {}-th Fibonacci number is {}".format(args.n, fib(args.n)))
    _logger.info("Script ends here")


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m aztermis.skeleton 42
    #
    run()
