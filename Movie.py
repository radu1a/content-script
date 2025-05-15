from Utility import Utility


class Movie:
    @staticmethod
    def create_movie(
            yt_url,
            full_video_path,
            background_video_path,
            stacked_path,
    ):
        print("Downloading...")
        Utility.download_video(full_video_path, yt_url)

        print("Stacking vertically...")
        Utility.stack_vertically(full_video_path, background_video_path, stacked_path)

        print("Splitting video...")
        video_path_list = Utility.split_video(stacked_path, stacked_path, 240)

        print("SUCCESS")
