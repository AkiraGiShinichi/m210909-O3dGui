# video_worker_thread.py
import os
import datetime
import numpy as np
import cv2
import pyrealsense2 as rs

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Signal, QThread

EXTERNAL_CAMERA = 1


class RealsenseCapture():
    camera_is_open = False

    # def __init__(self, width=1280, height=720, fps=30) -> None:
    def __init__(self, width=1280, height=720, fps=30, with_depth=False) -> None:
        self.with_depth = with_depth
        # Create a pipeline
        self.pipeline = rs.pipeline()
        # Create a config and configure the pipeline to stream
        #  different resolutions of color and depth streams
        self.config = rs.config()
        self.config.enable_stream(
            rs.stream.color, width, height, rs.format.rgb8, fps)
        # self.config.enable_stream(
        #     rs.stream.depth, width, height, rs.format.z16, fps)
        # self.config.enable_stream(
        #     rs.stream.infrared, 1, width, height, rs.format.y8, fps)
        # self.config.enable_stream(
        #     rs.stream.infrared, 2, width, height, rs.format.y8, fps)
        # Create an align object
        # rs.align allows us to perform alignment of depth frames to others frames
        # The "align_to" is the stream type to which we plan to align depth frames.
        # align_to = rs.stream.color
        # self.align = rs.align(align_to)

        try:
            # ! If there isn't any Realsense camera, this function is broken immediately -> time saving
            pipeline_profile = self.config.resolve(
                rs.pipeline_wrapper(self.pipeline))

            self.profile = self.pipeline.start(self.config)

            sensor = self.profile.get_device().query_sensors()[1]
            sensor.set_option(rs.option.exposure, 4)
            sensor.set_option(rs.option.gain, 80)  # 84

            self.camera_is_open = True
            print(f'\n    RealsenseCapture - initialized')
        except:
            print(f'\n    RealsenseCapture - initialized not success')

    def read(self, return_depth=False):
        """Read BGR image from Realsense camera

        Returns:
            [bool]: able to capture frame or not
            [ndarray]: frame
        """
        try:
            frames = self.pipeline.wait_for_frames()
            # Align the depth frame to color frame
            # frames = self.align.process(frames)

            color_frame = frames.get_color_frame()
            # depth_frame = frames.get_depth_frame()

            color_image = np.asarray(color_frame.get_data())
            # depth_image = np.asarray(depth_frame.get_data())
            # print(color_image.shape, depth_image.shape)

            # if return_depth:
            #     return True, color_image[:, :, ::-1], depth_image
            # else:
            return True, color_image[:, :, ::-1]
        except:
            self.camera_is_open = False
            print(f'\n    RealsenseCapture - read: error')
            return False, None

    def isOpened(self):
        return self.camera_is_open

    def release(self):
        print(f'\n    RealsenseCapture - release')
        try:
            self.pipeline.stop()
        except:
            print(
                f'\n    RealsenseCapture - release: error. Camera is not initialized yet.')


class VideoWorkerThread(QThread):
    frame_data_updated = Signal(np.ndarray)
    frame_data_invalid = Signal()

    def __init__(
            self, parent, video_file, fps=24, frame_size=(640, 480)) -> None:
        super().__init__()
        self.parent = parent
        self.video_file = video_file
        self.fps = fps
        self.frame_size = frame_size
        self.delay = int(1000 / self.fps)

        self.setup_capture()

        print(f'\n  VideoWorkerThread - initialized')

    def setup_capture(self):
        print(f'\n  VideoWorkerThread - setup_capture')
        if self.video_file == 0:
            self.video_capture = RealsenseCapture(
                width=self.frame_size[0],
                height=self.frame_size[1])
        elif self.video_file == 1:
            self.video_capture = cv2.VideoCapture(
                EXTERNAL_CAMERA + cv2.CAP_DSHOW)
            self.video_capture.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            self.video_capture.set(cv2.CAP_PROP_FOCUS, 521)
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
            self.video_capture.set(
                cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])
            self.video_capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(
                'M', 'J', 'P', 'G'))
        else:
            self.video_capture = cv2.VideoCapture(self.video_file)

    def initializeRecorder(self, file_path):
        print(f'\n  VideoWorkerThread - initializeRecorder')
        self.video_writer = cv2.VideoWriter(
            file_path, cv2.VideoWriter.fourcc(
                'M', 'J', 'P', 'G'), self.fps, self.frame_size)

    def executeRecording(self):
        if hasattr(self, 'video_writer'):
            if self.video_writer.isOpened():
                self.video_writer.write(self.frame)
            else:
                print(
                    f'\n  VideoWorkerThread - run / video_is_recording: Error - recorder is not initialized yet.')

    def stopRecording(self):
        if hasattr(self, 'video_writer'):
            if self.video_writer.isOpened():
                self.video_writer.release()
                print(
                    f'\n  VideoWorkerThread - run / not video_is_recording: stop recording.')

    def run(self):
        # print(f'\n  VideoWorkerThread - run')
        # print(f'\n  VideoWorkerThread - run: initialize video capture')
        # if self.video_file == 0:
        #     self.video_capture = RealsenseCapture(
        #         width=self.frame_size[0],
        #         height=self.frame_size[1])
        # elif self.video_file == 1:
        #     self.video_capture = cv2.VideoCapture(
        #         EXTERNAL_CAMERA + cv2.CAP_DSHOW)
        #     self.video_capture.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        #     self.video_capture.set(cv2.CAP_PROP_FOCUS, 521)
        #     self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
        #     self.video_capture.set(
        #         cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])
        #     self.video_capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(
        #         'M', 'J', 'P', 'G'))
        # else:
        #     self.video_capture = cv2.VideoCapture(self.video_file)

        print(f'\n  VideoWorkerThread - run: continuously capture frame and emit result')
        if not self.video_capture.isOpened():
            self.frame_data_invalid.emit()
        else:
            while self.parent.params['state']['video_thread_is_running']:
                if self.parent.params['state']['video_is_pausing']:
                    continue
                else:
                    ret_val, self.frame = self.video_capture.read()  # Read a frame from camera
                    if not ret_val:  # If couldn't get new valid frame
                        print(
                            f'\n  VideoWorkerThread - run: Error or reached the end of the video')
                        self.frame_data_invalid.emit()
                        break
                    else:  # If got new valid frame
                        self.frame_data_updated.emit(self.frame)
                        if self.parent.params['state']['video_is_recording']:
                            self.executeRecording()
                        else:
                            self.stopRecording()
                    cv2.waitKey(self.delay)

    def stopThread(self):
        print(f'\n  VideoWorkerThread - stopThread')
        self.wait()

        self.releaseVideoTools()

        QApplication.processEvents()

    def releaseVideoTools(self):
        print(f'\n  VideoWorkerThread - releaseVideoTools')
        if hasattr(self, 'video_writer'):
            self.video_writer.release()
        if hasattr(self, 'video_capture'):
            self.video_capture.release()
