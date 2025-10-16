import streamlit as st
import os
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import json
import tempfile
import io
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.oauth2 import service_account
import time

# Konfigurasi
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

st.set_page_config(page_title="YouTube Video Uploader from Drive", page_icon="🎥")

def main():
    st.title("🎥 YouTube Video Uploader from Google Drive")
    st.markdown("---")
    
    # Penjelasan aplikasi
    st.info("""
    **Cara Penggunaan:**
    1. Unggah file `client_secret.json` (YouTube API)
    2. Unggach file `service_account.json` (Google Drive API) *opsional untuk Streamlit Cloud
    3. Masukkan URL folder Google Drive
    4. Pilih video dari folder tersebut
    5. Isi detail video dan upload ke YouTube
    """)
    
    # Upload file credentials
    col1, col2 = st.columns(2)
    
    with col1:
        youtube_secret = st.file_uploader("Unggah YouTube client_secret.json", type=['json'])
    
    with col2:
        drive_secret = st.file_uploader("Unggah Drive service_account.json (opsional)", type=['json'])
    
    if youtube_secret is not None:
        # Simpan file sementara
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            tmp_file.write(youtube_secret.getvalue())
            temp_youtube_secret_path = tmp_file.name
        
        # Input URL Google Drive
        st.markdown("---")
        drive_url = st.text_input("🔗 URL Folder Google Drive", 
                                 "https://drive.google.com/drive/folders/14VH9nzPQkbAsP-2Ju-QR4dMZ75BpN6_E?usp=sharing")
        
        if drive_url:
            try:
                folder_id = extract_folder_id(drive_url)
                if folder_id:
                    st.success(f"Folder ID ditemukan: {folder_id}")
                    
                    # Tampilkan daftar video
                    videos = get_videos_from_drive(folder_id, drive_secret)
                    
                    if videos:
                        selected_video = st.selectbox(
                            "🎬 Pilih Video untuk Diupload",
                            options=videos,
                            format_func=lambda x: x['name']
                        )
                        
                        if selected_video:
                            st.markdown("---")
                            st.subheader("📝 Detail Video YouTube")
                            
                            # Form detail video
                            title = st.text_input("Judul Video", selected_video['name'].split('.')[0])
                            description = st.text_area("Deskripsi Video", "Video diupload dari Google Drive melalui Streamlit App")
                            category = st.selectbox("Kategori", 
                                ["22 - People & Blogs", "23 - Comedy", "24 - Entertainment", 
                                 "25 - News & Politics", "26 - Howto & Style", "27 - Education",
                                 "28 - Science & Technology", "29 - Nonprofits & Activism"],
                                index=0)
                            privacy_status = st.radio("Status Privasi", ["public", "private", "unlisted"])
                            
                            # Progress bar
                            progress_bar = st.empty()
                            status_text = st.empty()
                            
                            # Tombol upload
                            if st.button("📤 Upload ke YouTube", type="primary"):
                                try:
                                    # Download video dari Drive
                                    status_text.text("Mengunduh video dari Google Drive...")
                                    video_content = download_video_from_drive(selected_video['id'], drive_secret)
                                    
                                    if video_content:
                                        # Upload ke YouTube
                                        status_text.text("Mengupload video ke YouTube...")
                                        video_id = upload_video_to_youtube(
                                            temp_youtube_secret_path,
                                            video_content,
                                            selected_video['name'],
                                            title,
                                            description,
                                            category.split(" - ")[0],
                                            privacy_status,
                                            progress_bar,
                                            status_text
                                        )
                                        
                                        if video_id:
                                            st.success("✅ Video berhasil diupload!")
                                            st.markdown(f"**Tonton video Anda:** https://youtu.be/{video_id}")
                                        else:
                                            st.error("❌ Gagal mengupload video ke YouTube")
                                    else:
                                        st.error("❌ Gagal mengunduh video dari Google Drive")
                                        
                                except Exception as e:
                                    st.error(f"Terjadi kesalahan: {str(e)}")
                    else:
                        st.warning("Tidak ada video ditemukan di folder tersebut")
                else:
                    st.error("Tidak dapat mengekstrak Folder ID dari URL")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # Hapus file sementara
        os.unlink(temp_youtube_secret_path)

def extract_folder_id(url):
    """Ekstrak Folder ID dari URL Google Drive"""
    try:
        if "folders/" in url:
            folder_id = url.split("folders/")[1].split("?")[0]
            return folder_id
        return None
    except:
        return None

def get_videos_from_drive(folder_id, drive_secret=None):
    """Dapatkan daftar video dari folder Google Drive"""
    try:
        # Untuk demo, kita akan menggunakan API sederhana
        # Dalam produksi, gunakan PyDrive atau Google Drive API resmi
        
        st.info("🔍 Mengambil daftar video dari folder...")
        
        # Simulasi daftar video (karena autentikasi kompleks di Streamlit Cloud)
        # Anda bisa mengganti ini dengan implementasi API Drive yang sesungguhnya
        
        sample_videos = [
            {"id": "sample1", "name": "video1.mp4", "size": "100MB"},
            {"id": "sample2", "name": "video2.mov", "size": "150MB"},
            {"id": "sample3", "name": "video3.avi", "size": "80MB"}
        ]
        
        return sample_videos
        
    except Exception as e:
        st.error(f"Error mengambil video dari Drive: {str(e)}")
        return []

