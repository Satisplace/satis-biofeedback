# Biofeedback mindfulness by Simone TRavaglini
# Licence GPL3


import csv
import json
import os
import random
import serial
import time
import datetime
from datetime import date
from PIL import Image
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
import tkinter as tk
from tkinter import filedialog

from hrvanalysis import get_frequency_domain_features
#from hrvanalysis import plot_timeseries, plot_distrib, plot_psd, plot_poincare

settings_file_path = os.path.join(os.path.dirname(__file__), "settings.json")


# inizialize variables
ser = None
reading_serial = False
graph_running = False
graphOn = False
firstRun = False

increaseGsrDetect=False
indexIncreaseGsrDetect = 0
playBell=False

sd_nn = 0.0  
rmssd = 0.0  
min_hr = 0.0  
max_hr = 0.0  
mean_hr= 0.0
lfband= 0.0
hfband= 0.0
vlf= 0.0
lfHfRatio = 0.0

timeOverGsrMax = 0

collectOn = False
printOn = False
drawGsrLimit = False
removeGsrLimit = False
drawEmgLimit = False
removeEmgLimit = False

addTopic = False
gsrNow = 0
identificativo = ''


#FUNCTION: save in CSV data
def create_csv_file(data, identificativo, sessione, tipo, lista1, lista2):
    # Verify lists have same lenght
    if len(lista1) != len(lista2):
        raise ValueError("Can't save becouse data lists should have same lenght")

    # Create tkinter windows
    root = tk.Tk()
    root.withdraw()  # hide main windows

    # Ask CSV file name
    nome_file = filedialog.asksaveasfilename(title="Save as", initialfile="output.csv", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])

    if not nome_file:
        return  # user escape

    # Create alist with data
    dati = [(data, identificativo, sessione, tipo, lista1[i], lista2[i]) for i in range(len(lista1))]

    # open csv in write mode
    with open(nome_file, 'w', newline='') as file_csv:
        writer = csv.writer(file_csv)

        # Write CSV header
        writer.writerow(['Date', 'ID', 'Session' ,'Type', 'Time', 'Value'])

        # write CSV dat
        writer.writerows(dati)


