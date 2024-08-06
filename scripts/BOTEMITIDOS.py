import os
import shutil
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
import glob


# Crear Carpeta SRIBOT EN DOCUMENTOS
documents_folder = 'C:\\ia\\SRIBOT'
os.makedirs(documents_folder, exist_ok=True)

# Crear carpeta XML dentro de SRIBOT
xml_folder = os.path.join(documents_folder, 'XML', 'EMITIDAS')
os.makedirs(xml_folder, exist_ok=True)

# Crear subcarpetas si no existen
subcarpetas = ['FacturasE', 'LiquidacionesE', 'NotasCreditoE', 'NotasDebitoE', 'RetencionesE']
for subcarpeta in subcarpetas:
    os.makedirs(os.path.join(xml_folder, subcarpeta), exist_ok=True)

# Configuración del navegador Chrome
chrome_options = Options()
chrome_options.add_argument("--allow-running-insecure-content")  # Permitir contenido inseguro
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": xml_folder,  # Cambiar la ruta de descarga inicial
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# Configuración del Bot
chrome_options.add_extension("C:\\Resolver.crx")

# Función para procesar los archivos TXT y generar archivos XML
def procesar_archivos_txt():
    url = "https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline"
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": ""
    }

    def crear_body(clave_acceso):
        return f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ec="http://ec.gob.sri.ws.autorizacion">
        <soapenv:Header/>
        <soapenv:Body>
            <ec:autorizacionComprobante>
                <claveAccesoComprobante>{clave_acceso}</claveAccesoComprobante>
            </ec:autorizacionComprobante>
        </soapenv:Body>
    </soapenv:Envelope>"""

    # Buscar en todas las subcarpetas de la carpeta XML
    for root, dirs, files in os.walk(xml_folder):
        archivos_txt = glob.glob(os.path.join(root, "*.txt"))
        for ruta_txt in archivos_txt:
            with open(ruta_txt, "r", encoding="latin-1") as file:
                lines = file.readlines()

            claves_acceso = []
            for line in lines[1:]:
                columns = line.split("\t")
                if len(columns) > 2:
                    clave_acceso = columns[2].strip()
                    if clave_acceso:
                        claves_acceso.append(clave_acceso)

            for clave_acceso in claves_acceso:
                # Verificar si el archivo XML ya existe
                ruta_archivo = os.path.join(root, f"{clave_acceso}.xml")
                if os.path.exists(ruta_archivo):
                    print(f"El archivo {ruta_archivo} ya existe. Saltando...")
                    continue

                body = crear_body(clave_acceso)
                response = requests.post(url, data=body, headers=headers)

                if response.status_code == 200:
                    response_xml = ET.fromstring(response.text)
                    ns = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                          'ns2': 'http://ec.gob.sri.ws.autorizacion'}

                    autorizacion_response = response_xml.find('.//ns2:autorizacionComprobanteResponse', ns)
                    if autorizacion_response is not None:
                        respuesta_autorizacion = autorizacion_response.find('RespuestaAutorizacionComprobante', ns)
                        if respuesta_autorizacion is not None:
                            autorizaciones = respuesta_autorizacion.find('autorizaciones', ns)
                            if autorizaciones is not None:
                                autorizacion = autorizaciones.find('autorizacion', ns)
                                if autorizacion is not None:
                                    estado = autorizacion.find('estado').text
                                    numero_autorizacion = autorizacion.find('numeroAutorizacion').text
                                    fecha_autorizacion = autorizacion.find('fechaAutorizacion').text
                                    ambiente = autorizacion.find('ambiente').text
                                    comprobante = autorizacion.find('comprobante').text

                                    nuevo_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
                                    <autorizacion>
                                    <estado>{estado}</estado>
                                    <numeroAutorizacion>{numero_autorizacion}</numeroAutorizacion>
                                    <fechaAutorizacion>{fecha_autorizacion}</fechaAutorizacion>
                                    <ambiente>{ambiente}</ambiente>
                                    <comprobante><![CDATA[{comprobante}]]></comprobante>
                                    <mensajes/>
                                    </autorizacion>"""

                                    with open(ruta_archivo, "w", encoding="utf-8") as f:
                                        f.write(nuevo_xml)

                                    print(f"Archivo guardado en: {ruta_archivo}")
                                else:
                                    print(f"No se encontró el elemento 'autorizacion' para la clave {clave_acceso}.")
                            else:
                                print(f"No se encontró el elemento 'autorizaciones' para la clave {clave_acceso}.")
                        else:
                            print(f"No se encontró el elemento 'RespuestaAutorizacionComprobante' para la clave {clave_acceso}.")
                    else:
                        print(f"No se encontró el elemento 'autorizacionComprobanteResponse' para la clave {clave_acceso}.")
                else:
                    print(f"Error en la solicitud para la clave {clave_acceso}. Estado: {response.status_code}")

