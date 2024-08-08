import os
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

username = sys.argv[1]
password = sys.argv[2]
mesemitidos = sys.argv[3]
nombremesemitidos = sys.argv[4]
diaemitidos = sys.argv[5]
directory = sys.argv[6]
anioemitidos = sys.argv[7]

# Crear Carpeta SRIBOT EN DOCUMENTOS
documents_folder = directory
os.makedirs(documents_folder, exist_ok=True)

# Crear carpeta XML dentro de SRIBOT
xml_folder = os.path.join(documents_folder, 'XML', f'{anioemitidos}', f'{nombremesemitidos}', 'EMITIDAS')
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

# Ejecutar la función para procesar y descargar los archivos XML
procesar_archivos_txt()