# FUNCTION: collect data from serial and print 
def collect_serial_data():
    global ser, decoded_bytes, ser_bytes, currentDateAndTime, timenow, battiti,sd_nn, rmssd, min_hr, max_hr, gsrNow, nn_intervals_list, mean_hr, lfband,hfband,vlf,lfHfRatio, limitGSR, timeOverGsrMax, indexIncreaseGsrDetect, increaseGsrDetect,increaseGSR,playBell
    peakDetectorInterval = int(values['-SECINCREASE-'])
    increaseGsrMax = int(values['-PERCINCREASE-'])
    gsrCalibration = float(values['-GSR-CALIBRATION-'])
    hrGot = False
   
    if ser and collectOn:
             
        
        ser_bytes = ser.readline()
        decoded_bytes = ser_bytes.decode("utf-8").rstrip()
        
        window["-OUTPUT-"].print(decoded_bytes)
        
      
        # Split data
        
        if decoded_bytes.startswith('G-'):
                values3.append(float(decoded_bytes[2:])+gsrCalibration)  # Remove 'G-' e convert in float
                timestamps.append(time_as_int() - start_time)
                gsrNow = float(decoded_bytes[2:]) + gsrCalibration
                
                
                if len(values3)-indexIncreaseGsrDetect > peakDetectorInterval:
                    increaseGsrDetect=False 
                
                if (len(values3)>peakDetectorInterval+1) and (values3[len(values3)-(peakDetectorInterval+1)] != 0):
                    increaseGSR=(values3[len(values3)-1]-values3[len(values3)-(peakDetectorInterval+1)])/values3[len(values3)-(peakDetectorInterval+1)]*100
                    
                    if increaseGSR>increaseGsrMax and increaseGsrDetect==False:
                        increaseGsrDetect=True
                        print("play sound")
                        playBell=True
                        
                        indexIncreaseGsrDetect=len(values3)-1    
                
                    
                
        elif decoded_bytes.startswith('H-'):
                values2.append(int(decoded_bytes[2:]))  # Remove 'H-' e convert in int
                timestamps2.append(time_as_int() - start_time)
                
                hrGot = True
                
        elif decoded_bytes.startswith('E-'):
                emgSeries.append(float(decoded_bytes[2:]))  # Remove 'E-' e convert in int
                timestamps3.append(time_as_int() - start_time) 
                
                


        
        if hrGot:
            #remove peak 
            indici_picchi, _ = find_peaks(values2)
            valori_senza_picchi = np.delete(values2, indici_picchi)
            rr_intervals_without_outliers = remove_outliers(rr_intervals=values2,  
                                                    low_rri=450, high_rri=1340)
            interpolated_rr_intervals = interpolate_nan_values(rr_intervals=rr_intervals_without_outliers,
                                                    interpolation_method="linear")
            # This remove ectopic beats from signal
            nn_intervals_list = remove_ectopic_beats(rr_intervals=interpolated_rr_intervals, method="malik")
            
            
            if len(nn_intervals_list) > 0:  # list it's not empty

            
                # This replace ectopic beats nan values with linear interpolation
                interpolated_nn_intervals = interpolate_nan_values(rr_intervals=nn_intervals_list)
                interpolati = interpolated_nn_intervals
                battiti = [60000 / x  for x in interpolati] #calculate beat

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
            
        
        
        window["-LAST_VALUES_GSR-"].update("")
        window["-LAST_VALUES_HR-"].update("")
        last_values_str_gsr = ""  
        last_values_str_hr = ""  
       
        last_values_str_gsr = f"GSR:{gsrNow:.2f}"
        last_values_str_hr = f"SDNN:{sd_nn:.2f} RMSSD:{rmssd:.2f} minHR:{min_hr:.2f} maxHR:{max_hr:.2f} Mean HR:{mean_hr:.2f}\nLF:{lfband:.2f} HF:{hfband:.2f} VLF:{vlf:.2f} LF/HF:{lfHfRatio:.2f}"
        window["-LAST_VALUES_GSR-"].update(last_values_str_gsr)
        window["-LAST_VALUES_HR-"].update(last_values_str_hr)
        # update timer
        timenow = format_timer(time_as_int() - start_time)
        window['-TIMER-'].update(timenow)
        
        
#FUNCTION: play bell based on increase of GSR    
def play_bell():
   
    pygame.init()
    pygame.mixer.init()
    file_mp3 = 'bell.wav'
    pygame.mixer.music.load(file_mp3)
    pygame.mixer.music.play()

   
   

