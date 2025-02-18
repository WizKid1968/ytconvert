import streamlit as st
import yt_dlp
import os
from moviepy.editor import VideoFileClip

# Set the correct FFmpeg path (update this based on the output of 'which ffmpeg')
ffmpeg_path = "/opt/homebrew/bin/ffmpeg"  # Replace with your actual ffmpeg path

# Set page config with favicon
st.set_page_config(
    page_title="YouTube to MP4/MP3 Converter",
    page_icon=":hearts:"  # Replace with the path to your favicon file
)

def download_youtube_video(youtube_url, format):
    output_template = '%(title)s.%(ext)s'
    ydl_opts = {
        'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'ffmpeg_location': ffmpeg_path,
    }
    
    if format == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            if 'entries' in info:
                # Playlist: take the first video
                file_path = ydl.prepare_filename(info['entries'][0])
            else:
                # Single video
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

if st.button('Convert'):
    if youtube_url:
        with st.spinner('Processing...'):
            file_path = download_youtube_video(youtube_url, format_option)
            if file_path:
                st.success('Conversion completed!')
                st.write(f'File: {file_path}')
                if format_option == 'mp4':
                    st.video(file_path)
                    st.markdown("---")
                    st.subheader("Edit Video")
                    start_time = st.number_input("Enter start time (in seconds):", min_value=0.0, value=0.0, step=0.1)
                    end_time = st.number_input("Enter end time (in seconds):", min_value=0.0, value=10.0, step=0.1)
                    if st.button("Trim Video"):
                        trimmed_file = trim_video(file_path, start_time, end_time)
                        if trimmed_file:
                            st.video(trimmed_file)
                else:
                    st.audio(file_path)
            else:
                st.error('Failed to process the video.')
    else:
        st.error('Please enter a YouTube video URL.')
