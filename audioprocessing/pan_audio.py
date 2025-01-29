from pydub import AudioSegment
import click
import os
import time
import datetime
import threading

loudness_difference = 1
section_length = 200
num_threads = 100

@click.command()
@click.argument("input_file", required=True, type=str)
@click.option("-o", "--output_file", required=False, type=str, help="Output file name")
@click.option("-p", "--plot-speaker", is_flag=True, default=False, help="Show plot of speaker over time")
def pan_audio(input_file, output_file, plot_speaker):
    start_time = time.time()
    time_counter = threading.Thread(target=print_elapsed_time, args=(start_time,))
    time_counter.start()

    if output_file is None:
        output_file = os.path.dirname(os.path.abspath(input_file)) + "/PANNED_" + os.path.basename(input_file)
    if input_file[-4:] != ".wav":
        print("Input file must be a .wav file")
        return

    recording = get_audio_segment(input_file)
    final_audio = pan_audio_recursive(recording)
    print("Chunks panned. Exporting to ", output_file)
    print("Length of final audio: ", datetime.timedelta(seconds=(len(final_audio) / 1000)))

    final_audio.export(output_file, format="wav")
    time_counter.do_run = False
    time_counter.join()
    print("Total processing time: ", int(time.time() - start_time) , " seconds")

def pan_audio_recursive(source_audio: AudioSegment):
    segment_length = len(source_audio)
    if segment_length < section_length:
        return pan_audio_chunk(source_audio)

    half_length = segment_length // 2

    t1_target = pan_audio_recursive(source_audio[:half_length])
    t2_target = pan_audio_recursive(source_audio[half_length:])

    return t1_target + t2_target

def pan_audio_chunk(audio: AudioSegment):
    left, right = audio.split_to_mono()
    left_sections = left[::section_length]
    right_sections = right[::section_length]

    panned_left = AudioSegment.empty()
    panned_right = AudioSegment.empty()

    for left_section, right_section in zip(left_sections, right_sections):
        speaker = get_speaker(left_section, right_section, loudness_difference)
        panned_left_section, panned_right_section = get_panned_audio(left_section, right_section, speaker)
        panned_left += panned_left_section
        panned_right += panned_right_section

    final_chunk_audio = AudioSegment.from_mono_audiosegments(panned_left, panned_right)
    # print ("Length of chunk: ", datetime.timedelta(seconds=(len(final_chunk_audio) / 1000)))
    return final_chunk_audio
    # panned_chunks[chunk_index] = final_chunk_audio

def get_panned_audio(left_audio: AudioSegment, right_audio: AudioSegment, speaker: str) -> tuple[AudioSegment, AudioSegment]:
    if speaker == 'left':
        return left_audio, right_audio - 100
    if speaker == 'right':
        return left_audio - 100, right_audio
    return left_audio, right_audio


def get_speaker(left: AudioSegment, right: AudioSegment, threshold: int) -> str:
    if left.dBFS - right.dBFS > threshold:
        return "left"
    if right.dBFS - left.dBFS > threshold:
        return "right"
    return "both"


def get_speaker_numeric_value(speaker: str) -> int:
    if speaker == 'left':
        return 1
    if speaker == 'right':
        return -1
    return 0


def get_audio_segment(file_path: str) -> AudioSegment:
    recording = AudioSegment.from_file(file_path, format="wav")
    recording_length = datetime.timedelta(seconds=(len(recording) / 1000))
    print("Recording length: ", str(recording_length))
    return recording


def print_elapsed_time(start_time):
    t = threading.current_thread()
    while getattr(t, "do_run", True):
        print("Elapsed time: ", int(time.time() - start_time), end="\r")
        time.sleep(1)


def get_chunked_audio(audio: AudioSegment) -> list[AudioSegment]:
    audio_length = len(audio)
    chunk_length = audio_length // num_threads
    print("Calculated chunk length: ", datetime.timedelta(seconds=chunk_length/ 1000))
    print("Number of chunks: ", num_threads)
    return audio[::chunk_length]


if __name__ == "__main__":
    pan_audio()
