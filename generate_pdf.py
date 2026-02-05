#!/usr/bin/env python3
import subprocess
import os
import sys
from pathlib import Path

# Add user site-packages to path
sys.path.insert(0, '/Users/amritpalsingh/Library/Python/3.9/lib/python/site-packages')

import whisper
from fpdf import FPDF
from PIL import Image

# Configuration
OUTPUT_DIR = Path("/Users/amritpalsingh/Downloads/video_pdf_output")
VIDEOS = [
    "/Users/amritpalsingh/Downloads/video-58347111-7343-42c6-8f24-b91e031a3a1d.mp4",
    "/Users/amritpalsingh/Downloads/video-2e612f65-2c88-4793-9eba-a35a78e22a79.mp4",
    "/Users/amritpalsingh/Downloads/video-ad564ed9-f448-41dd-9ec8-d792ae6d19ad.mp4",
    "/Users/amritpalsingh/Downloads/video-3f302f9d-3ccd-4c4a-ae4b-97cb7a3c51c6.mp4",
]
FRAMES_PER_VIDEO = 5  # Extract 5 key frames per video

def get_video_duration(video_path):
    """Get video duration in seconds."""
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def extract_frames(video_path, output_dir, num_frames=5):
    """Extract frames at regular intervals from video."""
    video_name = Path(video_path).stem
    frames_dir = output_dir / video_name
    frames_dir.mkdir(exist_ok=True)
    
    duration = get_video_duration(video_path)
    interval = duration / (num_frames + 1)
    
    frame_paths = []
    for i in range(1, num_frames + 1):
        timestamp = interval * i
        output_path = frames_dir / f"frame_{i:02d}.jpg"
        cmd = [
            'ffmpeg', '-y', '-ss', str(timestamp), '-i', video_path,
            '-vframes', '1', '-q:v', '2', str(output_path)
        ]
        subprocess.run(cmd, capture_output=True)
        if output_path.exists():
            frame_paths.append(output_path)
    
    return frame_paths

def transcribe_video(video_path, model):
    """Transcribe video audio using Whisper."""
    print(f"  Transcribing: {Path(video_path).name}")
    result = model.transcribe(video_path, language="en")
    return result["text"]

def create_pdf(video_data, output_path):
    """Create PDF with frames and transcriptions."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    for idx, (video_path, frames, transcript) in enumerate(video_data, 1):
        video_name = Path(video_path).name
        
        # Add title page for each video
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"Video {idx}: {video_name[:40]}...", ln=True)
        pdf.ln(5)
        
        # Add frames
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Key Frames:", ln=True)
        
        for i, frame_path in enumerate(frames):
            if i % 2 == 0 and i > 0:
                pdf.add_page()
            
            try:
                # Resize image to fit
                img = Image.open(frame_path)
                img_width, img_height = img.size
                max_width = 180
                ratio = max_width / img_width
                new_height = int(img_height * ratio)
                if new_height > 100:
                    new_height = 100
                    ratio = new_height / img_height
                    max_width = int(img_width * ratio)
                
                pdf.image(str(frame_path), x=15, w=max_width)
                pdf.ln(5)
            except Exception as e:
                print(f"    Warning: Could not add frame {frame_path}: {e}")
        
        # Add transcription
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "Transcription:", ln=True)
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 10)
        
        # Handle text encoding
        clean_transcript = transcript.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, clean_transcript)
        pdf.ln(10)
    
    pdf.output(output_path)

def main():
    print("Loading Whisper model (this may take a moment)...")
    model = whisper.load_model("base")
    
    video_data = []
    
    for i, video_path in enumerate(VIDEOS, 1):
        print(f"\nProcessing video {i}/{len(VIDEOS)}: {Path(video_path).name}")
        
        # Extract frames
        print("  Extracting frames...")
        frames = extract_frames(video_path, OUTPUT_DIR, FRAMES_PER_VIDEO)
        
        # Transcribe
        transcript = transcribe_video(video_path, model)
        
        video_data.append((video_path, frames, transcript))
    
    # Generate PDF
    print("\nGenerating PDF...")
    output_pdf = OUTPUT_DIR / "video_learning_notes.pdf"
    create_pdf(video_data, str(output_pdf))
    
    print(f"\n✅ PDF created: {output_pdf}")

if __name__ == "__main__":
    main()
