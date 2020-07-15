"""
Download youtube live video automatically
"""
import os
import shutil
import cv2
import urllib
import m3u8
import streamlink
import argparse
from datetime import datetime

log = open(f'./log_{datetime.now().strftime("%Y%m%d-%H%M%S")}.txt', "w")


class YouTube_stream():
    def __init__(self, opt):
        self.url = opt.url
        self.filename = opt.CCTV
        self.chunks = opt.chunks
        self.step = opt.step
        self.ext = opt.ext
        self.dir_videos = opt.dir_videos
        self.dir_frames = opt.dir_frames
        self.dontsv_frames = opt.dontsv_frames
        self.save_videos = opt.save_videos

    def mk_folder(self):
        """
        Create dir_videos, dir_frames
        create /tmp
        """
        os.makedirs(self.dir_videos, exist_ok=True)

        if self.dontsv_frames is not True:
            os.makedirs(self.dir_frames, exist_ok=True)

    def del_folder(self):
        """
        Delete dir_videos if self.save_videos is False
        """
        if self.save_videos is not True:
            # os.removedirs(self.dir_videos)
            shutil.rmtree(self.dir_videos, ignore_errors=True)

    def get_stream(self):
        """
        Get upload chunk url
        url: 'http://www.youtube.com/**********'
            youtube live address
        """
        streams = streamlink.streams(self.url)
        stream_url = streams["best"]

        m3u8_obj = m3u8.load(stream_url.args['url'])
        return m3u8_obj.segments[0]

    def video2frames(self, video):
        """
        Convert video to frames
        video: 入力ビデオの保存場所
        dir_frames: 出力フレームの保存場所
        filename: 出力フレームの命名仕方
        step: 1秒何フレームを出力する（30/step）
        ext: 出力フレーム、画像の格式
        """
        path_video = os.path.join(self.dir_videos, video)
        cap = cv2.VideoCapture(path_video)
        if not cap.isOpened():
            raise IOError("入力ビデオが開けない、或いは存在しない")

        base_path = self.dir_frames + '/'
        # print(base_path)

        # 入力ビデオの総フレーム数の桁数
        digit = len(str(int(cap.get(cv2.CAP_PROP_FRAME_COUNT))))

        frame_id = 0
        while True:
            ret, frame = cap.read()
            frame_id += 1
            if not ret:
                break
            if frame_id % self.step != 0:
                continue
            else:
                cv2.imwrite('{}{}.{}'.format(base_path,
                                             video[:-3]+'_'+str(frame_id).zfill(digit),
                                             self.ext), frame)
        return

    def dl_stream(self):
        """
        Download each chunks
        url: 'http://www.youtube.com/**********'
            youtube live address
        filename: str
            prefix of downloaded files name
        chunks: int
            youtube video is uploaded by chunks, if each chunk has 2s,
            it means that download 2s * chunks of stream.
        dir_videos: str(path)
            all the downloaded videos will be saved to this path
        """
        self.mk_folder()
        ls_streams = []
        pre_time_stamp = 0
        for i in range(self.chunks+1):
            stream_segment = self.get_stream()
            cur_time_stamp = \
                stream_segment.program_date_time.strftime("%Y%m%d-%H%M%S")

            if pre_time_stamp == cur_time_stamp:
                continue
            else:
                print(cur_time_stamp)
                file = open(self.dir_videos + "/"
                            + self.filename + '_'
                            + str(cur_time_stamp)
                            + '.ts', 'ab+')
                with urllib.request.urlopen(stream_segment.uri) as response:
                    html = response.read()
                    file.write(html)
                    file.close()
                pre_time_stamp = cur_time_stamp
                ls_streams.append(str(cur_time_stamp))
                log.write(f"YoutTube Live timeline: {str(cur_time_stamp)}\n")

            video = self.filename + '_' + ls_streams[-1] + '.ts'
            if self.dontsv_frames is not True:
                # video = self.get_video()
                self.video2frames(video)
            if self.save_videos is not True:
                os.remove(os.path.join(self.dir_videos, video))
                print("{} is deleted.".format(video))

        self.del_folder()


if __name__ == '__main__':
    # example: url = "https://www.youtube.com/watch?v=2U3JnFbD-es"
    parser = argparse.ArgumentParser(
        usage="python get_yt_live.py \\\n"
              "     --url website of youtube live \\\n"
              "     --CCTV name of youtube live, or Nothing \\\n"
              "     --chunks length of live video 15 \\\n"
              "     --step 10 \\\n"
              "     --ext jpg \\\n"
              "     --dir_videos path/to/folder for saving videos ./output \\\n"
              "     --dir_frames path/to/folder for saving frames ./frames \\\n"
              "     --dontsv_frames \\\n"
              "     --save_videos"
    )
    parser.add_argument('--url', type=str,
                        default='https://www.youtube.com/watch?v=2U3JnFbD-es',
                        help='https://www.youtube.com/*****')
    parser.add_argument('--CCTV', type=str, default='live',
                        help='CCTVカメラの名前/場所')
    parser.add_argument('--chunks', type=int, default=15,
                        help='ビデオの長さ')
    parser.add_argument('--step', type=int, default=10,
                        help='10フレーム毎で画像作成')
    parser.add_argument('--ext', type=str, default='jpg',
                        help='画像ファイル形式')
    parser.add_argument('--dir_videos', type=str, default='./output',
                        help='ビデオの保存場所')
    parser.add_argument('--dir_frames', type=str, default='./frames',
                        help='フレーム・画像の保存場所')
    parser.add_argument('--dontsv_frames', action='store_true',
                        help='フレーム・画像を作成するか否か')
    parser.add_argument('--save_videos', action='store_true',
                        help='ビデオを保存するか否か')
    opt = parser.parse_args()

    for arg in vars(opt):
        log.write(f"{arg}, {getattr(opt, arg)}\n")
    log.write("==================================================\n")

    get_yt_stream = YouTube_stream(opt)
    get_yt_stream.dl_stream()
