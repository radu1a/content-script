import subprocess
import ffmpeg
import yt_dlp
import edge_tts
import os
import datetime
import whisper
import srt


class Utility:
    @staticmethod
    def stack_vertically(top_half, bottom_half, output):
        ffmpeg_command = [
            "ffmpeg",
            "-i", top_half,
            "-stream_loop", "2", "-i", bottom_half,
            "-filter_complex",
            "[0:v]scale=2112:-1,crop=1920:ih[v0];"
            "[1:v]scale=1920:-1[v1];"
            "[v0][v1]vstack=inputs=2[v]",
            "-map", "[v]",
            "-map", "0:a?",
            "-shortest",
            "-c:v", "h264_nvenc",
            "-preset", "p2",
            "-rc", "vbr_hq",
            "-cq", "21",
            "-maxrate", "12M",
            "-bufsize", "16M",
            "-c:a", "aac",
            "-b:a", "192k",
            "-y",  # Overwrite output
            output
        ]
        try:
            subprocess.run(ffmpeg_command, check=True)
        except ffmpeg.Error as e:
            print('Error running ffmpeg command:')
            print(e.stderr)

    @staticmethod
    def split_video(input_video_path, output_video_path_base, max_duration):
        output_video_path_base = output_video_path_base.split(".")[0]

        video_info = ffmpeg.probe(input_video_path)
        total_duration = float(video_info['format']['duration'])

        output_video_path_list = []

        if total_duration < max_duration:
            return [output_video_path_base + ".mp4"]

        i = 2
        while True:
            part_duration = total_duration / i
            if part_duration < max_duration:
                nr_parts = i
                break
            i += 1

        for i in range(nr_parts):
            output_path = f"{output_video_path_base}_part{i + 1}.mp4"
            output_video_path_list.append(output_path)

            start_time = i * part_duration

            cmd = [
                "ffmpeg",
                "-ss", str(start_time),  # Start time
                "-i", input_video_path,  # Input file
                "-t", str(max_duration),  # Duration
                "-c", "copy",  # No re-encoding
                "-avoid_negative_ts", "make_zero",  # Avoid weird timestamps
                "-y",  # Overwrite
                output_path
            ]

            subprocess.run(cmd, check=True)

        return output_video_path_list

    @staticmethod
    def download_video(download_path, yt_url):
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': download_path,
            'merge_output_format': 'mp4',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([yt_url])

    @staticmethod
    async def text_to_speech(text, audio_path):
        tts = edge_tts.Communicate(text, "en-US-GuyNeural", rate="+23%")
        await tts.save(audio_path)

    @staticmethod
    def re_encode_video(video_path):
        split = video_path.split(".")
        split[0] += "_encoded."

        output_path = split[0] + split[1]
        ffmpeg_command = [
            "ffmpeg",
            "-y",  # Overwrite output if exists
            "-i", video_path,
            "-vf", "scale=1920:1080,fps=30",  # Uniform resolution & frame rate
            "-c:v", "h264_nvenc",  # Use GPU (NVENC) for video encoding
            "-preset", "fast",  # Encoding speed/quality trade-off
            "-cq", "23",  # Constant quality (lower = better)
            "-b:v", "5M",  # Target bitrate (optional)
            "-c:a", "aac",  # Re-encode audio to AAC
            "-b:a", "192k",  # Audio bitrate
            output_path
        ]

        try:
            subprocess.run(ffmpeg_command, check=True)
            print("Videos re-encoded successfully!")
            os.remove(video_path)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    @staticmethod
    def concatenate_videos(video_dir_path, helper_file_path, video_output_path):
        for filename in os.listdir(video_dir_path):
            file_path = os.path.join(video_dir_path, filename)
            Utility.re_encode_video(file_path)

        with open(helper_file_path, "w") as f:
            for filename in os.listdir(video_dir_path):
                file_path = os.path.join(video_dir_path, filename)
                f.write(f"file '{file_path}'\n")

        ffmpeg_command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", helper_file_path,
            "-c", "copy",
            video_output_path
        ]

        try:
            subprocess.run(ffmpeg_command, check=True)
            print("Videos concatenated successfully!")
            os.remove(helper_file_path)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    @staticmethod
    def transcribe_audio(audio_path):
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, word_timestamps=True)
        return result['segments']

    @staticmethod
    def generate_srt(transcription_param, output_srt_path):
        subtitles = []
        index = 1

        for segment in transcription_param:
            for word_item in segment['words']:
                start_time = datetime.timedelta(seconds=word_item['start'])
                end_time = datetime.timedelta(seconds=word_item['end'])

                subtitles.append(srt.Subtitle(
                    index=index,
                    start=start_time,
                    end=end_time,
                    content=word_item['word'].strip()
                ))
                index += 1

        with open(output_srt_path, 'w', encoding='utf-8') as f:
            f.write(srt.compose(subtitles))

    @staticmethod
    def merge_audio_video_subtitles(audio_path, background_video_path, srt_path, output_video_path):
        srt_path_split = srt_path.split(":", 1)
        srt_path_split[0] += "\\:"
        srt_path = srt_path_split[0] + srt_path_split[1]

        audio_info = ffmpeg.probe(audio_path)
        audio_duration = float(audio_info['format']['duration'])

        ffmpeg_command = [
            "ffmpeg",
            "-stream_loop", "-1",
            "-t", f"{audio_duration}",
            "-i", background_video_path,
            "-i", audio_path,
            "-filter_complex",
            f"[0:v]scale=1920:1080,subtitles='{srt_path}':force_style='Alignment=10,"
            "FontName=Verdana,FontSize=40,Bold=1,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,Outline=1,Shadow=0'[v1]",
            "-map", "[v1]",
            "-map", "1:a",
            "-c:v", "h264_nvenc",
            "-preset", "p5",
            "-rc", "vbr_hq",
            "-cq", "21",
            "-maxrate", "10M",
            "-bufsize", "12M",
            "-shortest",
            output_video_path
        ]

        try:
            subprocess.run(ffmpeg_command, check=True)
        except ffmpeg.Error as e:
            print('Error running ffmpeg command:')
            print(e.stderr)