# FUNCTION: Update graph
def update_graph():
    global ax, ax2, ax3, clearOn, playBell, drawGsrLimit, removeGsrLimit, addTopic, drawEmgLimit, removeEmgLimit, graphOn
    
            
    while graph_running:
        
        
        if playBell == True:
            play_bell()
            playBell=False
        
        if clearOn:
            timestamps.clear()
            timestamps2.clear()
            timestamps3.clear()
            values2.clear()
            values3.clear()
            battiti.clear()
            emgSeries.clear()
            
            values2.append(1000)
            battiti.append(60)
            values3.append(0)
            emgSeries.append(1)
            timestamps.append(time_as_int() - start_time)
            timestamps2.append(time_as_int() - start_time)
            timestamps3.append(time_as_int() - start_time)
            ax.clear()
            ax2.clear()
            ax3.clear()
            

            (line,) = ax.plot(timestamps, values3, color="blue", label="GSR")
            (line2,) = ax2.plot(timestamps2, battiti, color="red", label="HR")
            (line3,) = ax3.plot(timestamps3, emgSeries, color="green", label="EMG")
            line.set_label("GSR")
            line2.set_label("HR")
            line3.set_label("EMG")
            ax.legend(loc="upper left")
            ax2.legend(loc="upper left")
            ax3.legend(loc="upper left")


            def format_xaxis(x, _):
                return format_timer(int(x))


            # Format X axis hh:mm:ss
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_xaxis))
            ax2.xaxis.set_major_formatter(ticker.FuncFormatter(format_xaxis))
            ax3.xaxis.set_major_formatter(ticker.FuncFormatter(format_xaxis))

            clearOn = False
        
        
            
        if len(battiti) == len(timestamps2) and len(values3) == len(timestamps) and len(emgSeries) == len(timestamps3):
        
            if drawGsrLimit == True:
               
               
               limitGSR=int(values['-GSR-'])
               ax.axhline(y=limitGSR, color='r', linestyle='--', linewidth=2)
               drawGsrLimit = False
            
            #if removeGsrLimit == True:
             #  #limitGSR=int(values['-GSR-'])
              # # Trova tutte le linee orizzontali (axhline) con lo stesso colore e stile
               #lines_to_remove = [line for line in ax.lines if line.get_color() == 'r' and line.get_linestyle() == '--']
    
                # Rimuovi le linee trovate
               #for line in lines_to_remove:
               #     line.remove()
               #removeGsrLimit = False
               
            
            if drawEmgLimit == True:
                             
               limitEMG=int(values['-EMG-'])
               ax3.axhline(y=limitEMG, color='r', linestyle='--', linewidth=2)
               drawEmgLimit = False
            
            #if removeEmgLimit == True:
               #limitEMG=int(values['-EMG-'])
               # Trova tutte le linee orizzontali (axhline) con lo stesso colore e stile
             #  lines_to_remove = [line3 for line3 in ax3.lines if line3.get_color() == 'r' and line3.get_linestyle() == '--']
    
                # Rimuovi le linee trovate
              # for line3 in lines_to_remove:
               #     line3.remove()
               #removeEmgLimit = False
               
            
            if addTopic == True:
               timeTopic = time_as_int() - start_time
               print(timeTopic)
               topicName=values['-TOPIC-']
               print(topicName)
               ax.axvline(x=timeTopic, color='red', linestyle='--')
               ax.text(timeTopic, 1, topicName, color='black', rotation=90, va='center')
               ax2.axvline(x=timeTopic, color='red', linestyle='--')
               ax2.text(timeTopic, 10, topicName, color='black', rotation=90, va='center')
               ax3.axvline(x=timeTopic, color='red', linestyle='--')
               ax3.text(timeTopic, 300, topicName, color='black', rotation=90, va='center')

               
               addTopic = False
            
            
            line.set_data(timestamps, values3)
            line2.set_data(timestamps2, battiti)
            line3.set_data(timestamps3, emgSeries)
            ax.relim()
            ax.autoscale_view()
            ax2.relim()
            ax2.autoscale_view()
            ax3.relim()
            ax3.autoscale_view()


            # set 5 values max on X axis
            max_ticks = 5  
            ax.xaxis.set_major_locator(plt.MaxNLocator(max_ticks))
            ax2.xaxis.set_major_locator(plt.MaxNLocator(max_ticks))
            ax3.xaxis.set_major_locator(plt.MaxNLocator(max_ticks))

            if graphOn:    
                canvas.draw()
                canvas2.draw()
                canvas3.draw()
               

            time.sleep(0.1)







# create graph thread
graph_thread = threading.Thread(target=update_graph)


# funzione per salvare l'identificativo
#def save_identificativo(identificativo):
    #config = configparser.ConfigParser()
    #config.read("config.ini")
    #config["SETTINGS"] = {"identificativo": identificativo}
    #with open("config.ini", "w") as configfile:
        #config.write(configfile)


# funzione per caricare l'identificativo
#def load_identificativo():
    #config = configparser.ConfigParser()
    #config.read("config.ini")
    #return config.get("SETTINGS", "identificativo")


# se non ancora creato lo aggiunge al file config.ini
#if not os.path.isfile("config.ini"):
    #with open("config.ini", "w") as configfile:
        #configfile.write("[SETTINGS]\nidentificativo = \n")

# carico l'identificativo
#identificativo = load_identificativo()


# FUNCTION: time as int
def time_as_int():
    return int(round(time.time() * 100))


# FUNCTION: format time
def format_timer(elapsed_time):
    hours = elapsed_time // 360000
    minutes = (elapsed_time % 360000) // 6000
    seconds = (elapsed_time % 6000) // 100
    return f"{hours:02}:{minutes:02}:{seconds:02}"


