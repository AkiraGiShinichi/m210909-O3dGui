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
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import numpy as np
import time
import threading
from typing import List, Tuple
import pyrealsense2 as rs
import cv2

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


def create_button(text:str = "Button", func:object=None, hpad=0, vpad=0):
    button = gui.Button(text)
    button.horizontal_padding_em = hpad
    button.vertical_padding_em = vpad
    if func is not None:
        button.set_on_clicked(func)
    
    return button

def create_collapsable_vert(text:str="Collapsable Vert", items:List[object] = None, spacing:int=0, margins:Tuple[int, int, int, int]=(0, 0, 0, 0)):
    left, top, right, bottom = margins
    vert = gui.CollapsableVert(text, spacing, gui.Margins(left, top, right, bottom))
    for item in items:
        vert.add_child(item)

    return vert


class AppWindow:
    MENU_OPEN = 1
    MENU_EXPORT = 2
    MENU_QUIT = 3
    MENU_SHOW_SETTINGS = 4
    MENU_ABOUT = 5

    def __init__(self, width=1024, height=768, *args, **kwargs):
        self.window = gui.Application.instance.create_window("Open3D", width=1024, height=768)
        em = self.window.theme.font_size

        # ─── REALSENSE CAMERA ────────────────────────────────────────────
        self.pipeline = rs.pipeline()
        self.config = rs.config()

        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)

        self.pipeline.start(self.config)
        #
        # ────────────────────────────────────────── REALSENSE CAMERA ─────
        #


        # ─── MAIN DISPLAY ────────────────────────────────────────────────
        self.main_display = gui.SceneWidget()
        self.main_display.scene = rendering.Open3DScene(self.window.renderer)
        #
        # ────────────────────────────────────────────── MAIN DISPLAY ─────
        #


        # ─── PANEL ───────────────────────────────────────────────────────
        self._hi_button = create_button("Say Hi", self._say_hi, hpad=0.5)
        self._hi_button1 = create_button("Say Hi1", self._say_hi, hpad=0.5)
        self._hi_button2 = create_button("Say Hi2", self._say_hi, hpad=0.5)
        self._hi_button3 = create_button("Say Hi3", self._say_hi, hpad=0.5)

        group1 = [self._hi_button, self._hi_button1, self._hi_button2, self._hi_button3]
        first_ctrls = create_collapsable_vert("First Controls", items=group1, spacing=0.25*em, margins=(em, 0, em, 0.25 * em))

        self.color_image = np.zeros((100, 100, 3))
        color_image_label = gui.Label("Color image")
        self.color_image_preview = gui.ImageWidget()

        self.depth_image = np.zeros((100, 100, 3))
        depth_image_label = gui.Label("Depth image")
        self.depth_image_preview = gui.ImageWidget()

        self.cloud = None
        cloud_label = gui.Label("Point cloud")
        self.cloud_preview = gui.SceneWidget()
        self.cloud_preview.scene = rendering.Open3DScene(self.window.renderer)

        group2 = [color_image_label, self.color_image_preview, depth_image_label, self.depth_image_preview, cloud_label, self.cloud_preview]
        second_ctrls = create_collapsable_vert("Second Controls", items=group2, spacing=0.25*em, margins=(em, 0, em, 0))

        self._settings_panel = gui.Vert(0, gui.Margins(0.25 * em, 0.25* em, 0.25 * em, 0.25 * em))
        self._settings_panel.add_child(first_ctrls)
        self._settings_panel.add_child(second_ctrls)
        #
        # ───────────────────────────────────────────────────── PANEL ─────
        #


        # ─── MENU ────────────────────────────────────────────────────────
        if gui.Application.instance.menubar is None:
            file_menu = gui.Menu()
            file_menu.add_item("Open...", AppWindow.MENU_OPEN)
            file_menu.add_separator()
            file_menu.add_item("Quit", AppWindow.MENU_QUIT)

            settings_menu = gui.Menu()
            settings_menu.add_item("Settings", AppWindow.MENU_SHOW_SETTINGS)
            settings_menu.set_checked(AppWindow.MENU_SHOW_SETTINGS, True)

            help_menu = gui.Menu()
            help_menu.add_item("About", AppWindow.MENU_ABOUT)

            menu = gui.Menu()
            menu.add_menu("File", file_menu)
            menu.add_menu("Settings", settings_menu)
            menu.add_menu("Help", help_menu)

            gui.Application.instance.menubar = menu
        #
        # ────────────────────────────────────────────────────── MENU ─────
        #


        # ─── STATUS BAR ──────────────────────────────────────────────────
        self.status_bar = gui.Label("")
        self.status_bar.visible = False
        #
        # ──────────────────────────────────────────────── STATUS BAR ─────
        #


        # ─── WINDOW ──────────────────────────────────────────────────────
        self.window.add_child(self.main_display)
        self.window.add_child(self._settings_panel)
        self.window.add_child(self.status_bar)
        self.window.set_on_layout(self._on_layout)

        self.window.set_on_menu_item_activated(AppWindow.MENU_OPEN, self._on_menu_open)
        self.window.set_on_menu_item_activated(AppWindow.MENU_EXPORT, self._on_menu_export)
        self.window.set_on_menu_item_activated(AppWindow.MENU_QUIT, self._on_menu_quit)
        self.window.set_on_menu_item_activated(AppWindow.MENU_SHOW_SETTINGS, self._on_menu_toggle_settings_panel)
        self.window.set_on_menu_item_activated(AppWindow.MENU_ABOUT, self._on_menu_about)

        threading.Thread(target=self._update_thread).start()
        #
        # ──────────────────────────────────────────────────── WINDOW ─────
        #

    def _on_layout(self, layout_context):
        window_size = self.window.content_rect
        self.main_display.frame = window_size

        panel_width = 17 * layout_context.theme.font_size
        panel_height = min(window_size.height, self._settings_panel.calc_preferred_size(layout_context, gui.Widget.Constraints()).height)
        self._settings_panel.frame = gui.Rect(window_size.get_right() - panel_width, window_size.y, panel_width, panel_height)

        pref = self.status_bar.calc_preferred_size(layout_context, gui.Widget.Constraints())
        self.status_bar.frame = gui.Rect(window_size.x, window_size.get_bottom() - pref.height, pref.width, pref.height)

    def _on_menu_open(self):
        dlg = gui.FileDialog(gui.FileDialog.OPEN, "Choose file to load", self.window.theme)
        dlg.add_filter(".ply .pcd", "Point cloud files (.ply, .pcd)")
        dlg.add_filter(".ply", "Polygon files (.ply)")
        dlg.add_filter(".pcd", "Point Cloud Data files (.pcd)")
        dlg.add_filter("", "All files")

        dlg.set_on_cancel(self._on_file_dialog_cancel)
        dlg.set_on_done(self._on_load_dialog_done)

        self.window.show_dialog(dlg)

    def _on_file_dialog_cancel(self):
        self.window.close_dialog()

    def _on_load_dialog_done(self, filename):
        self.window.close_dialog()
        self.load(filename)

    def load(self, path):
        self.main_display.scene.clear_geometry()

        cloud = o3d.io.read_point_cloud(path)

        material = rendering.Material()
        material.base_color = [0.9, 0.9, 0.9, 1.0]
        material.shader = "defaultLit"

        self.main_display.scene.add_geometry("__model__", cloud, material)
        bounds = cloud.get_axis_aligned_bounding_box()
        self.main_display.setup_camera(60, bounds, bounds.get_center())

    def _on_menu_export(self):
        pass

    def _on_menu_quit(self):
        gui.Application.instance.quit()

    def _on_menu_toggle_settings_panel(self):
        self._settings_panel.visible = not self._settings_panel.visible
        gui.Application.instance.menubar.set_checked(AppWindow.MENU_SHOW_SETTINGS, self._settings_panel.visible)

    def _on_menu_about(self):
        pass

    def _update_thread(self):
        while 1:
            time.sleep(0.100)

            frames = self.pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            depth_image = np.asarray(depth_frame.get_data())
            color_image = np.asarray(color_frame.get_data())

            # deph_image_dim, color_image_dim = depth_image.shape, color_image.shape

            def update():
                def to_o3d_image(np_image):
                    return o3d.geometry.Image(np_image)
                
                def standardize_depth_image(image, alpha=0.03, color_map=cv2.COLORMAP_JET):
                    return cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=alpha), color_map)

                self.depth_image_preview.update_image(to_o3d_image(standardize_depth_image(depth_image)))
                self.color_image_preview.update_image(to_o3d_image(color_image))
            
            gui.Application.instance.post_to_main_thread(self.window, update)

    def _say_hi(self):
        print("Hi!")

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

    _logger.debug("Start AppWindow")
    gui.Application.instance.initialize()
    window = AppWindow(width=1024, height=768)
    gui.Application.instance.run()

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
