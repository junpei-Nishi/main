import os
import warnings
warnings.simplefilter(action='ignore', category=Warning)
from datetime import datetime
from shutil import move, copy2
import imageio
from module.novelty_detector import NoveltyDetector
from module.trimming_data import TrimmingData
import argparse
import cv2
import time
from pathlib import Path
import numpy as np
from module.CvOverlayImage import CvOverlayImage
import json

def coords(s):
    try:
        x, y = map(int, s.split(','))
        return x, y
    except:
        raise argparse.ArgumentTypeError("Coordinates must be x,y")

class  SDTestInspector:
    
    def predict(self, image_paths_list, model):
        return model.predict_paths(image_paths_list)

    # カメラ撮影メソッド
    def save_frame_camera_key(self, args, dir_path, basename, timestamp, ext='jpg', delay=10, window_name='frame'):
        cap = cv2.VideoCapture(args.camera_id)
        if not cap.isOpened():
            return

        base_path = os.path.join(dir_path, basename)
        
        _, frame = cap.read()
        if args.mirror is True:
            frame = frame[:, ::-1]

        if args.size is not None and len(args.size) == 2:
            frame = cv2.resize(frame, args.size)

        if args.camera_guide and min(args.size) >= 226:
            guide = cv2.imread("view_finder_v3.png", cv2.IMREAD_UNCHANGED)
            guide_height, guide_width = guide.shape[0:2]
            frame_height, frame_width = frame.shape[0:2]
            left_top = int(frame_width / 2 - guide_width / 2), int(frame_height / 2 - guide_height / 2)
            finder = CvOverlayImage.overlay(frame, guide, left_top)
            # frame = CvOverlayImage.overlay(frame, guide, left_top)
        elif args.camera_guide and min(args.size) < 226:
            print('Size is too small. the size should be bigger than (226, 226)')

        if args.i2c_input: # 即時の自動撮影
            imagefilename = '{}_{}.{}'.format(base_path, timestamp, ext)
            cv2.imwrite(imagefilename, frame)
            cap.release()
            return imagefilename
        else: # プレビュー画面上で手動撮影
            while True:
                # cv2.startWindowThread()
                _, frame = cap.read()
                if args.mirror is True:
                    frame = frame[:, ::-1]

                if args.size is not None and len(args.size) == 2:
                    frame = cv2.resize(frame, args.size)

                if args.camera_guide and min(args.size) >= 226:
                    guide = cv2.imread("view_finder_v3.png", cv2.IMREAD_UNCHANGED)
                    guide_height, guide_width = guide.shape[0:2]
                    frame_height, frame_width = frame.shape[0:2]
                    left_top = int(frame_width / 2 - guide_width / 2), int(frame_height / 2 - guide_height / 2)
                    finder = CvOverlayImage.overlay(frame, guide, left_top)
                    cv2.imshow('camera capture', finder)
                elif args.camera_guide and min(args.size) < 226:
                    print('Size is too small. the size should be bigger than (226, 226)')
                else:
                    cv2.imshow('camera capture', frame)

                k = cv2.waitKey(1)
                if k == 27:  # ESCで終了
                    break
                elif k == 115:  # sで撮影
                    imagefilename = '{}_{}.{}'.format(base_path, timestamp, ext)
                    cv2.imwrite(imagefilename, frame)
                    cap.release()
                    cv2.destroyAllWindows()
                    return imagefilename

            cap.release()
            cv2.destroyAllWindows()

    # 推論開始メソッド
    def inspection(self, args):
        Path('captured_image').mkdir(exist_ok=True)
        Path('captured_image/tmp').mkdir(exist_ok=True)

        timestamp = str(datetime.now().isoformat()).replace(':', '-')[0:-7]
        if args.camera:
            original_image_path = self.save_frame_camera_key(args, 'captured_image', 'cap', timestamp)
        elif args.fastmode:
            original_image_path = 'testimages/kakipi/test/OK/camera_0_2019-06-19T17-46-52.730279.jpg'
        elif args.path:
            original_image_path = args.path
        else:
            original_image_path = input('image path: ')

        _, ext = os.path.splitext(original_image_path)
        file_name = f'cam{args.camera_id}_{timestamp}{ext}'
        copied_image_path = os.path.join(os.path.dirname(__file__), 'captured_image', 'tmp', file_name)
        copy2(original_image_path, copied_image_path)

        image_paths = [copied_image_path]
        image_path = copied_image_path
        save_path = os.path.dirname(image_path)

        im = imageio.imread(image_path)
        im_width, im_height = im.shape[1], im.shape[0]

        if args.nn == 'vgg':
            tr_width, tr_height = (200, 200)
        elif args.nn == 'MobileNet':
            tr_width, tr_height = (192, 192)
        elif args.nn == 'MobileNetV2':
            tr_width, tr_height = (192, 192)
        else:
            tr_width, tr_height = int(args.trimming_size[0]), int(args.trimming_size[1])

        trimming = not (im_width <= tr_width and im_height <= tr_height)

        if args.center:
            trimming_data = TrimmingData((((im_width - tr_width) / 2), ((im_height - tr_height) / 2)), (tr_width, tr_height), trimming)
        else:
            trimming_data = TrimmingData(args.anchor_point, args.trimming_size, trimming)

        # img = imageio.imread(image_path)
        file_name = os.path.basename(image_path)
        position = trimming_data.position
        size = trimming_data.size
        rect = im[int(position[1]):int(position[1]) + size[1], int(position[0]):int(position[0]) + size[0]]
        imageio.imwrite(os.path.join(save_path, file_name), rect)

        if args.layer != 18:
            layer = args.layer
        elif args.nn in ['vgg']:
            layer = 18
        elif args.nn in ['MobileNet', 'MobileNetV2']:
            layer = 64
        else:
            layer = args.layer

        model = NoveltyDetector(nth_layer=layer, nn_name=args.nn, detector_name=args.detector, pool=args.pool, pca_n_components=args.pca)
        model.load(args.joblib)

        if args.i2c_output:
            import smbus
            import time

            # I2C GPIO address for RasPi is 1
            bus = smbus.SMBus(1)
            # This address shoud be same as in the Arduino.
            SLAVE_ADDRESS = 0x04

        score = self.predict(image_paths, model)[0]
        if score >= args.threshold:
            print('良品 スコア：', score)
            if args.i2c_output:
                bus.write_byte(SLAVE_ADDRESS, ord('1'))
            judge = True
        else:
            print('不良品です　スコア：', score)
            if args.i2c_output:
                bus.write_byte(SLAVE_ADDRESS, ord('0'))
            judge = False

        dic = {
            "result": {
                "judge": judge,
                "score": float(score)
            },
        }

        return json.dumps(dic)

        os.remove(os.path.join('captured_image/tmp', file_name))

    def execute_cmdline(self):
        parser = argparse.ArgumentParser()

        parser.add_argument('-p', '--path',
                            default=None,
                            help='''path to image file like testimages/campbelle/test/OK/soup_28.jpg.''',
                            type=str)

        parser.add_argument('-ap', '--anchor_point',
                            default=(0, 0),
                            help='''explanation''',
                            type=coords)

        parser.add_argument('-ts', '--trimming_size',
                            default=(192, 192),
                            help='''(width, height)''',
                            type=coords)

        parser.add_argument('-t', '--threshold',
                            default=-0.5,
                            help='Threshold to split scores of predicted items. Default is -0.5',
                            type=float)

        parser.add_argument('-n', '--nn',
                            nargs='?',
                            default='vgg',
                            help='''Select neural network model among Xception, ResNet(Default),
                                InceptionV3, InceptionResNetV2, MobileNet, MobileNetV2, DenseNet, NASNet''',
                            type=str)

        parser.add_argument('-l', '--layer',
                            nargs='?',
                            default=18,
                            help='Select which layer to use as feature. Less channels work better.',
                            type=int)

        parser.add_argument('-jl', '--joblib',
                            default='learned_weight/sample.joblib',
                            help='select .joblib file',
                            type=str)

        parser.add_argument('-d', '--detector',
                            default='lof',
                            help='Select novelty detector among RobustCovariance, IsolationForest, LocalOutlierFactor, ABOD, kNN',
                            type=str)

        parser.add_argument('-pl', '--pool',
                            default=None,
                            type=str)
        parser.add_argument('-pca', '--pca',
                            type=int,
                            default=None)

        parser.add_argument('-c', '--center',
                            action='store_true')

        parser.add_argument('-cam', '--camera',
                            action='store_true')

        parser.add_argument('-f', '--fastmode',
                            action='store_true')

        parser.add_argument('-i2c_input', '--i2c_input',
                            action='store_true')

        parser.add_argument('-i2c_output', '--i2c_output',
                            action='store_true')

        parser.add_argument('-ci', '--camera_id',
                            default=0,
                            type=int)

        parser.add_argument('-s', '--size',
                            default=(192, 192),
                            help=''''(width, height)''',
                            type=coords)

        parser.add_argument('-g', '--camera_guide',
                            action='store_true',
                            help='''enable camera guide''', )

        parser.add_argument('-m', '--mirror',
                            action='store_true',
                            help='''enable mirror mode''', )

        parser.add_argument('-o', '--once',
                            action='store_true',
                            help='''inspect only once''', )

        args = parser.parse_args()
        
        if args.fastmode:
            print('[INFO] 単一簡易検査モードが有効になりました。')
            self.inspection(args)
        elif args.once:
            print('[INFO] 単一検査モードが有効になりました。')
            result = self.inspection(args)
            return result
        elif args.i2c_input:
            print('[INFO] I2C モードが有効になりました。')
            import smbus2
            import time
            while True:
                # I2C GPIO address for RasPi is 1
                bus = smbus.SMBus(1)
                # This address shoud be same as in the Arduino.
                SLAVE_ADDRESS = 0x04
                while True:
                    try:
                        result = bus.read_i2c_block_data(SLAVE_ADDRESS, 1, 1)        
                        break
                    except OSError:
                        pass
                if result[0] == 1:
                    self.inspection(args)
                    print('[INFO] 次の信号を待ち受けています...')
                    continue
                elif result[0] == 2:
                    break
                else:
                    continue
        else:
            print('[INFO] 連続モードが有効になりました。')
            while True:
                inputtext = input('start or exit (s or e): ')

                if inputtext in ['exit', 'e']:
                    break
                elif inputtext in ['start', 's']:
                    self.inspection(args)
                    continue
                else:
                    print('try again')
                    continue


if __name__ == '__main__':
    inspector = SDTestInspector()
    result = inspector.execute_cmdline()  # json
    print(result)
