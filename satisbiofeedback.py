# Biofeedback mindfulness by Simone TRavaglini
# Licence GPL3
# parte il grafico viene ricreato un nuovo grafico invece che aggiornato il precedente, rimettere creazione CSV


import csv
import random
import serial
import time
import PySimpleGUI as sg
from datetime import datetime
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
import pygame
import matplotlib.ticker as ticker
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import configparser
from hrvanalysis import remove_outliers, remove_ectopic_beats, interpolate_nan_values
from hrvanalysis import get_time_domain_features
from hrvanalysis.extract_features import _get_freq_psd_from_nn_intervals
from hrvanalysis.extract_features import get_poincare_plot_features

from hrvanalysis import get_frequency_domain_features
#from hrvanalysis import plot_timeseries, plot_distrib, plot_psd, plot_poincare




# inizializza variabili a FALSE
ser = None
reading_serial = False
graph_running = False
firstRun = False

increaseGsrDetect=False
indexIncreaseGsrDetect = 0
#peakDetectorInterval = 10
#increaseGsrMax = 1000000 #a value never happen
playBell=False

sd_nn = 0.0  # Inizializza sd_nn con un valore predefinito
rmssd = 0.0  # Inizializza rmssd con un valore predefinito
min_hr = 0.0  # Inizializza min_hr con un valore predefinito
max_hr = 0.0  # Inizializza max_hr con un valore predefinito
mean_hr= 0.0
lfband= 0.0
hfband= 0.0
vlf= 0.0
lfHfRatio = 0.0

timeOverGsrMax = 0




collectOn = False
printOn = False




# funzione collezione dati seriali e stampa a video dell'ultimo dato
def collect_serial_data():
    global ser, decoded_bytes, ser_bytes, currentDateAndTime, timenow, battiti,sd_nn, rmssd, min_hr, max_hr, gsrNow, nn_intervals_list, mean_hr, lfband,hfband,vlf,lfHfRatio, limitGSR, timeOverGsrMax, indexIncreaseGsrDetect, increaseGsrDetect,increaseGSR,playBell
    peakDetectorInterval = int(values['-SECINCREASE-'])
    increaseGsrMax = int(values['-PERCINCREASE-'])
    hrGot = False
    if ser and collectOn:
             
        #limitGSR=float(values['-GSR-'])      
        ser_bytes = ser.readline()
        decoded_bytes = ser_bytes.decode("utf-8").rstrip()
        
        window["-OUTPUT-"].print(decoded_bytes)
        
      
        # Dividi i dati in base alle virgole
        
        if decoded_bytes.startswith('G-'):
                values3.append(float(decoded_bytes[2:]))  # Rimuovi 'G-' e converte in float
                timestamps.append(time_as_int() - start_time)
                gsrNow = float(decoded_bytes[2:])
                #verifica se negli ultimi 20 secondi c'è stato un aumento del GSR
                
                if len(values3)-indexIncreaseGsrDetect > peakDetectorInterval:
                    increaseGsrDetect=False 
                
                if (len(values3)>peakDetectorInterval+1) and (values3[len(values3)-(peakDetectorInterval+1)] != 0):
                    increaseGSR=(values3[len(values3)-1]-values3[len(values3)-(peakDetectorInterval+1)])/values3[len(values3)-(peakDetectorInterval+1)]*100
                    #print(increaseGSR)
                    if increaseGSR>increaseGsrMax and increaseGsrDetect==False:
                        increaseGsrDetect=True
                        print("play sound")
                        playBell=True
                        
                        indexIncreaseGsrDetect=len(values3)-1    
                
                    
                #if gsrNow > limitGSR:
                    #print('sopra soglia!')
                    #playbell
                    #timeOverGsrMax = time_as_int();
                    #firstBell = timeOverGsrMax;
        elif decoded_bytes.startswith('H-'):
                values2.append(int(decoded_bytes[2:]))  # Rimuovi 'H-' e converte in intero
                timestamps2.append(time_as_int() - start_time)
                hrGot = True
                
                


        
        if hrGot:
            #elimino i picchi dall'HRV
            indici_picchi, _ = find_peaks(values2)
            valori_senza_picchi = np.delete(values2, indici_picchi)
            rr_intervals_without_outliers = remove_outliers(rr_intervals=values2,  
                                                    low_rri=450, high_rri=1340)
            interpolated_rr_intervals = interpolate_nan_values(rr_intervals=rr_intervals_without_outliers,
                                                    interpolation_method="linear")
            # This remove ectopic beats from signal
            nn_intervals_list = remove_ectopic_beats(rr_intervals=interpolated_rr_intervals, method="malik")
            
            
            if len(nn_intervals_list) > 0:  # Assicurati che la lista non sia vuota

            
                # This replace ectopic beats nan values with linear interpolation
                interpolated_nn_intervals = interpolate_nan_values(rr_intervals=nn_intervals_list)
                interpolati = interpolated_nn_intervals
                battiti = [60000 / x  for x in interpolati] #calcolo battiti ripuliti

                time_domain_features = get_time_domain_features(interpolated_nn_intervals)
                frequency_domain_features = get_frequency_domain_features(interpolated_nn_intervals)
                min_hr = time_domain_features['min_hr']
                max_hr = time_domain_features['max_hr']
                mean_hr = time_domain_features['mean_hr']
                mean_nni = time_domain_features['mean_nni']
                sd_nn = time_domain_features['sdnn']
                rmssd = time_domain_features['rmssd']
                lfband = round(frequency_domain_features['lf'],2)
                hfband = round(frequency_domain_features['hf'],2)
                vlf = round(frequency_domain_features['vlf'],2)
                lfHfRatio = round(frequency_domain_features['lf_hf_ratio'],2)
            
        
        
        window["-LAST_VALUES-"].update("")
        last_values_str = ""  # Inizializza la variabile per i valori passati
        #last_values_str = f": GSR:  HR:"
        last_values_str = f"SDNN:{sd_nn:.2f}\nRMSSD:{rmssd:.2f}\nminHR:{min_hr:.2f}\nmaxHR:{max_hr:.2f}\nMean HR:{mean_hr:.2f}\nLF:{lfband:.2f}\nHF:{hfband:.2f}\nVLF:{vlf:.2f}\nLF/HF:{lfHfRatio:.2f}\n\nGSR:{gsrNow:.2f} "
        window["-LAST_VALUES-"].update(last_values_str)
        # Aggiorna l'interfaccia grafica con il timer
        timenow = format_timer(time_as_int() - start_time)
        window['-TIMER-'].update(timenow)
        
        
    
