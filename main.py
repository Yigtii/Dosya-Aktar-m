import sys
import os
import random
from datetime import datetime, time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QSlider, QLabel,
                             QFileDialog, QListWidget, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


class VertusMusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vertus Music - Okul Zil Sistemi")
        self.setGeometry(100, 100, 900, 600)

        # Pencere logosunu ayarla
        self.setWindowIcon(QIcon("logo.png" if os.path.exists("logo.png") else ""))

        # Müzik çalar ve ses çıkışı
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        # Oynatma durumu ve zamanlayıcı
        self.is_playing = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_slider)

        # Zil zamanlayıcısı
        self.bell_timer = QTimer()
        self.bell_timer.timeout.connect(self.check_bell_time)
        self.bell_timer.start(30000)  # 30 saniyede bir kontrol et

        # Şarkı listesi
        self.songs = []
        self.current_index = -1

        # Zil programı
        self.bell_schedule = [
            # 1. Ders
            {"start": time(8, 0), "end": time(8, 40), "type": "ders", "music": False},
            {"start": time(8, 40), "end": time(8, 50), "type": "teneffus", "music": True, "duration": 10},

            # 2. Ders
            {"start": time(8, 50), "end": time(9, 30), "type": "ders", "music": False},
            {"start": time(9, 30), "end": time(9, 40), "type": "teneffus", "music": True, "duration": 10},

            # 3. Ders
            {"start": time(9, 40), "end": time(10, 20), "type": "ders", "music": False},
            {"start": time(10, 20), "end": time(10, 30), "type": "teneffus", "music": True, "duration": 10},

            # 4. Ders
            {"start": time(10, 30), "end": time(11, 10), "type": "ders", "music": False},
            {"start": time(11, 10), "end": time(11, 20), "type": "teneffus", "music": True, "duration": 10},

            # 5. Ders
            {"start": time(11, 20), "end": time(12, 0), "type": "ders", "music": False},

            # Öğle Arası
            {"start": time(12, 0), "end": time(13, 0), "type": "oglen", "music": False},

            # 6. Ders
            {"start": time(13, 0), "end": time(13, 40), "type": "ders", "music": False},
            {"start": time(13, 40), "end": time(13, 50), "type": "teneffus", "music": True, "duration": 10},

            # 7. Ders
            {"start": time(13, 50), "end": time(14, 30), "type": "ders", "music": False},
            {"start": time(14, 30), "end": time(14, 40), "type": "teneffus", "music": True, "duration": 10},

            # 8. Ders
            {"start": time(14, 40), "end": time(15, 20), "type": "ders", "music": False},
        ]

        self.current_period = None
        self.teneffus_timer = QTimer()
        self.teneffus_timer.timeout.connect(self.teneffus_bitisi)
        self.teneffus_remaining = 0

        self.init_ui()

    def init_ui(self):
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Sol panel - şarkı listesi ve zil kontrolü
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #121212; border-radius: 10px;")
        left_panel.setMinimumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)

        # Zil durumu
        bell_status_label = QLabel("Zil Durumu")
        bell_status_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        bell_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(bell_status_label)

        self.bell_status = QLabel("Aktif")
        self.bell_status.setStyleSheet("color: #1DB954; font-size: 14px; padding: 5px;")
        self.bell_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.bell_status)

        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold; padding: 10px;")
        self.current_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.current_time_label)

        self.period_info = QLabel("Henüz ders başlamadı")
        self.period_info.setStyleSheet("color: #b3b3b3; font-size: 12px; padding: 5px;")
        self.period_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.period_info.setWordWrap(True)
        left_layout.addWidget(self.period_info)

        # Zil kontrol butonları
        bell_control_widget = QWidget()
        bell_control_layout = QHBoxLayout(bell_control_widget)

        self.bell_toggle_btn = QPushButton("Zili Durdur")
        self.bell_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #333;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #252525;
            }
        """)
        self.bell_toggle_btn.clicked.connect(self.toggle_bell)
        bell_control_layout.addWidget(self.bell_toggle_btn)

        manual_play_btn = QPushButton("Şimdi Çal")
        manual_play_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1ed760;
            }
        """)
        manual_play_btn.clicked.connect(self.manual_play)
        bell_control_layout.addWidget(manual_play_btn)

        left_layout.addWidget(bell_control_widget)

        # Şarkı listesi başlığı
        song_list_label = QLabel("Şarkı Listesi")
        song_list_label.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold; padding: 10px; margin-top: 10px;")
        song_list_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(song_list_label)

        # Şarkı listesi
        self.song_list = QListWidget()
        self.song_list.setStyleSheet("""
            QListWidget {
                background-color: #121212;
                color: white;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #282828;
            }
            QListWidget::item:selected {
                background-color: #333333;
            }
            QListWidget::item:hover {
                background-color: #252525;
            }
        """)
        self.song_list.itemDoubleClicked.connect(self.play_selected_song)
        left_layout.addWidget(self.song_list)

        # Şarkı ekle butonu
        add_song_btn = QPushButton("Şarkı Ekle")
        add_song_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #333;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #252525;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        add_song_btn.clicked.connect(self.add_songs)
        left_layout.addWidget(add_song_btn)

        # Sağ panel - müzik çalar ve ayarlar
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #181818; border-radius: 10px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)

        # Albüm kapağı alanı
        album_frame = QFrame()
        album_frame.setStyleSheet("background-color: transparent;")
        album_layout = QVBoxLayout(album_frame)
        album_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Disk resmi
        self.disk_label = QLabel()
        if os.path.exists("disk.png"):
            pixmap = QPixmap("disk.png")
            self.disk_label.setPixmap(pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation))
        else:
            self.disk_label.setFixedSize(250, 250)
            self.disk_label.setStyleSheet("""
                QLabel {
                    background-color: #333;
                    border-radius: 125px;
                    border: 15px solid #1a1a1a;
                }
            """)
        self.disk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        album_layout.addWidget(self.disk_label)

        # Şarkı bilgileri
        self.song_title = QLabel("Şarkı Seçin")
        self.song_title.setStyleSheet("color: white; font-size: 20px; font-weight: bold; margin-top: 15px;")
        self.song_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        album_layout.addWidget(self.song_title)

        self.song_artist = QLabel("Zil Sistemi Hazır")
        self.song_artist.setStyleSheet("color: #b3b3b3; font-size: 14px; margin-top: 5px;")
        self.song_artist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        album_layout.addWidget(self.song_artist)

        right_layout.addWidget(album_frame)

        # İlerleme çubuğu
        progress_widget = QWidget()
        progress_widget.setStyleSheet("background-color: transparent;")
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 20, 0, 0)

        self.time_current = QLabel("0:00")
        self.time_current.setStyleSheet("color: #b3b3b3; font-size: 12px;")
        self.time_current.setFixedWidth(40)
        progress_layout.addWidget(self.time_current)

        self.song_slider = QSlider(Qt.Orientation.Horizontal)
        self.song_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #404040;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #1DB954;
                border-radius: 2px;
            }
            QSlider::add-page:horizontal {
                background: #404040;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
            }
        """)
        self.song_slider.sliderMoved.connect(self.set_position)
        progress_layout.addWidget(self.song_slider)

        self.time_total = QLabel("0:00")
        self.time_total.setStyleSheet("color: #b3b3b3; font-size: 12px;")
        self.time_total.setFixedWidth(40)
        progress_layout.addWidget(self.time_total)

        right_layout.addWidget(progress_widget)

        # Kontrol butonları
        control_widget = QWidget()
        control_widget.setStyleSheet("background-color: transparent;")
        control_layout = QHBoxLayout(control_widget)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.setContentsMargins(0, 20, 0, 0)

        prev_btn = QPushButton("◀◀")
        prev_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #b3b3b3;
                font-size: 16px;
                padding: 5px;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        prev_btn.clicked.connect(self.previous_song)
        control_layout.addWidget(prev_btn)

        self.play_btn = QPushButton("▶")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: none;
                border-radius: 20px;
                padding: 10px;
                font-size: 16px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #f2f2f2;
                transform: scale(1.05);
            }
        """)
        self.play_btn.clicked.connect(self.play_pause)
        control_layout.addWidget(self.play_btn)

        next_btn = QPushButton("▶▶")
        next_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #b3b3b3;
                font-size: 16px;
                padding: 5px;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        next_btn.clicked.connect(self.next_song)
        control_layout.addWidget(next_btn)

        right_layout.addWidget(control_widget)

        # Ses ve equalizer ayarları
        settings_widget = QWidget()
        settings_widget.setStyleSheet("background-color: transparent;")
        settings_layout = QHBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 20, 0, 0)

        volume_widget = QWidget()
        volume_widget.setStyleSheet("background-color: transparent;")
        volume_layout = QVBoxLayout(volume_widget)

        volume_label = QLabel("Ses")
        volume_label.setStyleSheet("color: #b3b3b3; font-size: 12px;")
        volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_layout.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #404040;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #b3b3b3;
                border-radius: 2px;
            }
            QSlider::add-page:horizontal {
                background: #404040;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
            }
        """)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)

        settings_layout.addWidget(volume_widget)

        bass_widget = QWidget()
        bass_widget.setStyleSheet("background-color: transparent;")
        bass_layout = QVBoxLayout(bass_widget)

        bass_label = QLabel("Bas")
        bass_label.setStyleSheet("color: #b3b3b3; font-size: 12px;")
        bass_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bass_layout.addWidget(bass_label)

        self.bass_slider = QSlider(Qt.Orientation.Horizontal)
        self.bass_slider.setRange(-24, 24)
        self.bass_slider.setValue(0)
        self.bass_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #404040;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #b3b3b3;
                border-radius: 2px;
            }
            QSlider::add-page:horizontal {
                background: #404040;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
            }
        """)
        self.bass_slider.valueChanged.connect(self.set_bass)
        bass_layout.addWidget(self.bass_slider)

        settings_layout.addWidget(bass_widget)

        right_layout.addWidget(settings_widget)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

        # Player sinyallerini bağla
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.playbackStateChanged.connect(self.state_changed)

        # Başlangıç ses seviyesini ayarla
        self.audio_output.setVolume(self.volume_slider.value() / 100)

        # Saati güncelle
        self.update_time()
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)

    def update_time(self):
        now = datetime.now()
        self.current_time_label.setText(now.strftime("%H:%M:%S"))

    def check_bell_time(self):
        if not self.bell_timer.isActive():
            return

        now = datetime.now().time()

        for period in self.bell_schedule:
            if period['start'] <= now <= period['end']:
                if self.current_period != period:
                    self.current_period = period
                    self.handle_period_change(period)
                break

    def handle_period_change(self, period):
        period_type = "Ders" if period['type'] == 'ders' else "Teneffüs" if period[
                                                                                'type'] == 'teneffus' else "Öğle Arası"
        self.period_info.setText(
            f"{period_type}\n{period['start'].strftime('%H:%M')} - {period['end'].strftime('%H:%M')}")

        if period['music']:
            self.start_teneffus_music(period['duration'])
        else:
            self.stop_music()

    def start_teneffus_music(self, duration_minutes):
        if not self.songs:
            QMessageBox.warning(self, "Uyarı", "Teneffüste çalacak şarkı bulunamadı!")
            return

        self.teneffus_remaining = duration_minutes * 60  # Saniyeye çevir
        self.play_random_song()

        # Teneffüs bitiş zamanlayıcısını başlat
        self.teneffus_timer.start(60000)  # Her dakika kontrol et

    def teneffus_bitisi(self):
        self.teneffus_remaining -= 60
        if self.teneffus_remaining <= 0:
            self.teneffus_timer.stop()
            self.stop_music()
            # Teneffüs bitti, ders başlıyor
            self.period_info.setText("Teneffüs bitti, ders başlıyor!")

    def play_random_song(self):
        if not self.songs:
            return

        if len(self.songs) == 1:
            # Sadece bir şarkı varsa onu çal
            self.play_song(0)
        else:
            # Rastgele bir şarkı seç (mevcut şarkıyı tekrar seçmemeye çalış)
            available_indices = [i for i in range(len(self.songs)) if i != self.current_index]
            if available_indices:
                random_index = random.choice(available_indices)
                self.play_song(random_index)

    def toggle_bell(self):
        if self.bell_timer.isActive():
            self.bell_timer.stop()
            self.bell_status.setText("Durduruldu")
            self.bell_toggle_btn.setText("Zili Başlat")
            self.bell_status.setStyleSheet("color: #ff6b6b; font-size: 14px; padding: 5px;")
        else:
            self.bell_timer.start(30000)
            self.bell_status.setText("Aktif")
            self.bell_toggle_btn.setText("Zili Durdur")
            self.bell_status.setStyleSheet("color: #1DB954; font-size: 14px; padding: 5px;")

    def manual_play(self):
        if self.songs:
            self.play_random_song()

    def add_songs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Şarkı Seç", "", "Ses Dosyaları (*.mp3 *.wav *.ogg *.flac *.m4a)"
        )

        for file in files:
            song_name = os.path.splitext(os.path.basename(file))[0]
            self.song_list.addItem(song_name)
            self.songs.append(file)

    def play_selected_song(self, item):
        index = self.song_list.row(item)
        if 0 <= index < len(self.songs):
            self.current_index = index
            self.play_song(index)

    def play_song(self, index):
        if 0 <= index < len(self.songs):
            file_path = self.songs[index]
            self.player.setSource(QUrl.fromLocalFile(file_path))

            song_name = os.path.splitext(os.path.basename(file_path))[0]
            self.song_title.setText(song_name)
            self.song_artist.setText("Zil Sistemi - Çalıyor")

            self.song_list.setCurrentRow(index)
            self.player.play()
            self.is_playing = True
            self.play_btn.setText("⏸")
            self.timer.start(1000)

    def play_pause(self):
        if not self.songs:
            return

        if self.player.source().isEmpty():
            if self.songs:
                self.play_random_song()
            return

        if self.is_playing:
            self.player.pause()
            self.play_btn.setText("▶")
            self.song_artist.setText("Zil Sistemi - Duraklatıldı")
        else:
            self.player.play()
            self.play_btn.setText("⏸")
            self.song_artist.setText("Zil Sistemi - Çalıyor")

        self.is_playing = not self.is_playing

    def next_song(self):
        if not self.songs:
            return

        if len(self.songs) == 1:
            self.play_song(0)
        else:
            next_index = (self.current_index + 1) % len(self.songs)
            self.play_song(next_index)

    def previous_song(self):
        if not self.songs:
            return

        if len(self.songs) == 1:
            self.play_song(0)
        else:
            prev_index = (self.current_index - 1) % len(self.songs)
            self.play_song(prev_index)

    def stop_music(self):
        self.player.stop()
        self.is_playing = False
        self.play_btn.setText("▶")
        self.song_artist.setText("Zil Sistemi - Hazır")
        self.song_title.setText("Şarkı Seçin")
        self.timer.stop()

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100)

    def set_bass(self, value):
        pass

    def set_position(self, position):
        self.player.setPosition(position)

    def position_changed(self, position):
        self.song_slider.setValue(position)
        minutes = position // 60000
        seconds = (position % 60000) // 1000
        self.time_current.setText(f"{minutes}:{seconds:02d}")

    def duration_changed(self, duration):
        self.song_slider.setRange(0, duration)
        minutes = duration // 60000
        seconds = (duration % 60000) // 1000
        self.time_total.setText(f"{minutes}:{seconds:02d}")

    def state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            # Şarkı bittiğinde, teneffüs devam ediyorsa yeni şarkı çal
            if self.teneffus_timer.isActive() and self.teneffus_remaining > 0:
                self.play_random_song()
            else:
                self.song_slider.setValue(0)
                self.is_playing = False
                self.play_btn.setText("▶")
                self.timer.stop()

    def update_slider(self):
        if self.player.duration() > 0:
            self.song_slider.setValue(self.player.position())


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Vertus Music - Okul Zil Sistemi")

    player = VertusMusicPlayer()
    player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