# Set audio
audio_folder = "AUDIO"
audio_files = [
    f for f in os.listdir(audio_folder) if f.endswith(".mp3") or f.endswith(".wav")
]
pygame.init()
pygame.mixer.init()
is_playing = False



# Inizialice lists to save data get from serial
values1 = []
values2 = []
values3 = []
emgSeries = []
timestamps = []
timestamps2 = []
timestamps3 = []
interpolati = []
battiti = []


# FUNTCTION: gest available ports
def get_available_ports():
    import serial.tools.list_ports

    ports = list(serial.tools.list_ports.comports())
    return [port.device for port in ports]

# List of baudrate
baud_list = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]


# Create canvas frame
frame_gsr = [
    [sg.Canvas(key="canvas")],
    [sg.Text("Set limit:",background_color="white", text_color="black"), sg.InputText(key="-GSR-",default_text="0"), sg.Button("Add", key="-DRAW-GSR-")],
    [sg.Text("", size=(100, 2), key="-LAST_VALUES_GSR-",background_color="white", text_color="black"), ],
   
    
    
]
frameGSR = sg.Frame("", frame_gsr, background_color="white",key="-FRAME-GSR-")


frame_hr = [
    [sg.Canvas(key="canvas2")],
    [sg.Text("", size=(100, 2), key="-LAST_VALUES_HR-", background_color="white",text_color="black")],
    
   
]
frameHR = sg.Frame("", frame_hr, background_color="white",key="-FRAME-HR-")

frame_emg = [
    [sg.Canvas(key="canvas3")],
    [sg.Text("Set limit:",background_color="white", text_color="black"), sg.InputText(key="-EMG-",default_text="0"), sg.Button("Add", key="-DRAW-EMG-")],
    [sg.Text("", size=(100, 2), key="-LAST_VALUES_EMG-",background_color="white",text_color="black")],
    
   
]
frameEMG = sg.Frame("", frame_emg, background_color="white",key="-FRAME-EMG-")




# Set layout
sg.theme('Lightgreen2')
tab1_layout = [
    [
        sg.Column(
            [
                [sg.Text("Select serial port:")],
                [
                    sg.Combo(
                        get_available_ports(),
                        size=(30, 1),
                        key="-PORT-",
                        enable_events=True,
                    )
                ],
                [sg.Text("Select baudrate:")],
                [sg.Combo(baud_list, size=(30, 1), key="-BAUD-", default_value="115200")],
                [sg.Multiline(size=(50, 10), key="-OUTPUT-")],
                
                
                [sg.Text("Select audio file:")],
                [sg.Combo(audio_files, key="-FILE-")],
                [
                    sg.Button("Start", key="-START-"),
                    sg.Button("Stop", key="-STOP-"),
                    sg.Button("Exit", key="-EXIT-"),
                ],
                [sg.Button("Export GSR", key="-SALVA-GSR-")],
                [sg.Button("Export HR", key="-SALVA-HR-")],
                [sg.Button("Export EMG", key="-SALVA-EMG-")],
                [sg.Text("Timer")],
                [sg.Text("", size=(50, 1), key="-TIMER-")],
                [sg.Text("Insert topic:")], 
                [sg.InputText(key="-TOPIC-")],
                [sg.Button("Add", key="-ADD-TOPIC-")],
                
                
                
            ],
            vertical_alignment="top",  size=(None, 1080),
        ),
        
        sg.Column([[frameGSR],
                   [frameEMG], 
            ],
                  vertical_alignment="top", size=(800,1000)
                  ),
        sg.Column([
                   [frameHR]],
                  vertical_alignment="top",  size=(800,1000)
                  ),
        
    ]
]