def play_bell():
    # Inizializza pygame
    pygame.init()

    # Crea un mixer audio
    pygame.mixer.init()

    # Specifica il percorso del file MP3 da riprodurre
    file_mp3 = 'bell.wav'

    # Carica il file MP3
    pygame.mixer.music.load(file_mp3)

    # Riproduci il file MP3
    pygame.mixer.music.play()

    # Lascia il programma in esecuzione finché la musica sta suonando
    #while pygame.mixer.music.get_busy():
        #pass

    # Chiudi pygame
    #pygame.quit()

# Funzione per l'aggiornamento del grafico
def update_graph():
    global ax, ax2, clearOn, playBell
    
            
    while graph_running:
        
        
        if playBell == True:
            play_bell()
            playBell=False
        
        if clearOn:
            timestamps.clear()
            timestamps2.clear()
            values2.clear()
            values3.clear()
            battiti.clear()
            
            values2.append(1000)
            battiti.append(60)
            values3.append(0)
            timestamps.append(time_as_int() - start_time)
            timestamps2.append(time_as_int() - start_time)
            ax.clear()
            ax2.clear()
            print("cancellato")

            (line,) = ax.plot(timestamps, values3, color="blue", label="GSR")
            (line2,) = ax2.plot(timestamps2, battiti, color="red", label="HR")
            line.set_label("GSR")
            line2.set_label("HR")
            ax.legend(loc="upper left")
            ax2.legend(loc="upper left")


            def format_xaxis(x, _):
                return format_timer(int(x))


            # Formatta asse X hh:mm:ss
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_xaxis))
            ax2.xaxis.set_major_formatter(ticker.FuncFormatter(format_xaxis))

            clearOn = False
            
        if len(battiti) == len(timestamps2) and len(values3) == len(timestamps):
        
            try:
               #ax.axvline(x=100, color='red', linestyle='--')
               limitGSR=int(values['-GSR-'])
               ax.axhline(y=limitGSR, color='r', linestyle='--', linewidth=2)
            except Exception as e:
                sg.popup(f"Errore stampa linea orizzontale: {e}")
                continue
            
            line.set_data(timestamps, values3)
            line2.set_data(timestamps2, battiti)
            ax.relim()
            ax.autoscale_view()
            ax2.relim()
            ax2.autoscale_view()

            # Imposta solo 5 valori come indicatori sull'asse X
            max_ticks = 5  # Numero di indicatori desiderati sull'asse X
            ax.xaxis.set_major_locator(plt.MaxNLocator(max_ticks))
            ax2.xaxis.set_major_locator(plt.MaxNLocator(max_ticks))

            canvas.draw()
            canvas2.draw()

            time.sleep(0.1)




