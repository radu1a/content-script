from Utility import Utility
import asyncio


class Story:
    @staticmethod
    def create_story(
            text,
            audio_path,
            srt_path,
            bg_videos_dir,
            full_bg_path,
            final_path,
            concat_helper_path
    ):
        print("TTS...")
        asyncio.run(Utility.text_to_speech(text, audio_path))

        print("Concatenating background videos...")
        Utility.concatenate_videos(bg_videos_dir, concat_helper_path, full_bg_path)

        print("Creating subtitles...")
        transcription = Utility.transcribe_audio(audio_path)
        Utility.generate_srt(transcription, srt_path)

        print("Merging audio video subtitles...")
        Utility.merge_audio_video_subtitles(audio_path, full_bg_path, srt_path, final_path)