def download_video_from_drive(file_id, drive_secret=None):
    """Download video dari Google Drive"""
    try:
        # Simulasi download video
        st.info("⬇️ Simulasi download video dari Google Drive...")
        time.sleep(2)  # Simulasi waktu download
        
        # Return dummy content (dalam implementasi nyata, ini akan berisi konten video)
        return b"dummy_video_content"
        
    except Exception as e:
        st.error(f"Error download video: {str(e)}")
        return None

def upload_video_to_youtube(client_secret_path, video_content, filename, title, description, category, privacy_status, progress_bar, status_text):
    """Upload video ke YouTube dengan progress tracking"""
    try:
        st.warning("""
        ⚠️ **PERINGATAN**: Autentikasi YouTube API tidak dapat dilakukan secara penuh di Streamlit Cloud.
        Untuk versi lengkap, jalankan aplikasi ini secara lokal dengan autentikasi OAuth yang benar.
        """)
        
        # Simulasi proses upload
        status_text.text("Simulasi upload ke YouTube...")
        for i in range(100):
            time.sleep(0.05)  # Simulasi waktu upload
            progress_bar.progress(i + 1)
        
        # Return dummy video ID
        return "dQw4w9WgXcQ"  # Rick Roll ID sebagai contoh
        
    except Exception as e:
        st.error(f"Error upload ke YouTube: {str(e)}")
        return None

# Versi implementasi nyata (untuk dijalankan lokal)
def get_videos_from_drive_real(folder_id, drive_secret):
    """Implementasi nyata untuk mengambil video dari Drive"""
    try:
        if drive_secret is not None:
            # Simpan service account file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                tmp_file.write(drive_secret.getvalue())
                service_account_path = tmp_file.name
            
            # Gunakan service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path, scopes=DRIVE_SCOPES)
            
            # Build Drive service
            from googleapiclient.discovery import build
            drive_service = build('drive', 'v3', credentials=credentials)
            
            # Query files in folder
            query = f"'{folder_id}' in parents and (mimeType contains 'video/')"
            results = drive_service.files().list(
                q=query,
                fields="files(id, name, size, mimeType)").execute()
            
            videos = results.get('files', [])
            
            # Hapus file sementara
            os.unlink(service_account_path)
            
            return videos
        else:
            # Fallback ke simulasi
            return get_videos_from_drive(folder_id)
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

def download_video_from_drive_real(file_id, drive_secret):
    """Implementasi nyata untuk download video"""
    try:
        if drive_secret is not None:
            # Simpan service account file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                tmp_file.write(drive_secret.getvalue())
                service_account_path = tmp_file.name
            
            # Gunakan service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path, scopes=DRIVE_SCOPES)
            
            # Build Drive service
            from googleapiclient.discovery import build
            drive_service = build('drive', 'v3', credentials=credentials)
            
            # Download file
            request = drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Hapus file sementara
            os.unlink(service_account_path)
            
            return fh.getvalue()
        else:
            return download_video_from_drive(file_id)
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Informasi setup
def show_setup_info():
    st.sidebar.title("ℹ️ Informasi Setup")
    st.sidebar.markdown("""
    ### Langkah-langkah Setup:
    
    **1. YouTube API:**
    - Buat project di [Google Cloud Console](https://console.cloud.google.com/)
    - Aktifkan YouTube Data API v3
    - Buat OAuth 2.0 credentials
    - Download file `client_secret.json`
    
    **2. Google Drive API:**
    - Aktifkan Google Drive API
    - Buat Service Account credentials
    - Download file `service_account.json`
    
    **3. Folder Google Drive:**
    - Pastikan folder dapat diakses
    - Format URL: `https://drive.google.com/drive/folders/FOLDER_ID`
    
    ### Catatan Penting:
    - Autentikasi penuh tidak berfungsi di Streamlit Cloud
    - Untuk penggunaan nyata, jalankan secara lokal
    """)

# Fungsi untuk upload langsung dari URL (alternatif)
def upload_from_direct_url():
    st.markdown("---")
    st.subheader("📤 Alternatif: Upload dari URL Direct")
    
    video_url = st.text_input("🔗 URL Video Langsung", placeholder="https://drive.google.com/uc?id=FILE_ID")
    
    if video_url:
        st.info("Fitur ini memerlukan implementasi tambahan untuk download dari URL direct")
        # Implementasi download dari URL bisa ditambahkan di sini

if __name__ == "__main__":
    show_setup_info()
    main()
    upload_from_direct_url()