# creao il thread
graph_thread = threading.Thread(target=update_graph)


# funzione per salvare l'identificativo
def save_identificativo(identificativo):
    config = configparser.ConfigParser()
    config.read("config.ini")
    config["SETTINGS"] = {"identificativo": identificativo}
    with open("config.ini", "w") as configfile:
        config.write(configfile)


# funzione per caricare l'identificativo
def load_identificativo():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config.get("SETTINGS", "identificativo")


# se non ancora creato lo aggiunge al file config.ini
if not os.path.isfile("config.ini"):
    with open("config.ini", "w") as configfile:
        configfile.write("[SETTINGS]\nidentificativo = \n")

# carico l'identificativo
identificativo = load_identificativo()


# Funzione per ottenere il tempo come intero
def time_as_int():
    return int(round(time.time() * 100))


# Formatta il timer nel formato hh:mm:ss
def format_timer(elapsed_time):
    hours = elapsed_time // 360000
    minutes = (elapsed_time % 360000) // 6000
    seconds = (elapsed_time % 6000) // 100
    return f"{hours:02}:{minutes:02}:{seconds:02}"


# Imposta la sottocartella "AUDIO"
audio_folder = "AUDIO"

# Ottieni la lista dei file audio nella sottocartella "AUDIO"
audio_files = [
    f for f in os.listdir(audio_folder) if f.endswith(".mp3") or f.endswith(".wav")
]

# Inizializza Pygame e imposta il mixer audio
pygame.init()
pygame.mixer.init()

# Definisci lo stato della riproduzione audio
is_playing = False
pause_position = 0  # Posizione di pausa dell'audio

# Inizializza le liste per salvare i dati letti dalla porta seriale
values1 = []
values2 = []
values3 = []
#last_values = ["", "", ""]  # lista vuota per contenere gli ultimi 3 valori
timestamps = []
timestamps2 = []
interpolati = []
battiti = []


# Crea la lista delle porte seriali disponibili
def get_available_ports():
    import serial.tools.list_ports

    ports = list(serial.tools.list_ports.comports())
    return [port.device for port in ports]


# Crea la lista dei baudrate disponibili
baud_list = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]

# Definisci il layout
sg.theme('LightGreen2')
layout = [
    [
        sg.Column(
            [
                [sg.Text("Seleziona la porta seriale:")],
                [
                    sg.Combo(
                        get_available_ports(),
                        size=(30, 1),
                        key="-PORT-",
                        enable_events=True,
                    )
                ],
                [sg.Text("Seleziona il baudrate:")],
                [sg.Combo(baud_list, size=(30, 1), key="-BAUD-", default_value="115200")],
                [sg.Multiline(size=(50, 10), key="-OUTPUT-")],
                [sg.Text("Inserisci il tuo codice identificativo:")],
                [sg.InputText(identificativo, key="-IDENTIFICATIVO-")],
                [sg.Text("Inserisci un valore soglia GSR:")],
                [sg.InputText(key="-GSR-",default_text="0")],
                [sg.Text("Aumento % per suono GSR:")],
                [sg.InputText(key="-PERCINCREASE-",default_text="0")],
                [sg.Text("Su quanti secondi (0 per non attivare il suono):")],
                [sg.InputText(key="-SECINCREASE-",default_text="0")],
                
                [sg.Text("Seleziona un file audio:")],
                [sg.Combo(audio_files, key="-FILE-")],
                [
                    sg.Button("Start", key="-START-"),
                    sg.Button("Stop", key="-STOP-"),
                    sg.Button("Esci", key="-EXIT-"),
                ],
                
                
                
            ],
            vertical_alignment="top",
        ),
        sg.Column(
            [
                
                [sg.Text("Ultimi tre valori:")],
                [sg.Text("", size=(50, 20), key="-LAST_VALUES-")],
                [sg.Text("Timer")],
                [sg.Text("", size=(50, 1), key="-TIMER-")],
            ],
            vertical_alignment="top",
        ),
        sg.Column([[sg.Canvas(key="canvas")], 
                   [sg.Canvas(key="canvas2")]],
                  vertical_alignment="top"
                  ),
        
    ]
]


