# -*- coding: utf-8 -*-
"""ASD.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1TlTvndePYd6i9NVKkvhQfxmOCHWZI5f0
"""

import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import math
from matplotlib.animation import FuncAnimation
import ffmpeg

df = pd.read_excel('2000_2600.xlsx')      #Koordinatlar
dx = pd.read_excel('closest_players_filtered.xlsx')   # Kaleci dışında kale çizgisine en yakın oyuncu
dy = ('closest_players_in_zones.xlsx') #Her dilimde, kale çizgisine en yakın (kaleci olmayan) oyuncu en yakın oyuncu

# Saha boyutları
saha_uzunluk = 105
saha_genislik = 68
orta_yuvarlak_yaricap = 9.15
ceza_sahasi_uzunluk = 16.5
ceza_sahasi_genislik = 40.3
penalti_noktasi_mesafe = 11
kale_genislik = 7.32
kale_derinlik = 2.44
time_interval = 0.2
oyuncu_capi = 4
top_capi = 3

# Topun opasitesini yükseklik bazlı ayarlayan fonksiyon
def get_opacity(h):
    if h <= 1:
        return 1.0  # %100
    elif h <= 2:
        return 0.9  # %90
    elif h <= 3:
        return 0.8  # %80
    elif h <= 6:
        return 0.7  # %70
    elif h <= 10:
        return 0.6  # %60
    elif h <= 15:
        return 0.4  # %40
    else:
        return 0.2  # %20

# Topun yüksekliğine göre alanını büyüten fonksiyon
def get_size_by_height(h, A0=100):
    if h <= 0:
        return A0
    return A0 * (1.4 + 0.6 * (math.log(h) / math.log(20)))

# Grafik ve saha sınırlarını oluşturma
fig, ax = plt.subplots(figsize=(10, 6))

# Grafik rengi
ax.set_facecolor('#187D36')

# Saha sınırlarını çizme
ax.add_patch(plt.Rectangle((-saha_uzunluk/2, -saha_genislik/2), saha_uzunluk, saha_genislik,
                           edgecolor='black', facecolor='none', lw=3))

# Orta çizgi
ax.plot([0, 0], [-saha_genislik/2, saha_genislik/2], color='black', lw=3)

# Ceza sahaları
ax.add_patch(plt.Rectangle((saha_uzunluk/2 - ceza_sahasi_uzunluk, -ceza_sahasi_genislik/2), ceza_sahasi_uzunluk, ceza_sahasi_genislik, edgecolor='black', facecolor='none', lw=3))
ax.add_patch(plt.Rectangle((-saha_uzunluk/2, -ceza_sahasi_genislik/2), ceza_sahasi_uzunluk, ceza_sahasi_genislik, edgecolor='black', facecolor='none', lw=3))

# Penaltı noktaları ve kaleler
ax.plot(saha_uzunluk/2 - penalti_noktasi_mesafe, 0, 'ko', markersize=5)
ax.plot(-saha_uzunluk/2 + penalti_noktasi_mesafe, 0, 'ko', markersize=5)
ax.add_patch(plt.Rectangle((saha_uzunluk/2 - kale_derinlik, -kale_genislik/2), kale_derinlik, kale_genislik, edgecolor='black', facecolor='none', lw=3))
ax.add_patch(plt.Rectangle((-saha_uzunluk/2, -kale_genislik/2), kale_derinlik, kale_genislik, edgecolor='black', facecolor='none', lw=3))

# Orta yuvarlak
center_circle = plt.Circle((0, 0), orta_yuvarlak_yaricap, color='black', fill=False, lw=3)
ax.add_patch(center_circle)

# Oyuncu ve top göstergeleri için scatter objelerini çaplara uygun şekilde başlatma
team_blue_scatter = ax.scatter([], [], s=(oyuncu_capi ** 2) * 10, color='#99D9EA', label='Team Blue', zorder=3)
team_red_scatter = ax.scatter([], [], s=(oyuncu_capi ** 2) * 10, color='#EDA4A5', label='Team Red', zorder=3)
ball_scatter = ax.scatter([], [], s=(top_capi ** 2) * 10, color='#FFF200', label='Ball', zorder=5, alpha=1)

# Eksen ayarları
ax.set_xlim(-saha_uzunluk/2 - 5, saha_uzunluk/2 + 5)
ax.set_ylim(-saha_genislik/2 - 5, saha_genislik/2 + 5)
ax.set_aspect('equal')
ax.set_title('Savunma Hattı')
ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
plt.grid(False)

# Eksen ayarlarını kaldır
ax.set_xticks([])
ax.set_yticks([])