tab2_layout = [
    [
        
        sg.Column(
            [
                
                [sg.Text("Inserist you ID:")],
                [sg.InputText(identificativo, key="-IDENTIFICATIVO-")],
                [sg.Text("Calibrate GSR:")],
                [sg.InputText(key="-GSR-CALIBRATION-",default_text="0")],
                [sg.Text("Active flow")],  
                [sg.Checkbox("Start GSR", key="-ENABLE-GSR-", default=True)],  
                [sg.Checkbox("Start HEART RATE", key="-ENABLE-HR-", default=True)],  
                [sg.Checkbox("Start EMG", key="-ENABLE-EMG-", default=False)],  
                [
                    sg.Button("SAVE", key="-SAVE-SETTINGS-"),
                    sg.Button("LOAD", key="-LOAD-SETTINGS-"),
                    
                ],
                [sg.Text("ALERT")],
                
                [sg.Text("Percent increase for GSR sound:")],
                [sg.InputText(key="-PERCINCREASE-",default_text="0")],
                [sg.Text("How many seconds (0 to silence):")],
                [sg.InputText(key="-SECINCREASE-",default_text="0")],
                
              
                
            ],
            vertical_alignment="top",
        ),
        
        
    ]
]


layout = [
    [
        sg.TabGroup(
            [
                [
                    sg.Tab("Data management", tab1_layout, key="-TAB1-"),
                    sg.Tab("Settings", tab2_layout, key="-TAB2-"),
                ]
            ]
        )
    ]
]


# Create interface
window = sg.Window("OPENBIOFEEDBACK", layout, size=(1920, 1080),finalize=True, resizable=True,)


#load settings
try:
    with open(settings_file_path, "r") as file:
        settings = json.load(file)
except Exception as e:
    print(f"Errore durante il caricamento delle impostazioni: {e}")
        
window["-IDENTIFICATIVO-"].update(settings.get("identificativo", ""))
window["-GSR-"].update(settings.get("gsr_threshold", ""))
window["-PERCINCREASE-"].update(settings.get("perc_increase", ""))
window["-SECINCREASE-"].update(settings.get("sec_increase", ""))
window["-ENABLE-GSR-"].update(settings.get("enable_gsr", False))
window["-ENABLE-HR-"].update(settings.get("enable_hr", False))
window["-ENABLE-EMG-"].update(settings.get("enable_emg", False))


# First creation of graph
fig, ax = plt.subplots()
fig2, ax2 = plt.subplots()
fig3, ax3 = plt.subplots()

(line,) = ax.plot(timestamps, values3, color="blue", label="GSR")
(line2,) = ax2.plot(timestamps2, battiti, color="red", label="HR")
(line3,) = ax3.plot(timestamps3, emgSeries, color="green", label="EMG")

line.set_label("GSR")
line2.set_label("HR")
line3.set_label("EMG")
ax.legend(loc="upper left")
ax2.legend(loc="upper left")
ax3.legend(loc="upper left")



def format_xaxis(x, _):
    return format_timer(int(x))


# Formatt X hh:mm:ss
ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_xaxis))
ax2.xaxis.set_major_formatter(ticker.FuncFormatter(format_xaxis))
ax3.xaxis.set_major_formatter(ticker.FuncFormatter(format_xaxis))

canvas = FigureCanvasTkAgg(fig, master=window["canvas"].TKCanvas)
canvas.draw()
canvas.get_tk_widget().pack(side="top", fill="both", expand=True)


canvas2 = FigureCanvasTkAgg(fig2, master=window["canvas2"].TKCanvas)
canvas2.draw()
canvas2.get_tk_widget().pack(side="top", fill="both", expand=True)

canvas3 = FigureCanvasTkAgg(fig3, master=window["canvas3"].TKCanvas)
canvas3.draw()
canvas3.get_tk_widget().pack(side="top", fill="both", expand=True)




# set canvas dimensions
canvas.get_tk_widget().configure(height=400)
canvas2.get_tk_widget().configure(height=400)
canvas3.get_tk_widget().configure(height=400)


# Set clearOn a True for first creation
clearOn = True


