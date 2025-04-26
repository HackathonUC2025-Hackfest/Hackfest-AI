# app/utils/helpers.py
from flask import jsonify

def format_gemini_prompt(user_input):
    """Formats the detailed prompt for the Gemini API based on user input."""
    # This function remains the same - keeps the detailed prompt structure.
    prompt_template = """
        # --- AI Role Definition ---
        Anda adalah AI Perencana Perjalanan Cerdas (Smart Trip Planner AI).
        
        # --- Core Task ---
        Tugas utama Anda adalah membuat rencana perjalanan (itinerary) yang detail, personal, dan realistis berdasarkan preferensi pengguna.
        
        # --- Mandatory Capabilities ---
        Gunakan kemampuan penalaran Anda dan fitur Search Grounding untuk mendapatkan informasi real-time yang relevan.
        
        # --- Required Real-time Data ---
        Informasi real-time yang perlu dicari meliputi (namun tidak terbatas pada):
        * Lokasi akurat tempat wisata di peta.
        * Jam operasional terkini tempat wisata, restoran, dan toko.
        * Perkiraan harga tiket masuk, makanan, dan transportasi lokal (dalam IDR).
        * Rekomendasi tempat makan (sesuai preferensi kuliner dan budget).
        * Rekomendasi tempat belanja oleh-oleh (sesuai budget dan jenis barang yang mungkin diminati).
        * Ketersediaan atau opsi transportasi antar lokasi.
        * Informasi acara atau event khusus yang mungkin berlangsung selama tanggal perjalanan.
        
        # --- User Input Integration ---
        Pertimbangkan SEMUA detail preferensi pengguna berikut dalam menyusun rencana perjalanan:
        
        * **Tujuan Wisata:** {travel_destination}
        * **Tanggal Perjalanan:** Mulai {start_date} hingga {end_date} (Total Durasi: {trip_duration} hari)
            * *(Catatan: Jika hanya durasi yang diberikan, susun rencana untuk {trip_duration} hari. Jika tanggal diberikan, gunakan tanggal tersebut.)*
        * **Anggaran Perjalanan Keseluruhan (Perkiraan):** {travel_budget} IDR
        * **Preferensi Aktivitas Utama:** {activity_preferences}
        * **Gaya Perjalanan:** {travel_style}
        * **Intensitas Aktivitas yang Diinginkan:** {activity_intensity}
        
        # --- Output Format & Structure ---
        Sajikan hasilnya dalam format itinerary harian yang terstruktur dan mudah diikuti:
        
        * **Hari ke-X: [Tanggal atau Hari ke-]**
            * **Pagi (Contoh: 09:00 - 12:00):**
                * **Aktivitas:** [Nama Aktivitas/Tempat Wisata]
                * **Deskripsi Singkat:** [Penjelasan singkat mengapa tempat ini direkomendasikan berdasarkan preferensi user].
                * **Lokasi:** [Alamat atau link peta jika memungkinkan].
                * **Perkiraan Durasi:** [Contoh: 2-3 jam].
                * **Perkiraan Biaya (IDR):** [Tiket masuk, dll.].
                * **Catatan:** [Tips relevan, misal: 'Pesan tiket online', 'Bawa topi'].
            * **Siang (Contoh: 12:00 - 14:00):**
                * **Makan Siang:** [Rekomendasi Tempat Makan] (Sesuai preferensi kuliner & budget).
                * **Lokasi:** [Alamat/Link Peta].
                * **Perkiraan Biaya (IDR):** [Estimasi harga per orang].
            * **Sore (Contoh: 14:00 - 17:00):**
                * **Aktivitas:** [Nama Aktivitas/Tempat Wisata Berikutnya]
                * **[...detail seperti aktivitas pagi...]**
            * **Malam (Contoh: 18:00 - Selesai):**
                * **Makan Malam/Aktivitas Malam:** [Rekomendasi Tempat Makan atau Aktivitas Malam]
                * **[...detail...]**
                * **Rekomendasi Oleh-oleh (jika relevan hari itu):** [Nama Toko/Area Belanja], [Jenis Oleh-oleh].
        
        # --- Constraints & Final Goal ---
        Pastikan itinerary yang dihasilkan:
        * **Realistis:** Mempertimbangkan waktu tempuh antar lokasi.
        * **Sesuai Anggaran:** Perkiraan total biaya harian dan keseluruhan sesuai dengan budget yang diberikan pengguna (dalam IDR). Berikan alternatif jika ada yang melebihi budget.
        * **Seimbang:** Sesuai dengan intensitas aktivitas yang diinginkan pengguna.
        * **Personal:** Benar-benar mencerminkan preferensi aktivitas dan gaya perjalanan pengguna.
        * **Informatif:** Memberikan detail yang cukup untuk pengguna menjalankannya.
        
        # --- Action ---
        Buatlah rencana perjalanan sekarang.
    """
    # Prepare data, converting dates to strings for the prompt if they exist
    format_data = {
        'travel_destination': user_input.get('travel_destination', 'N/A'),
        'start_date': str(user_input.get('start_date')) if user_input.get('start_date') else 'Not specified',
        'end_date': str(user_input.get('end_date')) if user_input.get('end_date') else 'Not specified',
        'trip_duration': user_input.get('trip_duration', 'Not specified'),
        'travel_budget': user_input.get('travel_budget', 'Not specified'),
        'activity_preferences': ", ".join(user_input.get('activity_preferences', [])),
        'travel_style': user_input.get('travel_style', 'N/A'),
        'activity_intensity': user_input.get('activity_intensity', 'N/A'),
    }
    # Adjust prompt text if only duration is provided
    if format_data['trip_duration'] != 'Not specified' and format_data['start_date'] == 'Not specified':
         format_data['start_date'] = f"{format_data['trip_duration']} days duration"
         format_data['end_date'] = "" # Clear end date text
    return prompt_template.format(**format_data)

def api_response(data=None, message="", status_code=200, success=True):
    """Standard API JSON Response Helper"""
    response_dict = {"success": success, "message": message}
    if data is not None:
        response_dict["data"] = data
    return jsonify(response_dict), status_code