import streamlit as st
import os
import json
import tempfile
import time
import urllib.parse
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

st.set_page_config(page_title="YouTube Video Uploader", page_icon="🎥")

# Konfigurasi OAuth
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 
                  'https://www.googleapis.com/auth/youtube']

# Redirect URI untuk aplikasi Streamlit
REDIRECT_URI = "https://ytupload.streamlit.app/"

def main():
    st.title("🎥 YouTube Video Uploader")
    st.markdown("---")
    
    # Inisialisasi session state
    if 'credentials' not in st.session_state:
        st.session_state.credentials = None
    if 'channels' not in st.session_state:
        st.session_state.channels = []
    if 'selected_channel' not in st.session_state:
        st.session_state.selected_channel = None
    if 'auth_state' not in st.session_state:
        st.session_state.auth_state = None
    
    # Tab navigation
    tab1, tab2, tab3 = st.tabs(["🔑 Autentikasi", "📺 Pilih Channel", "📤 Upload Video"])
    
    with tab1:
        authentication_tab()
    
    with tab2:
        channel_selection_tab()
    
    with tab3:
        upload_video_tab()

def authentication_tab():
    st.header("🔑 Autentikasi YouTube")
    
    st.info(f"""
    **Langkah Autentikasi:**
    1. Pastikan `client_secret.json` sudah terdaftar dengan redirect URI: `{REDIRECT_URI}`
    2. Unggah file `client_secret.json` dari Google Cloud Console
    3. Klik tombol "🔐 Autentikasi dengan YouTube"
    4. Ikuti proses login dan izinkan akses
    """)
    
    # Upload client_secret.json
    client_secret_file = st.file_uploader("Unggah client_secret.json", type=['json'])
    
    if client_secret_file is not None:
        # Simpan file sementara
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
            tmp_file.write(client_secret_file.getvalue())
            st.session_state.client_secret_path = tmp_file.name
        
        st.success("✅ File client_secret.json berhasil diunggah!")
        
        # Tombol autentikasi
        if st.button("🔐 Autentikasi dengan YouTube", type="primary"):
            start_oauth_flow()
    
    # Handle OAuth callback
    handle_oauth_callback()
    
    # Tampilkan status autentikasi
    if st.session_state.credentials:
        st.success("✅ Anda sudah terautentikasi!")
    else:
        st.warning("⚠️ Anda belum terautentikasi")

