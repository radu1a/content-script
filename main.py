from Movie import Movie
from Story import Story
import asyncio
import os

BASE_PATH = os.getcwd() + "\\"
BASE_PATH = BASE_PATH.replace("\\", "/")


async def start_movie():
    yt_url = input("Youtube URL: ")
    video_id = yt_url.split("=")[1]
    full_video = BASE_PATH + f"movie-aux/initial/{video_id}.mp4"
    background_video = BASE_PATH + "movie-aux/background/active.mp4"
    stacked_video = BASE_PATH + f"movie-aux/final/{video_id}.mp4"

    Movie.create_movie(yt_url, full_video, background_video, stacked_video)


def start_story():
    text_input_path = BASE_PATH + "story-aux/text.txt"

    srt_path = BASE_PATH + "story-aux/helper/subtitles.srt"
    audio_path = BASE_PATH + "story-aux/helper/audio.mp3"
    concat_helper_path = BASE_PATH + "story-aux/helper/file-list.txt"
    full_bg_path = BASE_PATH + "story-aux/helper/full-bg.mp4"

    bg_video_dir = BASE_PATH + "story-aux/bg-videos/"
    final_path = BASE_PATH + "story-aux/final/output.mp4"

    with open(text_input_path, "r") as f:
        text = f.read()

    Story.create_story(text, audio_path, srt_path, bg_video_dir, full_bg_path, final_path, concat_helper_path)


if __name__ == "__main__":
    choice = input("What do you want? (movie/story): ")
    if choice == "movie":
        asyncio.run(start_movie())
    elif choice == "story":
        start_story()