# Función para limpiar carpetas seleccionadas
def limpiar_carpetas():
    seleccion_subcarpeta = subcarpeta_var.get()
    if seleccion_subcarpeta == "No":
        messagebox.showinfo("Información", "No se ha limpiado ninguna carpeta.")
    elif seleccion_subcarpeta == "Todas":
        for subcarpeta in subcarpetas:
            shutil.rmtree(os.path.join(xml_folder, subcarpeta))
            os.makedirs(os.path.join(xml_folder, subcarpeta), exist_ok=True)
        messagebox.showinfo("Éxito", "Todas las subcarpetas han sido limpiadas.")
    else:
        shutil.rmtree(os.path.join(xml_folder, seleccion_subcarpeta))
        os.makedirs(os.path.join(xml_folder, seleccion_subcarpeta), exist_ok=True)
        messagebox.showinfo("Éxito", f"La subcarpeta {seleccion_subcarpeta} ha sido limpiada.")
    ventana_opciones.destroy()
    seleccionar_opcion_procesar()

# Crear ventana Tkinter para opciones de limpieza
def ventana_limpiar_carpetas():
    global subcarpeta_var, ventana_opciones

    ventana_opciones = tk.Tk()
    ventana_opciones.title("Opciones de Limpieza de Carpetas")

    ancho_ventana_opciones = 400
    alto_ventana_opciones = 200

    ancho_pantalla = ventana_opciones.winfo_screenwidth()
    alto_pantalla = ventana_opciones.winfo_screenheight()

    x = (ancho_pantalla // 2) - (ancho_ventana_opciones // 2)
    y = (alto_pantalla // 2) - (alto_ventana_opciones // 2)

    ventana_opciones.geometry(f"{ancho_ventana_opciones}x{alto_ventana_opciones}+{x}+{y}")

    label = tk.Label(ventana_opciones, text="¿Desea eliminar el contenido de las carpetas?")
    label.pack(pady=10)

    subcarpeta_var = tk.StringVar()
    subcarpeta_combo = ttk.Combobox(ventana_opciones, textvariable=subcarpeta_var, state="readonly")
    subcarpeta_combo['values'] = ["No", "Todas"] + subcarpetas
    subcarpeta_combo.pack(pady=5)

    boton_aceptar = tk.Button(ventana_opciones, text="Aceptar", command=limpiar_carpetas)
    boton_aceptar.pack(pady=10)

    ventana_opciones.mainloop()

# Ventana emergente para seleccionar la opción de procesamiento
def seleccionar_opcion_procesar():
    def enviar_seleccion():
        opcion_seleccionada = combobox_procesar.get()
        if opcion_seleccionada == "Sí":
            procesar_archivos_txt()
        ventana.destroy()

    ventana = tk.Tk()
    ventana.title("Seleccione una opción")

    # Obtener el ancho y alto de la pantalla
    ancho_pantalla = ventana.winfo_screenwidth()
    alto_pantalla = ventana.winfo_screenheight()

    # Establecer dimensiones de la ventana
    ancho_ventana = 380
    alto_ventana = 150

    # Calcular la posición x e y para centrar la ventana
    x = (ancho_pantalla // 2) - (ancho_ventana // 2)
    y = (alto_pantalla // 2) - (alto_ventana // 2)

    # Establecer la geometría de la ventana
    ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")

    tk.Label(ventana, text="¿Desea descargar los comprobantes de los archivos TXT existentes?").pack(pady=10)

    opciones = ["Seleccione una opción", "Sí", "No"]
    combobox_procesar = ttk.Combobox(ventana, values=opciones, state="readonly")
    combobox_procesar.pack(pady=10)
    combobox_procesar.current(0)  # Selecciona la primera opción por defecto

    tk.Button(ventana, text="Aceptar", command=enviar_seleccion).pack(pady=10)

    ventana.mainloop()

# Iniciar la ventana de limpieza de carpetas
ventana_limpiar_carpetas()