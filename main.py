import streamlit as st
import yt_dlp
import os
from moviepy import *

# Initialize session state variables if not set
if 'downloaded_video' not in st.session_state:
    st.session_state["downloaded_video"] = None
if 'trimmed_video' not in st.session_state:
    st.session_state["trimmed_video"] = None

# Set the correct FFmpeg path (update this based on the output of 'which ffmpeg')
ffmpeg_path = "/opt/homebrew/bin/ffmpeg"  # Replace with your actual ffmpeg path

# Set page config with favicon
st.set_page_config(
    page_title="YouTube to MP4/MP3 Converter",
    page_icon=":hearts:"  # Replace with the path to your favicon file
)

def download_youtube_video(youtube_url, format):
    output_template = '%(id)s.%(ext)s'
    ydl_opts = {
        'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': output_template,
        'ffmpeg_location': ffmpeg_path,
    }
    
    if format == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif format == 'mp4':
        # Using merge_output_format ensures the final container is mp4.
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            if 'entries' in info:
                # Playlist: take the first video
                entry = info['entries'][0]
                if entry.get('title') is None:
                    entry['title'] = entry.get('id', 'video')
                file_path = ydl.prepare_filename(entry)
            else:
                if info.get('title') is None:
                    info['title'] = info.get('id', 'video')
                file_path = ydl.prepare_filename(info)
        
        if format == 'mp3':
            file_path = os.path.splitext(file_path)[0] + '.mp3'
        elif format == 'mp4':
            file_path = os.path.splitext(file_path)[0] + '.mp4'
        
        st.info(f"File downloaded to: {file_path}")
        return file_path
    except Exception as e:
        st.error(f"Error downloading video: {str(e)}")
        return None

def trim_video(file_path, start_time, end_time):
    try:
        clip = VideoFileClip(file_path)
        trimmed_clip = clip.subclip(start_time, end_time)
        base, ext = os.path.splitext(file_path)
        output_path = base + '_trimmed.mp4'
        trimmed_clip.write_videofile(output_path, codec="libx264")
        clip.close()
        trimmed_clip.close()
        st.success(f"Trimmed video saved to: {output_path}")
        return output_path
    except Exception as e:
        st.error(f"Error trimming video: {str(e)}")
        return None

st.title('YouTube to MP4/MP3 Converter')

youtube_url = st.text_input('Enter YouTube Video URL:')
format_option = st.selectbox('Select format:', ('mp4', 'mp3'))

# Convert button logic
if st.button('Convert'):
    if youtube_url:
        with st.spinner('Processing...'):
            file_path = download_youtube_video(youtube_url, format_option)
            if file_path:
                # Store the downloaded file path in session state
                st.session_state["downloaded_video"] = file_path
                st.success('Conversion completed!')
                st.write(f'File: {file_path}')
                if format_option == 'mp4':
                    abs_video_path = os.path.abspath(file_path)
                    if os.path.exists(abs_video_path):
                        with open(abs_video_path, "rb") as f:
                            st.video(f.read(), format="video/mp4")
                    else:
                        st.error(f"Video file not found: {abs_video_path}")
                else:
                    abs_audio_path = os.path.abspath(file_path)
                    if os.path.exists(abs_audio_path):
                        with open(abs_audio_path, "rb") as f:
                            st.audio(f.read(), format="audio/mp3")
                    else:
                        st.error(f"Audio file not found: {abs_audio_path}")
            else:
                st.error('Failed to process the video.')
    else:
        st.error('Please enter a YouTube video URL.')

# Trim video section - displayed if a video was successfully downloaded
if st.session_state["downloaded_video"]:
    st.markdown("---")
    st.subheader("Edit Video")
    start_time = st.number_input("Enter start time (in seconds):", min_value=0.0, value=0.0, step=0.1)
    end_time = st.number_input("Enter end time (in seconds):", min_value=0.0, value=10.0, step=0.1)
    if st.button("Trim Video"):
        downloaded_file = st.session_state["downloaded_video"]
        trimmed_file = trim_video(downloaded_file, start_time, end_time)
        if trimmed_file:
            st.session_state["trimmed_video"] = trimmed_file
            st.experimental_rerun()
    # Persistent display: if a trimmed video exists, show it
    if st.session_state["trimmed_video"]:
        abs_trimmed_path = os.path.abspath(st.session_state["trimmed_video"])
        if os.path.exists(abs_trimmed_path):
            with open(abs_trimmed_path, "rb") as f:
                st.video(f.read(), format="video/mp4")
        else:
            st.error(f"Trimmed video file not found: {abs_trimmed_path}")