def start_oauth_flow():
    """Mulai proses OAuth flow dengan redirect URI yang benar"""
    try:
        # Baca client secret
        with open(st.session_state.client_secret_path, 'r') as f:
            client_config = json.load(f)
        
        # Modifikasi redirect URI dalam client config
        if 'web' in client_config:
            client_config['web']['redirect_uris'] = [REDIRECT_URI]
        elif 'installed' in client_config:
            # Untuk installed apps, kita tetap bisa menggunakan redirect
            pass
        
        # Buat OAuth flow
        flow = Flow.from_client_config(
            client_config,
            scopes=YOUTUBE_SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        # Simpan flow di session state
        st.session_state.oauth_flow = flow
        
        # Dapatkan authorization URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Simpan state untuk verifikasi
        st.session_state.auth_state = state
        
        st.markdown(f"**Klik link berikut untuk autentikasi:**")
        st.markdown(f"[🔐 Login ke YouTube]({auth_url})")
        st.info(f"""
        **Instruksi:**
        1. Klik link di atas untuk login
        2. Setelah login dan memberi izin, Anda akan dialihkan ke URL dengan kode
        3. Salin URL lengkap setelah redirect dan masukkan di bawah
        """)
        
        # Input untuk URL setelah redirect
        redirect_url = st.text_input("Masukkan URL lengkap setelah redirect:")
        
        if redirect_url:
            st.session_state.redirect_url = redirect_url
            st.experimental_rerun()
            
    except Exception as e:
        st.error(f"❌ Error autentikasi: {str(e)}")

def handle_oauth_callback():
    """Handle OAuth callback dari URL"""
    try:
        # Cek jika ada redirect URL yang disimpan
        if 'redirect_url' in st.session_state and st.session_state.redirect_url:
            redirect_url = st.session_state.redirect_url
            
            # Parse URL untuk mendapatkan kode
            parsed_url = urllib.parse.urlparse(redirect_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Dapatkan kode dan state
            auth_code = query_params.get('code', [None])[0]
            state = query_params.get('state', [None])[0]
            
            if auth_code:
                # Verifikasi state
                if state == st.session_state.auth_state:
                    # Tukar kode dengan credentials
                    flow = st.session_state.oauth_flow
                    flow.fetch_token(code=auth_code)
                    st.session_state.credentials = flow.credentials
                    
                    # Hapus URL redirect yang sudah diproses
                    del st.session_state.redirect_url
                    del st.session_state.auth_state
                    
                    st.success("✅ Autentikasi berhasil!")
                    st.experimental_rerun()
                else:
                    st.error("❌ State tidak sesuai. Kemungkinan ada masalah dengan autentikasi.")
            else:
                st.error("❌ Tidak dapat mengekstrak kode autentikasi dari URL")
                
    except Exception as e:
        st.error(f"❌ Error handling callback: {str(e)}")

def channel_selection_tab():
    st.header("📺 Pilih Channel YouTube")
    
    if not st.session_state.credentials:
        st.warning("⚠️ Silakan autentikasi terlebih dahulu di tab Autentikasi")
        return
    
    if st.button("🔄 Refresh Daftar Channel"):
        get_youtube_channels()
    
    if st.session_state.channels:
        st.success(f"✅ Ditemukan {len(st.session_state.channels)} channel")
        
        # Buat daftar channel untuk selectbox
        channel_options = []
        channel_dict = {}
        
        for channel in st.session_state.channels:
            channel_title = channel.get('snippet', {}).get('title', 'Unknown Channel')
            channel_id = channel.get('id', '')
            option_text = f"{channel_title} (ID: {channel_id})"
            channel_options.append(option_text)
            channel_dict[option_text] = channel
        
        # Pilih channel
        selected_option = st.selectbox(
            "Pilih channel untuk upload:",
            options=channel_options,
            index=0
        )
        
        # Tampilkan detail channel
        selected_channel = channel_dict[selected_option]
        st.session_state.selected_channel = selected_channel
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Channel Details")
            st.write(f"**Nama:** {selected_channel.get('snippet', {}).get('title', 'N/A')}")
            st.write(f"**ID:** {selected_channel.get('id', 'N/A')}")
            st.write(f"**Deskripsi:** {selected_channel.get('snippet', {}).get('description', 'N/A')}")
        
        with col2:
            st.subheader("Statistik")
            stats = selected_channel.get('statistics', {})
            st.write(f"**Subscriber:** {stats.get('subscriberCount', 'N/A')}")
            st.write(f"**Video:** {stats.get('videoCount', 'N/A')}")
            st.write(f"**Views:** {stats.get('viewCount', 'N/A')}")
        
        st.success("✅ Channel siap digunakan untuk upload!")
        
    else:
        st.info("Klik 'Refresh Daftar Channel' untuk memuat channel Anda")

def get_youtube_channels():
    """Dapatkan daftar channel YouTube"""
    try:
        if not st.session_state.credentials:
            st.warning("❌ Tidak ada credentials")
            return
            
        youtube = build('youtube', 'v3', credentials=st.session_state.credentials)
        
        # Dapatkan daftar channel
        request = youtube.channels().list(
            part='snippet,contentDetails,statistics',
            mine=True
        )
        response = request.execute()
        
        st.session_state.channels = response.get('items', [])
        
        if not st.session_state.channels:
            st.warning("Tidak ada channel ditemukan. Pastikan Anda memiliki channel YouTube.")
            
    except Exception as e:
        st.error(f"Error mengambil channel: {str(e)}")

def upload_video_tab():
    st.header("📤 Upload Video ke YouTube")
    
    if not st.session_state.credentials:
        st.warning("⚠️ Silakan autentikasi terlebih dahulu di tab Autentikasi")
        return
    
    if not st.session_state.selected_channel:
        st.warning("⚠️ Silakan pilih channel di tab Pilih Channel")
        return
    
    st.success(f"✅ Siap upload ke channel: {st.session_state.selected_channel.get('snippet', {}).get('title', 'N/A')}")
    
    # Input video (simulasi untuk demo)
    st.info("🔍 Untuk demo, gunakan simulasi upload. Dalam implementasi nyata, Anda bisa menghubungkan dengan Google Drive.")
    
    # Simulasi file video
    video_file = st.file_uploader("Pilih video untuk diupload (simulasi)", type=['mp4', 'avi', 'mov', 'mkv'])
    
    # Detail video
    st.subheader("📝 Detail Video")
    title = st.text_input("Judul Video", "Video Baru dari Streamlit")
    description = st.text_area("Deskripsi Video", "Video diupload melalui aplikasi Streamlit dengan autentikasi YouTube")
    
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Kategori", 
            ["22 - People & Blogs", "23 - Comedy", "24 - Entertainment", 
             "25 - News & Politics", "26 - Howto & Style", "27 - Education",
             "28 - Science & Technology", "29 - Nonprofits & Activism"],
            index=0)
    
    with col2:
        privacy_status = st.radio("Status Privasi", ["public", "private", "unlisted"])
    
    tags = st.text_input("Tags (pisahkan dengan koma)", "streamlit,youtube,upload")
    
    # Progress dan status
    progress_bar = st.empty()
    status_text = st.empty()
    
    # Tombol upload
    if st.button("📤 Upload Video ke YouTube", type="primary", disabled=not video_file):
        if video_file:
            try:
                # Simulasi proses upload
                status_text.text("🔄 Memulai proses upload...")
                progress_bar.progress(0)
                
                # Simulasi upload progress
                for i in range(100):
                    time.sleep(0.05)  # Simulasi waktu upload
                    progress_bar.progress(i + 1)
                    if i < 30:
                        status_text.text("⬆️ Mengunggah video...")
                    elif i < 70:
                        status_text.text("⚙️ Memproses metadata...")
                    else:
                        status_text.text("✅ Hampir selesai...")
                
                # Simulasi berhasil
                st.success("🎉 Video berhasil diupload!")
                st.balloons()
                
                # Tampilkan hasil (simulasi)
                st.subheader("📊 Hasil Upload")
                st.markdown(f"**📹 Judul:** {title}")
                st.markdown(f"**📺 Channel:** {st.session_state.selected_channel.get('snippet', {}).get('title', 'N/A')}")
                st.markdown("**🔗 URL Video:** https://youtu.be/dQw4w9WgXcQ")
                st.markdown("**🕒 Durasi:** 5:30 menit")
                st.markdown("**📊 Status:** Diproses")
                
            except Exception as e:
                st.error(f"❌ Error saat upload: {str(e)}")
        else:
            st.warning("⚠️ Silakan pilih file video terlebih dahulu")

# Informasi dan bantuan
def show_help_info():
    st.sidebar.title("ℹ️ Bantuan")
    st.sidebar.markdown(f"""
    ### Konfigurasi Google Cloud Console:
    
    **Redirect URI yang digunakan:**
    ```
    {REDIRECT_URI}
    ```
    
    **Langkah Setup:**
    1. Buat project di [Google Cloud Console](https://console.cloud.google.com/)
    2. Aktifkan YouTube Data API v3
    3. Buat OAuth 2.0 credentials (Web Application)
    4. Tambahkan redirect URI di atas
    5. Download `client_secret.json`
    
    **Langkah Autentikasi:**
    1. Unggah `client_secret.json`
    2. Klik "🔐 Autentikasi dengan YouTube"
    3. Klik link untuk login
    4. Setelah redirect, salin URL lengkap
    5. Masukkan URL di input yang disediakan
    
    ### Troubleshooting:
    - Pastikan redirect URI sudah terdaftar di Google Cloud Console
    - Gunakan tipe "Web Application" untuk OAuth credentials
    - Tunggu beberapa menit setelah menambahkan redirect URI
    """)

if __name__ == "__main__":
    show_help_info()
    main()