# Crea la finestra dell'interfaccia grafica
window = sg.Window("OPENBIOFEEDBACK", layout, finalize=True, resizable=True,)


# Creazione iniziale dei grafici e dei canvas
fig, ax = plt.subplots()
fig2, ax2 = plt.subplots()

(line,) = ax.plot(timestamps, values3, color="blue", label="GSR")
(line2,) = ax2.plot(timestamps2, battiti, color="red", label="HR")

line.set_label("GSR")
line2.set_label("HR")
ax.legend(loc="upper left")
ax2.legend(loc="upper left")


def format_xaxis(x, _):
    return format_timer(int(x))


# Formatta asse X hh:mm:ss
ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_xaxis))
ax2.xaxis.set_major_formatter(ticker.FuncFormatter(format_xaxis))

canvas = FigureCanvasTkAgg(fig, master=window["canvas"].TKCanvas)
canvas.draw()
canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

canvas2 = FigureCanvasTkAgg(fig2, master=window["canvas2"].TKCanvas)
canvas2.draw()
canvas2.get_tk_widget().pack(side="top", fill="both", expand=True)

# Imposta clearOn a True per consentire la creazione iniziale dei grafici
clearOn = True


# Loop principale dell'applicazione
while True:
    event, values = window.read(timeout=100)
    if event == "-EXIT-" or event == sg.WIN_CLOSED:
        break

    if event == "-EXIT-" or event == sg.WIN_CLOSED:
        break
    elif event == "-START-":
        (values['-GSR-'])
        if not values["-PORT-"]:
            sg.popup("Seleziona una porta seriale.")
        else:
            try:
                ser = serial.Serial(values["-PORT-"], int(values["-BAUD-"]), timeout=1)
                sg.popup(
                    f"Connessione riuscita alla porta {values['-PORT-']} con baudrate {values['-BAUD-']}."
                )
                reading_serial = True
                collectOn = True
                clearOn = True
                print(clearOn)
                start_time = time_as_int()

            except Exception as e:
                sg.popup(f"Errore di connessione alla porta seriale: {e}")
                continue

        if not ser:
            sg.popup("Connetti alla porta seriale prima di avviare la lettura.")
        else:
            window["-STOP-"].update(disabled=False)

            reading_serial = True

            printOn = True
            collect_serial_data()
            graph_running = True

            if firstRun == False:
                
                graph_thread.start()
                firstRun = True

            selected_file = values["-FILE-"]
            identificativo = values["-IDENTIFICATIVO-"]
            save_identificativo(identificativo)

            if selected_file:
                file_path = os.path.join(audio_folder, selected_file)

                if not is_playing:
                    if pause_position == 0:
                        pygame.mixer.music.load(file_path)
                        pygame.mixer.music.play()
                    else:
                        pygame.mixer.music.play(start=pause_position)

                    is_playing = True
                    window["-STOP-"].update(disabled=False)
                else:
                    sg.popup("Nessun file audio selezionato.")

    elif event == "-STOP-":
        pygame.mixer.music.stop()
        collectOn = False
        window["-STOP-"].update(disabled=True)

    
    try:
        collect_serial_data()
        
        

    except ValueError:
        continue
    
    


# Termina il thread del grafico e chiude la porta seriale
graph_running = False
# graph_thread.join()

if ser:
    ser.close()

# Chiude la finestra dell'interfaccia grafica
window.close()