# Oyuncu numaralarını tutmak için boş liste
annotations_blue = []  # Changed to an empty list
annotations_red = []  # Changed to an empty list
arrow_ball = ax.arrow(0, 0, 0, 0, color='#FFF200', head_width=1.0)
arrows_blue = [ax.arrow(0, 0, 0, 0, color='#99D9EA', head_width=0.5) for _ in range(11)]  # Initialize arrows_blue
arrows_red = [ax.arrow(0, 0, 0, 0, color='#EDA4A5', head_width=0.5) for _ in range(11)]  # Initialize arrows_red

# İlk olarak mavi ve kırmızı takım oyuncuları için numaraları başlatıyoruz
for i in range(11):  # Mavi takım için
    annotation = ax.annotate(str(i + 1), (0, 0), color='#99D9EA', fontsize=10, ha='center')
    annotations_blue.append(annotation)  # Now appends to an empty list

for i in range(11):  # Kırmızı takım için
    annotation = ax.annotate(str(i + 12), (0, 0), color='#EDA4A5', fontsize=10, ha='center')
    annotations_red.append(annotation)  # Now appends to an empty list

def draw_defense_line(ax, player_x, saha_genislik, line_color, alpha=0.2, label=None):
    """
    Verilen x koordinatında, y eksenine paralel bir çizgi çizer ve önceki çizgiyi siler.

    Args:
        ax: Matplotlib ekseni.
        player_x: Çizginin x koordinatı.
        saha_genislik: Sahanın genişliği.
        line_color: Çizginin rengi.
        alpha: Çizginin opaklığı (0 ile 1 arasında, varsayılan: 0.2).
        label: Çizgi etiketi (örneğin 'blue_defense' veya 'red_defense').
    """
    # Önceki aynı renkteki çizgiyi sil
    for line in ax.lines:
        if line.get_label() == label:
            line.remove()

    # Yeni çizgiyi ekle
    ax.plot([player_x, player_x], [-saha_genislik / 2, saha_genislik / 2],
            color=line_color, linestyle='-', linewidth=3, alpha=alpha, label=label)

def draw_defense_grid(ax, x_start, x_end, saha_genislik, saha_uzunluk, color='orange', alpha=0.2):
    """İki savunma hattı arasını 4x7.5 m'lik 16 eşit dilime böler (sadece yatay çizgiler)"""

    # Get lines with the specified color to remove them later
    lines_to_remove = [line for line in ax.lines if line.get_color() == color]

    # Remove the lines with the specified color
    for line in lines_to_remove:
        line.remove()

    # Dilimlerin boyutları
    zone_height = saha_genislik / 16

    # Yatay çizgiler
    for j in range(17):
        y_pos = -saha_genislik / 2 + j * zone_height  # Sahanın altından başlayarak yukarıya doğru çiz
        ax.plot([x_start, x_end], [y_pos, y_pos], color=color, linestyle='-', linewidth=1, alpha=alpha)

