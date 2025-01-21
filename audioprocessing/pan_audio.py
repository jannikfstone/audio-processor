from pydub import AudioSegment
import matplotlib.pyplot as plt
import click
import os

loudness_difference = 1
section_length = 500

@click.command()
@click.argument("input_file", required=True, type=str)
@click.option("-o", "--output_file", required=False, type=str, help="Output file name")
@click.option("-p", "--plot-speaker", is_flag=True, default=False, help="Show plot of speaker over time")
def pan_audio(input_file, output_file, plot_speaker):
    if output_file is None:
        output_file = os.path.dirname(os.path.abspath(input_file)) + "/PANNED_" + os.path.basename(input_file)
    if input_file[-4:] != ".wav":
        print("Input file must be a .wav file")
        return

    recording = AudioSegment.from_file(input_file, format="wav")
    print("Recording length: ", len(recording) / 1000, " seconds")
    left, right = recording.split_to_mono()
    left_sections = left[::section_length]
    right_sections = right[::section_length]

    speaker_time_series, timestamp_series = [], []
    panned_left = AudioSegment.empty()
    panned_right = AudioSegment.empty()
    last_displayed_progress = -1

    current_timestamp = 0
    for left_section, right_section in zip(left_sections, right_sections):
        if current_timestamp > 30:
            break
        timestamp_series.append(current_timestamp)
        current_timestamp += section_length / 1000
        speaker = get_speaker(left_section, right_section, loudness_difference)
        speaker_time_series.append(get_speaker_numeric_value(speaker))
        panned_left_section, panned_right_section = get_panned_audio(left_section, right_section, speaker)
        panned_left += panned_left_section
        panned_right += panned_right_section
        percentage_processed = current_timestamp / (len(recording) / 1000) * 100
        if int(percentage_processed) % 5 == 0 and int(percentage_processed) != last_displayed_progress:
            print("Processed ", int(percentage_processed), "%")
            last_displayed_progress = int(percentage_processed)

    final_audio = AudioSegment.from_mono_audiosegments(panned_left, panned_right)
    plt.plot(timestamp_series, speaker_time_series)
    plt.ylabel('Speaker')
    plt.xlabel('Time')
    if plot_speaker:
        plt.show()
    final_audio.export(output_file, format="wav")


def get_panned_audio(left, right, speaker):
    if speaker == 'left':
        return left, right - 100
    if speaker == 'right':
        return left - 100, right
    return left, right

def get_speaker(left, right, threshold):
    if left.dBFS - right.dBFS > threshold:
        return "left"
    if right.dBFS - left.dBFS > threshold:
        return "right"
    return "both"

def get_speaker_numeric_value(speaker):
    if speaker == 'left':
        return 1
    if speaker == 'right':
        return -1
    return 0

if __name__ == "__main__":
    pan_audio()
