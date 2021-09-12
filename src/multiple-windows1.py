"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = o3dgui.skeleton:run

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

import config as conf
import open3d as o3d
import numpy as np
import time
import threading

from o3dgui import __version__

__author__ = "akiragishinichi"
__copyright__ = "akiragishinichi"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from o3dgui.skeleton import fib`,
# when using this Python module as a library.


def fib(n):
    """Fibonacci example function

    Args:
      n (int): integer

    Returns:
      int: n-th Fibonacci number
    """
    assert n > 0
    a, b = 1, 1
    for i in range(n - 1):
        a, b = b, a + b
    return a


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
        version="O3dGui {ver}".format(ver=__version__),
    )
    parser.add_argument("--n", help="n-th Fibonacci number", type=int)
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


class MultiWinApp:
    def __init__(self, *args, **kwargs):
        self.is_done = False
        self.cloud = None
        self.main_vis = None
        self.n_snapshots = 0
        self.snapshot_pos = None

    def run(self):
        app = o3d.visualization.gui.Application.instance
        app.initialize()

        self.main_vis = o3d.visualization.O3DVisualizer("Open3D - Multi-Window Demo")
        self.main_vis.add_action("Take snapshot in new window", self.on_snapshot)
        self.main_vis.set_on_close(self.on_main_window_closing)

        app.add_window(self.main_vis)
        self.snapshot_pos = (self.main_vis.os_frame.x, self.main_vis.os_frame.y)

        threading.Thread(target=self.update_thread).start()

        app.run()

    def on_snapshot(self, vis):
        pass

    def on_main_window_closing(self):
        self.is_done = True
        return True

    def update_thread(self):
        self.cloud = o3d.io.read_point_cloud(conf.CLOUD_PATH)
        print(self.cloud)
        bounds = self.cloud.get_axis_aligned_bounding_box()
        extent = bounds.get_extent()

        def add_first_cloud():
            mat = o3d.visualization.rendering.Material()
            mat.shader = "defaultUnlit"
            self.main_vis.add_geometry(conf.CLOUD_NAME, self.cloud, mat)
            self.main_vis.reset_camera_to_default()
            self.main_vis.setup_camera(60, bounds.get_center(), bounds.get_center() + [0, 0, -3], [0, -1, 0])
        
        o3d.visualization.gui.Application.instance.post_to_main_thread(self.main_vis, add_first_cloud)

        while not self.is_done:
            time.sleep(0.1)

            # pts = np.asarray(self.cloud.points)
            # magnitude = 0.005 * extent
            # displacement = magnitude * (np.random.random_sample(pts.shape) - 0.5)

            # new_pts = pts + displacement
            # self.cloud.points = o3d.utility.Vector3dVector(new_pts)

            # def update_cloud():
            #     self.main_vis.remove_geometry(conf.CLOUD_NAME)
            #     mat = o3d.visualization.rendering.Material()
            #     mat.shader = "defaultUnlit"
            #     self.main_vis.add_geometry(conf.CLOUD_NAME, self.cloud, mat)

            # if self.is_done:
            #     break

            # o3d.visualization.gui.Application.instance.post_to_main_thread(self.main_vis, update_cloud)

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
    print("The {}-th Fibonacci number is {}".format(args.n, fib(args.n)))

    _logger.debug("Start MultiWinApp")
    MultiWinApp().run()

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
    #     python -m o3dgui.skeleton 42
    #
    run()