# Animasyon fonksiyonu
def animate(i):
    global arrow_ball  # arrow_ball değişkenini küresel olarak tanımlıyoruz.

    if i < len(df) - 1:
        # Mavi takım pozisyonları
        team_blue_positions = df.loc[i, [
            'player1_x', 'player1_y', 'player2_x', 'player2_y', 'player3_x', 'player3_y',
            'player4_x', 'player4_y', 'player5_x', 'player5_y', 'player6_x', 'player6_y',
            'player7_x', 'player7_y', 'player8_x', 'player8_y', 'player9_x', 'player9_y',
            'player10_x', 'player10_y', 'player11_x', 'player11_y'
        ]].values.reshape(-1, 2)

        # Kırmızı takım pozisyonlarını alın
        team_red_positions = df.loc[i, [
            'player12_x', 'player12_y', 'player13_x', 'player13_y', 'player14_x', 'player14_y',
            'player15_x', 'player15_y', 'player16_x', 'player16_y', 'player17_x', 'player17_y',
            'player18_x', 'player18_y', 'player19_x', 'player19_y', 'player20_x', 'player20_y',
            'player21_x', 'player21_y', 'player22_x', 'player22_y'
        ]].values.reshape(-1, 2)

        next_team_blue_positions  = df.loc[i+1, [
            'player1_x', 'player1_y', 'player2_x', 'player2_y', 'player3_x', 'player3_y',
            'player4_x', 'player4_y', 'player5_x', 'player5_y', 'player6_x', 'player6_y',
            'player7_x', 'player7_y', 'player8_x', 'player8_y', 'player9_x', 'player9_y',
            'player10_x', 'player10_y', 'player11_x', 'player11_y'
        ]].values.reshape(-1, 2)

        next_team_red_positions  = df.loc[i+1, [
            'player12_x', 'player12_y', 'player13_x', 'player13_y', 'player14_x', 'player14_y',
            'player15_x', 'player15_y', 'player16_x', 'player16_y', 'player17_x', 'player17_y',
            'player18_x', 'player18_y', 'player19_x', 'player19_y', 'player20_x', 'player20_y',
            'player21_x', 'player21_y', 'player22_x', 'player22_y'
        ]].values.reshape(-1, 2)

        # Top pozisyonu ve yüksekliği
        ball_position = df.loc[i, ['ball_x', 'ball_y']].values
        ball_height = df.loc[i, 'ball_z']
        next_ball_position = df.loc[i + 1, ['ball_x', 'ball_y']].values

        # Opasite ve boyut güncellemeleri
        opacity = get_opacity(ball_height)
        size = get_size_by_height(ball_height)

        # Scatter objelerini güncelle
        team_blue_scatter.set_offsets(team_blue_positions)
        team_red_scatter.set_offsets(team_red_positions)
        ball_scatter.set_offsets(ball_position)
        ball_scatter.set_sizes([size])
        ball_scatter.set_alpha(opacity)

        # Oyuncu numaralarını güncelle
        for j, pos in enumerate(team_blue_positions):
            annotations_blue[j].set_position((pos[0], pos[1] + oyuncu_capi / 2))  # Numaraları oyuncunun üstüne ekle
        for j, pos in enumerate(team_red_positions):
            annotations_red[j].set_position((pos[0], pos[1] + oyuncu_capi / 2))  # Numaraları oyuncunun üstüne ekle

        # Yön oklarını güncelle
        for j in range(11):
            dx_blue, dy_blue = next_team_blue_positions[j] - team_blue_positions[j]
            dx_red, dy_red = next_team_red_positions[j] - team_red_positions[j]
            arrows_blue[j].remove()  # Eski oku sil
            arrows_red[j].remove()  # Eski oku sil
            arrows_blue[j] = ax.arrow(team_blue_positions[j][0], team_blue_positions[j][1], dx_blue, dy_blue, color='#99D9EA', head_width=oyuncu_capi / 2)
            arrows_red[j] = ax.arrow(team_red_positions[j][0], team_red_positions[j][1], dx_red, dy_red, color='#EDA4A5', head_width=oyuncu_capi / 2)

        dx_ball, dy_ball = next_ball_position - ball_position
        arrow_ball.remove()  # Eski oku sil
        arrow_ball = ax.arrow(ball_position[0], ball_position[1], dx_ball, dy_ball, color='#FFF200', head_width=top_capi / 2)

        # Verileri al
        en_yakin_oyuncu_mavi = dx.loc[i, 'Mavi Kale Çizgisine En Yakın Oyuncu']
        en_yakin_oyuncu_kirmizi = dx.loc[i, 'Kırmızı Kale Çizgisine En Yakın Oyuncu']

        # Birinci savunma hattını çizen oyuncuların x koordinatlarını al
        en_yakin_oyuncu_mavi_x = df.loc[i, f'player{int(en_yakin_oyuncu_mavi[6:])}_x']
        en_yakin_oyuncu_kirmizi_x = df.loc[i, f'player{int(en_yakin_oyuncu_kirmizi[6:])}_x']

        # İlk savunma hatlarını çiz
        draw_defense_line(ax, en_yakin_oyuncu_mavi_x, saha_genislik, line_color='#99D9EA', alpha=0.2, label='blue_defense')
        draw_defense_line(ax, en_yakin_oyuncu_kirmizi_x, saha_genislik, line_color='#EDA4A5', alpha=0.2, label='red_defense')

        # **İkinci savunma hatlarını çiz**
        ikinci_savunma_hatti_mavi_x = en_yakin_oyuncu_mavi_x + 7.5
        ikinci_savunma_hatti_kirmizi_x = en_yakin_oyuncu_kirmizi_x - 7.5

        draw_defense_line(ax, ikinci_savunma_hatti_mavi_x, saha_genislik, line_color='#99D9EA', alpha=0.2, label='blue_defense_2')
        draw_defense_line(ax, ikinci_savunma_hatti_kirmizi_x, saha_genislik, line_color='#EDA4A5', alpha=0.2, label='red_defense_2')

        # Savunma bölgelerini çiz
        draw_defense_grid(ax, en_yakin_oyuncu_mavi_x, ikinci_savunma_hatti_mavi_x, saha_genislik, saha_uzunluk, color='blue', alpha=0.3)
        draw_defense_grid(ax, ikinci_savunma_hatti_kirmizi_x, en_yakin_oyuncu_kirmizi_x, saha_genislik, saha_uzunluk, color='red', alpha=0.3)

#Animasyonu çalıştır
ani = FuncAnimation(fig, animate, frames=len(df) - 1, interval=200, repeat=False)

#Animasyonu göster
plt.show(ani)
ani.save("parca.mp4", writer="ffmpeg")