#################################### MAIN Loop #################################################
while True:
    event, values = window.read(timeout=100)
    
    
    
    gsr_enabled = values["-ENABLE-GSR-"]
    emg_enabled = values["-ENABLE-EMG-"]
    hr_enabled = values["-ENABLE-HR-"]
    sessionName = values["-FILE-"]
    
    if gsr_enabled:
        window['-FRAME-GSR-'].update(visible=True)  

    else:
        window['-FRAME-GSR-'].update(visible=False)  
    
    if emg_enabled:
        window['-FRAME-EMG-'].update(visible=True)  

    else:
        window['-FRAME-EMG-'].update(visible=False)  
        
    if hr_enabled:
        window['-FRAME-HR-'].update(visible=True)  

    else:
        window['-FRAME-HR-'].update(visible=False) 

    if event == "-DRAW-GSR-":
        drawGsrLimit = True
    
    if event == "-REMOVE-GSR-":
        removeGsrLimit = True
        
    if event == "-DRAW-EMG-":
        drawEmgLimit = True
    
    if event == "-REMOVE-EMG-":
        removeEmgLimit = True

    if event == "-ADD-TOPIC-":
            addTopic = True
        
    
    
    #SAVE DATA
    if event == "-SALVA-GSR-":
        dateToday = date.today()
        create_csv_file(dateToday, identificativo, sessionName, "GSR", timestamps, values3)
        
    if event == "-SALVA-EMG-":
        dateToday = date.today()
        create_csv_file(dateToday, identificativo, sessionName, "EMG", timestamps3, emgSeries)
        
    if event == "-SALVA-HR-":
        dateToday = date.today()
        create_csv_file(dateToday, identificativo, sessionName, "HR", timestamps2, values2)
        
    
    
    
    
    
    #SAVE SETTINGS
    if event == "-SAVE-SETTINGS-":
        print("salvo")
        settings = {
                        "identificativo": window["-IDENTIFICATIVO-"].get(),
                        "gsr_threshold": int(window["-GSR-"].get()),
                        "perc_increase": int(window["-PERCINCREASE-"].get()),
                        "sec_increase": int(window["-SECINCREASE-"].get()),
                        "enable_gsr": window["-ENABLE-GSR-"].get(),
                        "enable_hr": window["-ENABLE-HR-"].get(),
                        "enable_emg": window["-ENABLE-EMG-"].get(),
                    }
        print(settings)
        # Salva in json file
        try:
            with open(settings_file_path, "w") as file:
                json.dump(settings, file)
        except Exception as e:
            print(f"Errore durante il salvataggio delle impostazioni: {e}")

        
    #load settings
    if event =="-LOAD-SETTINGS-":
        try:
            with open(settings_file_path, "r") as file:
                settings = json.load(file)
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        window["-IDENTIFICATIVO-"].update(settings.get("identificativo", ""))
        window["-GSR-"].update(settings.get("gsr_threshold", ""))
        window["-PERCINCREASE-"].update(settings.get("perc_increase", ""))
        window["-SECINCREASE-"].update(settings.get("sec_increase", ""))
        window["-ENABLE-GSR-"].update(settings.get("enable_gsr", False))
        window["-ENABLE-HR-"].update(settings.get("enable_hr", False))
        window["-ENABLE-EMG-"].update(settings.get("enable_emg", False))
    
    
    
    if event == "-EXIT-" or event == sg.WIN_CLOSED:
        break

    if event == "-EXIT-" or event == sg.WIN_CLOSED:
        break
    elif event == "-START-":
        window["-SALVA-GSR-"].update(disabled=True)
        graphOn = True
        (values['-GSR-'])
        if not values["-PORT-"]:
            sg.popup("Select serial port")
        else:
            try:
                ser = serial.Serial(values["-PORT-"], int(values["-BAUD-"]), timeout=1)
                sg.popup(
                    f"Connected port {values['-PORT-']} with baudrate {values['-BAUD-']}."
                )
                reading_serial = True
                collectOn = True
                clearOn = True
                print(clearOn)
                start_time = time_as_int()

            except Exception as e:
                sg.popup(f"Connection Error: {e}")
                continue

        if not ser:
            sg.popup("Connect serial port")
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
        graphOn=False
        window["-SALVA-GSR-"].update(disabled=False)
        pygame.mixer.music.stop()
        collectOn = False
        window["-STOP-"].update(disabled=True)

    
    try:
        collect_serial_data()
        
        

    except ValueError:
        continue
    
    


# End graph tread
graph_running = False
# graph_thread.join()

if ser:
    ser.close()

# Close windows
window.close()
