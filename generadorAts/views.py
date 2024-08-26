from django.shortcuts import render

# Create your views here.

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
import subprocess
import os
import threading
import shutil
import json
import datetime
import select
import subprocess
import os
import sys
import time
import shutil
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from xml.etree import ElementTree as ET
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from django.core.cache import cache
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from tkinter import Tk
from tkinter.filedialog import asksaveasfilename
from collections import defaultdict
import os
from django.db import connection
from .models import xmlRegister

# Descargar Facturas Recibidas
def ejecutar_script(username, password, mes, nombremesrecibidos, dia, tipo_comprobante, directory, anio):
    try:
        tipo_comprobante_nombres = {
            "1": "Facturas",
            "2": "Liquidaciones",
            "3": "NotasCredito",
            "4": "NotasDebito",
            "6": "Retenciones"
        }
        sendState('Esperando ejecución')
        # Obtener el nombre de la carpeta del tipo de comprobante
        tipo_comprobante_nombre = tipo_comprobante_nombres.get(tipo_comprobante, "Desconocido")
        tipo_comprobante_folder = os.path.join(f"{directory}\\XML\\{anio}\\{nombremesrecibidos}\\RECIBIDAS", tipo_comprobante_nombre)
        os.makedirs(tipo_comprobante_folder, exist_ok=True)

        continue_proccess, dbName, missing_elements = verify_data(tipo_comprobante_folder)
        sendState('Creando carpetas ...')

        if continue_proccess == True:
            documents_folder = directory
            os.makedirs(documents_folder, exist_ok=True)

            xml_folder = os.path.join(documents_folder, 'XML')
            os.makedirs(xml_folder, exist_ok=True)

            # Configuración del navegador Chrome
            chrome_options = Options()
            chrome_options.add_argument("--allow-running-insecure-content")  # Permitir contenido inseguro
            chrome_options.add_experimental_option("prefs", {
                "download.default_directory": xml_folder,  # Cambiar la ruta de descarga
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            })
            chrome_options.add_extension("C:\\Resolver.crx")
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                print(f"Error al iniciar ChromeDriver: {e}", flush=True)
                sys.exit(1)
            url = "https://srienlinea.sri.gob.ec/auth/realms/Internet/protocol/openid-connect/auth?client_id=app-sri-claves-angular&redirect_uri=https%3A%2F%2Fsrienlinea.sri.gob.ec%2Fsri-en-linea%2F%2Fcontribuyente%2Fperfil&state=f535d2b5-e613-4f17-8669-fac1a601b292&nonce=089fd62c-1ea9-4f7f-b502-1617eeb0a8ba&response_mode=fragment&response_type=code&scope=openid"
            try:
                driver.get(url)
                # Esperar hasta que el campo de usuario esté presente en la página
                input_usuario = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "usuario"))
                )

                # Ingresar el usuario
                input_usuario.send_keys(username)

                # Esperar hasta que el campo de contraseña esté presente en la página
                input_password = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="password"]'))
                )

                # Ingresar la contraseña
                input_password.send_keys(password)

                # Encontrar el botón de inicio de sesión y hacer clic en él
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="kc-login"]'))
                )
                login_button.click()
                sendState('Ingresando al portal SRI.')

                try:
                    # Saltarse encuesta 24/04/2024
                    ubicarse = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, '//*[@id="mat-dialog-0"]/sri-modal-perfil/sri-titulo-modal-mat/div/div[2]/button/span'))
                    )

                    ubicarse.click()
                    sendState('Resolviendo encuesta')
                except TimeoutException:
                    sendState('Accediendo a los comprobantes.')

                driver.get("https://srienlinea.sri.gob.ec/tuportal-internet/accederAplicacion.jspa?redireccion=57&idGrupo=55")

                # Seleccionar el año
                select_anio_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'frmPrincipal:ano'))
                )
                select_anio = Select(select_anio_element)
                select_anio.select_by_value(anio)
                sendState('Ingresando Año.')

                # Seleccionar el mes
                select_mes_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'frmPrincipal:mes'))
                )
                select_mes = Select(select_mes_element)
                select_mes.select_by_value(mes)
                sendState('Ingresando mes.')

                # Seleccionar el día
                select_dia_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'frmPrincipal:dia'))
                )
                select_dia = Select(select_dia_element)
                select_dia.select_by_value(dia)
                sendState('Ingresando día.')

                # Seleccionar el tipo de comprobante
                tipo_comprobante_select_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'frmPrincipal:cmbTipoComprobante'))
                )
                tipo_comprobante_select = Select(tipo_comprobante_select_element)
                tipo_comprobante_select.select_by_value(tipo_comprobante)
                sendState('Ingresando tipo de comprobante.')

                # Hacer clic en el elemento recaptcha
                sendState('Ejecutando Captcha ...')
                recaptcha_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="btnRecaptcha"]'))
                )
                recaptcha_button.click()

                # Esperar que la IA resuelva el captcha
                sendState('Resolviendo Captcha ...')
                time.sleep(80)
                
                sendState('Consultando comprobantes ...')

                # Función para obtener el valor de numeroAutorizacion de un archivo XML
                def obtener_numero_autorizacion(xml_path):
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
                    numero_autorizacion = root.find('.//numeroAutorizacion').text
                    return numero_autorizacion

                # Función para renombrar los archivos XML descargados
                def renombrar_xmls():
                    # Esperar a que los archivos se descarguen completamente
                    time.sleep(10)

                    # Obtener la lista de archivos XML en el directorio de descargas
                    files = glob.glob(xml_folder + "\\*.xml")

                    # Iterar sobre cada archivo XML
                    for file in files:
                        try:
                            numero_autorizacion = obtener_numero_autorizacion(file)
                            new_filename = f"{xml_folder}\\{numero_autorizacion}.xml"
                            os.rename(file, new_filename)
                            shutil.move(new_filename, tipo_comprobante_folder)
                        except Exception as e:
                            sendState(f"Error al procesar el archivo {file}: {e}")

                    # Eliminar los archivos XML que quedan en la carpeta xml_folder
                    remaining_files = glob.glob(xml_folder + "\\*.xml")
                    for file in remaining_files:
                        try:
                            os.remove(file)
                        except Exception as e:
                            sendState(f"Error al eliminar el archivo {file}: {e}")

                    sendState('Modificando archivos ...')


                # Función para hacer clic en los enlaces y descargar los archivos XML
                def hacer_clic_en_enlace():
                    paginacion_previa = ""
                    while True:
                        try:
                            # Verificar si es la última página
                            span_paginacion = driver.find_element(By.XPATH,
                                                                '/html/body/div[2]/div[2]/div[3]/form[2]/div[5]/div/div[2]/table/tfoot/tr/td/span[3]')
                            texto_paginacion = span_paginacion.text

                            if paginacion_previa == texto_paginacion:
                                break  # Si la paginación es la misma que la anterior, salir del bucle
                            else:
                                paginacion_previa = texto_paginacion

                            # Encuentra todos los elementos tr dentro de la tabla usando XPath
                            elementos_tr = driver.find_elements(By.XPATH,
                                                                "/html/body/div[2]/div[2]/div[3]/form[2]/div[5]/div/div[2]/table/tbody/tr")

                            # Iterar sobre cada enlace y hacer clic
                            for elemento in elementos_tr:
                                enlace = elemento.find_element(By.XPATH, 'td[10]//a')
                                enlace.click()
                                time.sleep(1)  # Espera 1 segundo antes de continuar

                            # Hacer clic en el enlace de paginación
                            enlace_siguiente = driver.find_element(By.XPATH,
                                                                '//*[@id="frmPrincipal:tablaCompRecibidos_paginator_bottom"]/span[4]')
                            enlace_siguiente.click()
                            time.sleep(5)  # Espera 5 segundos para cargar la página siguiente

                            # Mover el cursor del mouse sobre el botón de captcha
                            action = ActionChains(driver)
                            action.move_to_element(recaptcha_button).perform()

                        except:
                            break  # Salir del bucle si no hay más páginas

                    # Llamada a la función para renombrar los archivos XML
                    renombrar_xmls()

                # Llamada a la función para hacer click en los enlaces y descargar los archivos XML
                sendState('Descargando archivos ...')
                hacer_clic_en_enlace()

                sendState('Guardando contenido en la base de datos.')
                # Aqui debe estar la funcion para guardar los registros en la base de datos
                xml_files = glob.glob(os.path.join(tipo_comprobante_folder, '*.xml'))
                save_xml_db(dbName, xml_files, missing_elements)

                # Crear una ventana emergente para mostrar el mensaje
                sendState('Comprobantes descargados exitosamente.')

            except Exception as e:
                print("Error:", e, flush=True)
        else:
            sendState('Los comprobantes de esta fecha se encuentran actualizados.')
            
    except Exception as e:
        print("Excepción al intentar ejecutar el script:", str(e), flush=True)


def sendState(text):
    if text == '':
        cache.set('estado_actual', 'Sin ejecutar')
    else:
        cache.set('estado_actual', text)

def getEstado(request):
    estado = cache.get('estado_actual', 'Sin ejecutar')
    return JsonResponse({'estado': estado})

# Descargar Facturas Recibidas
def ejecutar_script_botemitidos(username, password, mesemitidos, nombremesemitidos, diaemitidos, directory,anioemitidos,tipo_comprobante_emitidos):
    sendStateEmit('Esperando ejecución.')
    time.sleep(1)
        
    tipo_comprobante_nombres = {
        "1": "FacturasE",
        "2": "LiquidacionesE",
        "3": "NotasCreditoE",
        "4": "NotasDebitoE",
        "6": "RetencionesE"
    }

    # Crear Carpeta SRIBOT EN DOCUMENTOS
    documents_folder = directory
    os.makedirs(documents_folder, exist_ok=True)

    xml_folder = os.path.join(documents_folder, 'XML')
    os.makedirs(xml_folder, exist_ok=True)

    # Configuración del navegador Chrome
    chrome_options = Options()
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": directory,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    chrome_options.add_extension(r"C:\Resolver.crx")

    driver = webdriver.Chrome(options=chrome_options)

    def renombrar_archivo_descargado(directory, diaemitidos):
        time.sleep(10)
        """Renombra el archivo TXT descargado agregando el día en el nombre del archivo."""
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):
                old_file = os.path.join(directory, filename)
                new_file = os.path.join(directory, f'{diaemitidos}.txt')
                os.rename(old_file, new_file)
                print(f'Archivo renombrado a {new_file}')

                # Mover el archivo a la carpeta correspondiente del tipo de comprobante en EMITIDAS
                tipo_comprobante_folder = os.path.join(f"{directory}\\XML\\{anioemitidos}\\{nombremesemitidos}\\EMITIDAS", tipo_comprobante_nombres.get(tipo_comprobante_emitidos, "Desconocido"))
                os.makedirs(tipo_comprobante_folder, exist_ok=True)
                
                destination_file = os.path.join(tipo_comprobante_folder, f'{diaemitidos}.txt')

                # Si el archivo ya existe en la carpeta de destino, se sobrescribe
                if os.path.exists(destination_file):
                    os.remove(destination_file)

                shutil.move(new_file, tipo_comprobante_folder)
                print(f"Archivo {new_file} movido y sobrescrito en {tipo_comprobante_folder}", flush=True)


    def procesar_archivos_txt():
        sendStateEmit('Procesando archivo TXT.')
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

        # Buscar en el tipo_comprobante_folder
        for root, dirs, files in os.walk(os.path.join(tipo_comprobante_folder)):
            archivos_txt = glob.glob(os.path.join(root, "*.txt"))
            for ruta_txt in archivos_txt:
                print(f"Procesando archivo TXT: {ruta_txt}")  # Imprimir el archivo TXT que se está procesando
                with open(ruta_txt, "r", encoding="latin-1") as file:
                    lines = file.readlines()

                claves_acceso = []
                for line in lines[1:]:
                    columns = line.split("\t")
                    if len(columns) > 2:
                        clave_acceso = columns[2].strip()
                        if clave_acceso:
                            claves_acceso.append(clave_acceso)

                for indexC,clave_acceso in enumerate(claves_acceso):
                    # Verificar si el archivo XML ya existe
                    ruta_archivo = os.path.join(root, f"{clave_acceso}.xml")
                    if os.path.exists(ruta_archivo):
                        print(f"El archivo {ruta_archivo} ya existe. Saltando...")
                        sendStateEmit(f"El archivo ya existe, cambiando al siguiente ({indexC+1}/{len(claves_acceso)}).")
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
                                        sendStateEmit(f"Archivo guardado correctamente ({indexC+1}/{len(claves_acceso)}).")
                                    else:
                                        sendStateEmit('No se encontró el elemento de autorización.')
                                        print(f"No se encontró el elemento 'autorizacion' para la clave {clave_acceso}.")
                                else:
                                    sendStateEmit('No se encontró el elemento autorizaciones.')
                                    print(f"No se encontró el elemento 'autorizaciones' para la clave {clave_acceso}.")
                            else:
                                sendStateEmit('No se encontró el elemento RespuestaAutorizacionComprobante.')
                                print(f"No se encontró el elemento 'RespuestaAutorizacionComprobante' para la clave {clave_acceso}.")
                        else:
                            print(f"Error en la solicitud para la clave {clave_acceso}. Estado: {response.status_code}")
        sendStateEmit('Descarga completa.')
        time.sleep(2)

    try:
        sendStateEmit('Ingresando al portal SRI.')
        # URL de la página del SRI
        url = "https://srienlinea.sri.gob.ec/auth/realms/Internet/protocol/openid-connect/auth?client_id=app-sri-claves-angular&redirect_uri=https%3A%2F%2Fsrienlinea.sri.gob.ec%2Fsri-en-linea%2F%2Fcontribuyente%2Fperfil&state=f535d2b5-e613-4f17-8669-fac1a601b292&nonce=089fd62c-1ea9-4a7f-b502-1617eeb0a8ba&response_mode=fragment&response_type=code&scope=openid"
        driver.get(url)
        
        # Ingresar usuario y contraseña
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "usuario"))
        ).send_keys(username)
        print("Usuario ingresado con éxito.")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="password"]'))
        ).send_keys(password)
        print("Contraseña ingresada con éxito.")
        
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="kc-login"]'))
        ).click()
        print("Inicio de sesión exitoso.")
        
        # Saltarse encuesta si aparece
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="mat-dialog-0"]/sri-modal-perfil/sri-titulo-modal-mat/div/div[2]/div/div[2]/button'))
            ).click()
            sendState('Resolviendo encuesta')
        except TimeoutException:
            sendState('Accediendo a Comprobantes Emitido')
        
        time.sleep(5)  # Esperar para cargar la página

        # Abrir menú y navegar a la sección de Facturación Electrónica
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="sri-menu"]/span'))
        ).click()
        print("Menú desplegable abierto con éxito.")
        
        sidebar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "mySidebar"))
        )
        WebDriverWait(sidebar, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'FACTURACIÓN ELECTRÓNICA')]"))
        ).click()
        
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="mySidebar"]/p-panelmenu/div/div[4]/div[2]/div/p-panelmenusub/ul/li[4]/a'))
        ).click()
        
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="mySidebar"]/p-panelmenu/div/div[4]/div[2]/div/p-panelmenusub/ul/li[4]/p-panelmenusub/ul/li[2]/a'))
        ).click()
        
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="consultaDocumentoForm:panelPrincipal"]/ul/li[2]/a'))
        ).click()
        
        # Seleccionar el año
        fecha_desde_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="frmPrincipal:calendarFechaDesde_input"]'))
        )
        
        fecha_desde_input.clear()
        fecha_desde_input.send_keys(f'{diaemitidos}/{mesemitidos}/{anioemitidos}')
        sendStateEmit('Ingresando Fecha')
        tipo_comprobante_select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'frmPrincipal:cmbTipoComprobante'))
        )
        tipo_comprobante_select = Select(tipo_comprobante_select_element)
        tipo_comprobante_select.select_by_value(tipo_comprobante_emitidos)

        # Obtener el nombre de la carpeta del tipo de comprobante
        tipo_comprobante_nombre = tipo_comprobante_nombres.get(tipo_comprobante_emitidos, "Desconocido")
        tipo_comprobante_folder = os.path.join(f"{directory}\\XML\\{anioemitidos}\\{nombremesemitidos}\\EMITIDAS", tipo_comprobante_nombre)
        os.makedirs(tipo_comprobante_folder, exist_ok=True)
        print("Carpeta creada para el tipo de comprobante:", tipo_comprobante_nombre, flush=True)
        sendStateEmit("Carpeta creada para el tipo de comprobante:")

        # Hacer clic en el elemento recaptcha
        recaptcha_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="btnRecaptcha"]'))
        )
        
        recaptcha_button.click()

        # Esperar que la IA resuelva el captcha
        sendStateEmit('Resolviendo Captcha ...')
        time.sleep(100)

        # Condicion para cuando no exista inforamcion

        try:
            # Intentar localizar el elemento que indica que hay información
            info_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="frmPrincipal:tablaCompEmitidos:j_idt51"]'))
            )
            print('se encontro info')
            # Si se encuentra el elemento, proceder con la descarga del archivo TXT
            listado_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="frmPrincipal:lnkTxtlistado"]'))
            )
            listado_button.click()
            sendStateEmit('Descargando Txt ...')
            
            # Renombrar y mover archivos descargados
            renombrar_archivo_descargado(directory, diaemitidos)
            procesar_archivos_txt()

        except TimeoutException:
            # Si no se encuentra el elemento, indicar que no hay información disponible
            sendStateEmit('No existe información del día consultado.')
            driver.quit()

    finally:
        driver.quit()


def sendStateEmit(text):
    if text == '':
        cache.set('estado_actual_emitido', 'Sin ejecutar')
    else:
        cache.set('estado_actual_emitido', text)

def getEstadoEmit(request):
    estado = cache.get('estado_actual_emitido', 'Sin ejecutar')
    return JsonResponse({'estado_emitido': estado})

# Crear Reporte Recibidos
def ejecutar_script_reporterecibidos(directory, nombremesmodal, aniomodal):   
    def obtener_archivos_xml(directory):
        xml_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.xml'):
                    xml_files.append(os.path.join(root, file))
        return xml_files


    def procesar_archivos_compras(xml_files):
        dfs_compras = []
        cedula_dfs_compras = []

        for file_path in xml_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()

            root = ET.fromstring(xml_data)
            estado = root.find('.//estado').text
            fecha_autorizacion = root.find('.//fechaAutorizacion').text
            numero_autorizacion = root.find('.//numeroAutorizacion').text
            cdata_node = root.find('.//comprobante').text
            cdata_root = ET.fromstring(cdata_node)

            fecha_emision = cdata_root.find('.//fechaEmision').text
            ruc = cdata_root.find('.//ruc').text
            razon_social = cdata_root.find('.//razonSocial').text
            identificacion_comprador = cdata_root.find('.//identificacionComprador').text

            info_tributaria = cdata_root.find('.//infoTributaria')
            estab = info_tributaria.find('.//estab').text
            ptoEmi = info_tributaria.find('.//ptoEmi').text
            secuencial = info_tributaria.find('.//secuencial').text

            serie = f"{estab}{ptoEmi}"

            subtotal_0 = subtotal_12 = subtotal_5 = subtotal_15 = subtotal_no_objeto_de_impuesto = subtotal_exento_iva = subtotal_iva_diferenciado = 0.0
            iva_12 = iva_5 = iva_15 = iva_no_objeto_impuesto = iva_exento = iva_diferenciado = 0.0

            total_sin_impuestos = float(cdata_root.find('.//totalSinImpuestos').text)
            importe_total = float(cdata_root.find('.//importeTotal').text)

            for impuesto in cdata_root.findall('.//totalImpuesto'):
                codigo_porcentaje = int(impuesto.find('codigoPorcentaje').text)
                base_imponible = float(impuesto.find('baseImponible').text)
                valor = float(impuesto.find('valor').text)

                if codigo_porcentaje == 0:
                    subtotal_0 += base_imponible
                elif codigo_porcentaje == 2:
                    subtotal_12 += base_imponible
                    iva_12 += valor
                elif codigo_porcentaje == 5:
                    subtotal_5 += base_imponible
                    iva_5 += valor
                elif codigo_porcentaje == 4:
                    subtotal_15 += base_imponible
                    iva_15 += valor
                elif codigo_porcentaje == 6:
                    subtotal_no_objeto_de_impuesto += base_imponible
                elif codigo_porcentaje == 7:
                    subtotal_exento_iva += base_imponible
                elif codigo_porcentaje == 8:
                    subtotal_iva_diferenciado += base_imponible

            data = {
                "RUC Proveedor": [ruc],
                "Proveedor": [razon_social],
                "Fecha Emisión": [fecha_emision],
                "Serie": [serie],
                "Secuencial": [secuencial],
                "Número Autorización": [numero_autorizacion],
                "Clave de acceso": [numero_autorizacion],
                "Subtotal 0": [subtotal_0],
                "Subtotal 12": [subtotal_12],
                "Subtotal 5": [subtotal_5],
                "Subtotal 15": [subtotal_15],
                "Subtotal": [total_sin_impuestos],
                "IVA 12": [iva_12],
                "IVA 5": [iva_5],
                "IVA 15": [iva_15],
                "Total": [importe_total],
                "Estado": [estado]
            }
            df = pd.DataFrame(data)

            if len(identificacion_comprador) > 10:
                dfs_compras.append(df)
            elif len(identificacion_comprador) == 10:
                cedula_dfs_compras.append(df)

        if dfs_compras:
            final_compras_df = pd.concat(dfs_compras, ignore_index=True)
        else:
            final_compras_df = pd.DataFrame()

        if cedula_dfs_compras:
            final_cedula_compras_df = pd.concat(cedula_dfs_compras, ignore_index=True)
        else:
            final_cedula_compras_df = pd.DataFrame()

        if not final_compras_df.empty:
            sumas_totales_compras = final_compras_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales_compras["RUC Proveedor"] = ""
            sumas_totales_compras["Proveedor"] = ""
            sumas_totales_compras["Fecha Emisión"] = "Sumas Totales"
            sumas_totales_compras["Serie"] = ""
            sumas_totales_compras["Secuencial"] = ""
            sumas_totales_compras["Número Autorización"] = ""
            sumas_totales_compras["Clave de acceso"] = ""
            sumas_totales_compras["Estado"] = ""
            sumas_totales_compras_df = pd.DataFrame([sumas_totales_compras])
            final_compras_df = pd.concat([final_compras_df, sumas_totales_compras_df], ignore_index=True)

        if not final_cedula_compras_df.empty:
            sumas_totales_cedula_compras = final_cedula_compras_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales_cedula_compras["RUC Proveedor"] = ""
            sumas_totales_cedula_compras["Proveedor"] = ""
            sumas_totales_cedula_compras["Fecha Emisión"] = "Sumas Totales"
            sumas_totales_cedula_compras["Serie"] = ""
            sumas_totales_cedula_compras["Secuencial"] = ""
            sumas_totales_cedula_compras["Número Autorización"] = ""
            sumas_totales_cedula_compras["Clave de acceso"] = ""
            sumas_totales_cedula_compras["Estado"] = ""
            sumas_totales_cedula_compras_df = pd.DataFrame([sumas_totales_cedula_compras])
            final_cedula_compras_df = pd.concat([final_cedula_compras_df, sumas_totales_cedula_compras_df],
                                                ignore_index=True)

        return final_compras_df, final_cedula_compras_df


    def procesar_archivos_liquidacion(xml_files):
        dfs_liquidacion = []
        cedula_dfs_liquidacion = []

        for file_path in xml_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()

            root = ET.fromstring(xml_data)
            estado = root.find('.//estado').text
            fecha_autorizacion = root.find('.//fechaAutorizacion').text
            numero_autorizacion = root.find('.//numeroAutorizacion').text
            cdata_node = root.find('.//comprobante').text
            cdata_root = ET.fromstring(cdata_node)

            fecha_emision = cdata_root.find('.//fechaEmision').text
            ruc = cdata_root.find('.//ruc').text

            info_tributaria = cdata_root.find('.//infoTributaria')
            estab = info_tributaria.find('.//estab').text
            ptoEmi = info_tributaria.find('.//ptoEmi').text
            secuencial = info_tributaria.find('.//secuencial').text

            numero_doc = f"{estab}{ptoEmi}{secuencial}"

            identificacion_proveedor = cdata_root.find('.//infoLiquidacionCompra/identificacionProveedor').text
            razonsocial_proveedor = cdata_root.find('.//infoLiquidacionCompra/razonSocialProveedor').text

            subtotal_0 = subtotal_12 = subtotal_5 = subtotal_15 = subtotal_no_objeto_de_impuesto = subtotal_exento_iva = subtotal_iva_diferenciado = 0.0
            iva_12 = iva_5 = iva_15 = iva_no_objeto_impuesto = iva_exento = iva_diferenciado = 0.0

            total_sin_impuestos = float(cdata_root.find('.//totalSinImpuestos').text)
            importe_total = float(cdata_root.find('.//importeTotal').text)

            for impuesto in cdata_root.findall('.//totalImpuesto'):
                codigo_porcentaje = int(impuesto.find('codigoPorcentaje').text)
                base_imponible = float(impuesto.find('baseImponible').text)
                valor = float(impuesto.find('valor').text)

                if codigo_porcentaje == 0:
                    subtotal_0 += base_imponible
                elif codigo_porcentaje == 2:
                    subtotal_12 += base_imponible
                    iva_12 += valor
                elif codigo_porcentaje == 5:
                    subtotal_5 += base_imponible
                    iva_5 += valor
                elif codigo_porcentaje == 4:
                    subtotal_15 += base_imponible
                    iva_15 += valor
                elif codigo_porcentaje == 6:
                    iva_no_objeto_impuesto += base_imponible
                elif codigo_porcentaje == 7:
                    iva_exento += base_imponible
                elif codigo_porcentaje == 8:
                    iva_diferenciado += base_imponible

            data = {
                "Fecha Emisión": [fecha_emision],
                "Fecha Autorización": [fecha_autorizacion],
                "Identificacion Proveedor": [identificacion_proveedor],
                "#Doc": [numero_doc],
                "# Autorizacion": [numero_autorizacion],
                "Proveedor": [razonsocial_proveedor],
                "Identificación Comprador": [ruc],
                "Subtotal 15": [subtotal_15],
                "Subtotal 0": [subtotal_0],
                "Subtotal 12": [subtotal_12],
                "Subtotal 5": [subtotal_5],
                "Subtotal 15": [subtotal_15],
                "Subtotal": [total_sin_impuestos],
                "IVA 12": [iva_12],
                "IVA 5": [iva_5],
                "IVA 15": [iva_15],
                "Total": [importe_total],
                "Estado": [estado]

            }
            df = pd.DataFrame(data)

            if len(ruc) > 10:
                dfs_liquidacion.append(df)
            elif len(ruc) == 10:
                cedula_dfs_liquidacion.append(df)

        if dfs_liquidacion:
            final_liquidacion_df = pd.concat(dfs_liquidacion, ignore_index=True)
        else:
            final_liquidacion_df = pd.DataFrame()

        if cedula_dfs_liquidacion:
            final_cedula_liquidacion_df = pd.concat(cedula_dfs_liquidacion, ignore_index=True)
        else:
            final_cedula_liquidacion_df = pd.DataFrame()

        if not final_liquidacion_df.empty:
            sumas_totales = final_liquidacion_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales["Fecha Emisión"] = "Sumas Totales"
            sumas_totales["Fecha Autorización"] = ""
            sumas_totales["Identificacion Proveedor"] = ""
            sumas_totales["Proveedor"] = ""
            sumas_totales["Identificación Empresa"] = ""
            sumas_totales["Estado"] = ""
            sumas_totales_df = pd.DataFrame([sumas_totales])
            final_liquidacion_df = pd.concat([final_liquidacion_df, sumas_totales_df], ignore_index=True)

        return final_liquidacion_df, final_cedula_liquidacion_df


    def procesar_archivos_retenciones(xml_files):
        dfs = []

        for file_path in xml_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()

            try:
                root = ET.fromstring(xml_data)
                estado = root.find("estado").text
                fecha_autorizacion = root.find("fechaAutorizacion").text
                numero_autorizacion = root.find("numeroAutorizacion").text

                comprobante_cdata = root.find(".//comprobante").text
                comprobante_xml = ET.fromstring(comprobante_cdata)
                version = comprobante_xml.attrib.get("version", "")

                if version == "1.0.0":
                    info_tributaria = comprobante_xml.find("infoTributaria")
                    nombre_comercial = info_tributaria.find("razonSocial").text if info_tributaria.find(
                        "razonSocial") is not None else ""
                    ruc = info_tributaria.find("ruc").text
                    estab = info_tributaria.find("estab").text
                    ptoEmi = info_tributaria.find("ptoEmi").text
                    secuencial = info_tributaria.find("secuencial").text
                    serie = f"{estab}{ptoEmi}"
                    info_comp_retencion = comprobante_xml.find("infoCompRetencion")
                    fecha_emision = info_comp_retencion.find("fechaEmision").text

                    for impuesto in comprobante_xml.findall("impuestos/impuesto"):
                        codigo_retencion = impuesto.find("codigoRetencion").text
                        base_imponible = float(impuesto.find("baseImponible").text)
                        porcentaje_retener = float(impuesto.find("porcentajeRetener").text)
                        valor_retenido = float(impuesto.find("valorRetenido").text)

                        data = {
                            "Fecha Emisión": [fecha_emision],
                            "Fecha Autorización": [fecha_autorizacion],
                            "Serie": [serie],
                            "Secuencial": [secuencial],
                            "# Autorización": [numero_autorizacion],
                            "RUC": [ruc],
                            "Razon Social": [nombre_comercial],
                            "Codigo Retencion": [codigo_retencion],
                            "Base Imponible": [base_imponible],
                            "Porcentaje Retener": [porcentaje_retener],
                            "Valor Retenido": [valor_retenido],
                            "Estado": [estado],
                            "Versión": [version]
                        }

                        df = pd.DataFrame(data)
                        dfs.append(df)
                elif version == "2.0.0":
                    info_tributaria = comprobante_xml.find("infoTributaria")
                    nombre_comercial = info_tributaria.find("nombreComercial").text if info_tributaria.find(
                        "nombreComercial") is not None else ""
                    razon_social = info_tributaria.find("razonSocial").text if info_tributaria.find(
                        "razonSocial") is not None else ""
                    proveedor = nombre_comercial if nombre_comercial else razon_social
                    ruc = info_tributaria.find("ruc").text
                    estab = info_tributaria.find("estab").text
                    ptoEmi = info_tributaria.find("ptoEmi").text
                    secuencial = info_tributaria.find("secuencial").text
                    serie = f"{estab}{ptoEmi}"
                    info_comp_retencion = comprobante_xml.find("infoCompRetencion")
                    fecha_emision = info_comp_retencion.find("fechaEmision").text
                    doc_sustento = comprobante_xml.find(".//docSustento")
                    num_doc_sustento = doc_sustento.find("numDocSustento").text if doc_sustento is not None else ""

                    for retencion in comprobante_xml.findall(".//retencion"):
                        codigo_retencion = retencion.find("codigoRetencion").text
                        base_imponible = float(retencion.find("baseImponible").text)
                        porcentaje_retener = float(retencion.find("porcentajeRetener").text)
                        valor_retenido = float(retencion.find("valorRetenido").text)
                        codigo = retencion.find("codigo").text
                        codigo = int(codigo)

                        if codigo == 1:
                            descripcion = 'Renta'
                        elif codigo == 2:
                            descripcion = 'Iva'
                        elif codigo == 3:
                            descripcion = 'ICE'
                        elif codigo == 6:
                            descripcion = 'Rendimientos Financieros'
                        elif codigo == 7:
                            descripcion = 'ISD'
                        elif codigo == 8:
                            descripcion = 'Operaciones de Exportación'
                        elif codigo == 9:
                            descripcion = 'Operaciones de Importación'
                        elif codigo == 10:
                            descripcion = 'Servicios Profesionales'

                        data = {
                            "Fecha Emisión": [fecha_emision],
                            "Fecha Autorización": [fecha_autorizacion],
                            "Serie": [serie],
                            "Secuencial": [secuencial],
                            "# Autorización": [numero_autorizacion],
                            "RUC": [ruc],
                            "Razon Social": [proveedor],
                            "Codigo Retencion": [codigo_retencion],
                            "Base Imponible": [base_imponible],
                            "Porcentaje Retener": [porcentaje_retener],
                            "Valor Retenido": [valor_retenido],
                            "Estado": [estado],
                            "Versión": [version],
                            "Tipo de Retención": [descripcion]
                        }

                        df = pd.DataFrame(data)
                        dfs.append(df)
                else:
                    print(f"Versión del comprobante no compatible: {version}. Saltando archivo.")
                    continue

            except Exception as e:
                print(f"Error al procesar el archivo {file_path}: {e}")

        if dfs:
            final_df = pd.concat(dfs, ignore_index=True)
            subtotals = final_df.groupby("Codigo Retencion").agg({
                'Base Imponible': 'sum',
                'Valor Retenido': 'sum'
            }).reset_index()

            output_data = []

            for codigo_retencion, group in final_df.groupby("Codigo Retencion"):
                output_data.append(group)
                subtotal = subtotals[subtotals["Codigo Retencion"] == codigo_retencion]
                subtotal_row = {
                    "Fecha Emisión": "Subtotal",
                    "Fecha Autorización": "",
                    "Serie": "",
                    "Secuencial": "",
                    "# Autorización": "",
                    "RUC": "",
                    "Razon Social": "",
                    "Codigo Retencion": codigo_retencion,
                    "Base Imponible": subtotal["Base Imponible"].values[0],
                    "Porcentaje Retener": "",
                    "Valor Retenido": subtotal["Valor Retenido"].values[0],
                    "Estado": "",
                    "Versión": ""
                }
                output_data.append(pd.DataFrame([subtotal_row]))

            output_df = pd.concat(output_data, ignore_index=True)
        else:
            output_df = pd.DataFrame()

        return output_df


    def procesar_archivos_notas_credito(xml_files):
        dfs_notas_credito = []
        cedula_dfs_notas_credito = []

        for file_path in xml_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()

            root = ET.fromstring(xml_data)
            estado = root.find('.//estado').text
            fecha_autorizacion = root.find('.//fechaAutorizacion').text
            numero_autorizacion = root.find('.//numeroAutorizacion').text
            cdata_node = root.find('.//comprobante').text
            cdata_root = ET.fromstring(cdata_node)

            fecha_emision = cdata_root.find('.//fechaEmision').text
            ruc = cdata_root.find('.//ruc').text
            razon_social = cdata_root.find('.//razonSocial').text
            identificacion_comprador = cdata_root.find('.//identificacionComprador').text

            info_tributaria = cdata_root.find('.//infoTributaria')
            estab = info_tributaria.find('.//estab').text
            ptoEmi = info_tributaria.find('.//ptoEmi').text
            secuencial = info_tributaria.find('.//secuencial').text

            serie = f"{estab}{ptoEmi}"

            subtotal_0 = subtotal_12 = subtotal_5 = subtotal_15 = subtotal_no_objeto_de_impuesto = subtotal_exento_iva = subtotal_iva_diferenciado = 0.0
            iva_12 = iva_5 = iva_15 = iva_no_objeto_impuesto = iva_exento = iva_diferenciado = 0.0

            total_sin_impuestos = float(cdata_root.find('.//totalSinImpuestos').text)
            importe_total = float(cdata_root.find('.//valorModificacion').text)

            for impuesto in cdata_root.findall('.//totalImpuesto'):
                codigo_porcentaje = int(impuesto.find('codigoPorcentaje').text)
                base_imponible = float(impuesto.find('baseImponible').text)
                valor = float(impuesto.find('valor').text)

                if codigo_porcentaje == 0:
                    subtotal_0 += base_imponible
                elif codigo_porcentaje == 2:
                    subtotal_12 += base_imponible
                    iva_12 += valor
                elif codigo_porcentaje == 5:
                    subtotal_5 += base_imponible
                    iva_5 += valor
                elif codigo_porcentaje == 4:
                    subtotal_15 += base_imponible
                    iva_15 += valor

            data = {
                "RUC Proveedor": [ruc],
                "Proveedor": [razon_social],
                "Fecha Emisión": [fecha_emision],
                "Serie": [serie],
                "Secuencial": [secuencial],
                "Número Autorización": [numero_autorizacion],
                "Clave de acceso": [numero_autorizacion],
                "Subtotal 0": [subtotal_0],
                "Subtotal 12": [subtotal_12],
                "Subtotal 5": [subtotal_5],
                "Subtotal 15": [subtotal_15],
                "Subtotal": [total_sin_impuestos],
                "IVA 12": [iva_12],
                "IVA 5": [iva_5],
                "IVA 15": [iva_15],
                "Total": [importe_total],
                "Estado": [estado]
            }
            df = pd.DataFrame(data)

            if len(identificacion_comprador) > 10:
                dfs_notas_credito.append(df)
            elif len(identificacion_comprador) == 10:
                cedula_dfs_notas_credito.append(df)

        if dfs_notas_credito:
            final_notas_credito_df = pd.concat(dfs_notas_credito, ignore_index=True)
        else:
            final_notas_credito_df = pd.DataFrame()

        if cedula_dfs_notas_credito:
            final_cedula_notas_credito_df = pd.concat(cedula_dfs_notas_credito, ignore_index=True)
        else:
            final_cedula_notas_credito_df = pd.DataFrame()

        if not final_notas_credito_df.empty:
            sumas_totales = final_notas_credito_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales["RUC Proveedor"] = ""
            sumas_totales["Proveedor"] = ""
            sumas_totales["Fecha Emisión"] = "Sumas Totales"
            sumas_totales["Serie"] = ""
            sumas_totales["Secuencial"] = ""
            sumas_totales["Número Autorización"] = ""
            sumas_totales["Clave de acceso"] = ""
            sumas_totales["Estado"] = ""
            sumas_totales_df = pd.DataFrame([sumas_totales])
            final_notas_credito_df = pd.concat([final_notas_credito_df, sumas_totales_df], ignore_index=True)

        if not final_cedula_notas_credito_df.empty:
            sumas_totales_cedula = final_cedula_notas_credito_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales_cedula["RUC Proveedor"] = ""
            sumas_totales_cedula["Proveedor"] = ""
            sumas_totales_cedula["Fecha Emisión"] = "Sumas Totales"
            sumas_totales_cedula["Serie"] = ""
            sumas_totales_cedula["Secuencial"] = ""
            sumas_totales_cedula["Número Autorización"] = ""
            sumas_totales_cedula["Clave de acceso"] = ""
            sumas_totales_cedula["Estado"] = ""
            sumas_totales_cedula_df = pd.DataFrame([sumas_totales_cedula])
            final_cedula_notas_credito_df = pd.concat([final_cedula_notas_credito_df, sumas_totales_cedula_df],
                                                    ignore_index=True)

        return final_notas_credito_df, final_cedula_notas_credito_df


    def procesar_archivos_notas_debito(xml_files):
        dfs_notas_debito = []
        cedula_dfs_notas_debito = []

        for file_path in xml_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()

            root = ET.fromstring(xml_data)
            estado = root.find('.//estado').text
            fecha_autorizacion = root.find('.//fechaAutorizacion').text
            numero_autorizacion = root.find('.//numeroAutorizacion').text
            cdata_node = root.find('.//comprobante').text
            cdata_root = ET.fromstring(cdata_node)

            fecha_emision = cdata_root.find('.//fechaEmision').text
            ruc = cdata_root.find('.//ruc').text
            razon_social = cdata_root.find('.//razonSocial').text
            identificacion_comprador = cdata_root.find('.//identificacionComprador').text

            info_tributaria = cdata_root.find('.//infoTributaria')
            estab = info_tributaria.find('.//estab').text
            ptoEmi = info_tributaria.find('.//ptoEmi').text
            secuencial = info_tributaria.find('.//secuencial').text

            serie = f"{estab}{ptoEmi}"

            subtotal_0 = subtotal_12 = subtotal_5 = subtotal_15 = subtotal_no_objeto_de_impuesto = subtotal_exento_iva = subtotal_iva_diferenciado = 0.0
            iva0 = iva_12 = iva_5 = iva_15 = iva_no_objeto_impuesto = iva_exento = iva_diferenciado = 0.0

            total_sin_impuestos = float(cdata_root.find('.//totalSinImpuestos').text)
            importe_total = float(cdata_root.find('.//valorTotal').text)

            for impuesto in cdata_root.findall('.//impuesto'):
                codigo_porcentaje = int(impuesto.find('codigoPorcentaje').text)
                base_imponible = float(impuesto.find('baseImponible').text)
                valor = float(impuesto.find('valor').text)

                if codigo_porcentaje == 0:
                    subtotal_0 += base_imponible
                    iva0 += valor
                elif codigo_porcentaje == 2:
                    subtotal_12 += base_imponible
                    iva_12 += valor
                elif codigo_porcentaje == 5:
                    subtotal_5 += base_imponible
                    iva_5 += valor
                elif codigo_porcentaje == 4:
                    subtotal_15 += base_imponible
                    iva_15 += valor
                elif codigo_porcentaje == 6:
                    subtotal_no_objeto_de_impuesto += base_imponible
                    iva_no_objeto_impuesto += valor

            data = {
                "RUC Proveedor": [ruc],
                "Proveedor": [razon_social],
                "Fecha Emisión": [fecha_emision],
                "Serie": [serie],
                "Secuencial": [secuencial],
                "Número Autorización": [numero_autorizacion],
                "Clave de acceso": [numero_autorizacion],
                "Subtotal 0": [subtotal_0],
                "Subtotal 12": [subtotal_12],
                "Subtotal 5": [subtotal_5],
                "Subtotal 15": [subtotal_15],
                "Subtotal": [total_sin_impuestos],
                "IVA 12": [iva_12],
                "IVA 5": [iva_5],
                "IVA 15": [iva_15],
                "Total": [importe_total],
                "Estado": [estado]
            }
            df = pd.DataFrame(data)

            if len(identificacion_comprador) > 10:
                dfs_notas_debito.append(df)
            elif len(identificacion_comprador) == 10:
                cedula_dfs_notas_debito.append(df)

        if dfs_notas_debito:
            final_notas_debito_df = pd.concat(dfs_notas_debito, ignore_index=True)
        else:
            final_notas_debito_df = pd.DataFrame()

        if cedula_dfs_notas_debito:
            final_cedula_notas_debito_df = pd.concat(cedula_dfs_notas_debito, ignore_index=True)
        else:
            final_cedula_notas_debito_df = pd.DataFrame()

        if not final_notas_debito_df.empty:
            sumas_totales = final_notas_debito_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales["RUC Proveedor"] = ""
            sumas_totales["Proveedor"] = ""
            sumas_totales["Fecha Emisión"] = "Sumas Totales"
            sumas_totales["Serie"] = ""
            sumas_totales["Secuencial"] = ""
            sumas_totales["Número Autorización"] = ""
            sumas_totales["Clave de acceso"] = ""
            sumas_totales["Estado"] = ""
            sumas_totales_df = pd.DataFrame([sumas_totales])
            final_notas_debito_df = pd.concat([final_notas_debito_df, sumas_totales_df], ignore_index=True)

        if not final_cedula_notas_debito_df.empty:
            sumas_totales_cedula = final_cedula_notas_debito_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales_cedula["RUC Proveedor"] = ""
            sumas_totales_cedula["Proveedor"] = ""
            sumas_totales_cedula["Fecha Emisión"] = "Sumas Totales"
            sumas_totales_cedula["Serie"] = ""
            sumas_totales_cedula["Secuencial"] = ""
            sumas_totales_cedula["Número Autorización"] = ""
            sumas_totales_cedula["Clave de acceso"] = ""
            sumas_totales_cedula["Estado"] = ""
            sumas_totales_cedula_df = pd.DataFrame([sumas_totales_cedula])
            final_cedula_notas_debito_df = pd.concat([final_cedula_notas_debito_df, sumas_totales_cedula_df],
                                                    ignore_index=True)

        return final_notas_debito_df, final_cedula_notas_debito_df

    def guardar_en_excel(filename, sheets_data):
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            for sheet_name, df in sheets_data.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    workbook = writer.book
                    worksheet = writer.sheets[sheet_name]

                    # Aplicar formato de texto explícitamente
                    text_format = workbook.add_format({'num_format': '@'})
                    if '#Doc' in df.columns:
                        col_idx = df.columns.get_loc('#Doc')
                        worksheet.set_column(col_idx + 1, col_idx + 1, None, text_format)
                    if 'Número Autorización' in df.columns:
                        col_idx = df.columns.get_loc('Número Autorización')
                        worksheet.set_column(col_idx + 1, col_idx + 1, None, text_format)

    def seleccionar_y_guardar(sheets_data):
        Tk().withdraw()  # Ocultar la ventana principal de Tkinter
        filename = asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if filename:
            guardar_en_excel(filename, sheets_data)
            return f"Los datos se han guardado en {filename}"
        else:
            return "No se seleccionó ningún archivo. Los datos no se han guardado."

    def main():
        directory_compras = os.path.join(directory,'XML',aniomodal,nombremesmodal,'RECIBIDAS', 'Facturas')
    
        directory_retenciones = os.path.join(directory,'XML',aniomodal,nombremesmodal,'RECIBIDAS', 'Retenciones')
        directory_notas_credito = os.path.join(directory,'XML',aniomodal,nombremesmodal,'RECIBIDAS', 'NotasCredito')
        directory_notas_debito = os.path.join(directory,'XML',aniomodal,nombremesmodal,'RECIBIDAS', 'NotasDebito')
        directory_liquidacion = os.path.join(directory,'XML',aniomodal,nombremesmodal,'RECIBIDAS', 'Liquidaciones')

        xml_files_compras = obtener_archivos_xml(directory_compras)
        xml_files_retenciones = obtener_archivos_xml(directory_retenciones)
        xml_files_notas_credito = obtener_archivos_xml(directory_notas_credito)
        xml_files_notas_debito = obtener_archivos_xml(directory_notas_debito)
        xml_files_liquidacion = obtener_archivos_xml(directory_liquidacion)

        final_compras_df, final_cedula_compras_df = procesar_archivos_compras(xml_files_compras)
        final_retenciones_df = procesar_archivos_retenciones(xml_files_retenciones)
        final_notas_credito_df, final_cedula_notas_credito_df = procesar_archivos_notas_credito(xml_files_notas_credito)
        final_notas_debito_df, final_cedula_notas_debito_df = procesar_archivos_notas_debito(xml_files_notas_debito)
        final_liquidaciones_df, final_cedula_liquidaciones = procesar_archivos_liquidacion(xml_files_liquidacion)

        sheets_data = {
            "Compras Recibidas": final_compras_df,
            "Compras Cédula Recibidas": final_cedula_compras_df,
            "Retenciones Recibidas": final_retenciones_df,
            "Notas de Crédito Recibidas": final_notas_credito_df,
            "Notas de Crédito Cédula Recibidas": final_cedula_notas_credito_df,
            "Notas de Débito Recibidas": final_notas_debito_df,
            "Notas de Débito Cédula Recibidas": final_cedula_notas_debito_df,
            "Liquidacion Recibidas": final_liquidaciones_df,
            "Liquidaciones Cédula Recibidas": final_cedula_liquidaciones
        }

        return seleccionar_y_guardar(sheets_data)

    return main()


# Crear Reporte Emitidos
def ejecutar_script_reporteemitidos(directory, nombremesmodal, aniomodal):  
    def obtener_archivos_xml(directory):
        xml_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.xml'):
                    xml_files.append(os.path.join(root, file))
        return xml_files


    def procesar_archivos_compras(xml_files):
        dfs_compras = []
        cedula_dfs_compras = []

        for file_path in xml_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()

            root = ET.fromstring(xml_data)
            estado = root.find('.//estado').text
            fecha_autorizacion = root.find('.//fechaAutorizacion').text
            numero_autorizacion = root.find('.//numeroAutorizacion').text
            cdata_node = root.find('.//comprobante').text
            cdata_root = ET.fromstring(cdata_node)

            fecha_emision = cdata_root.find('.//fechaEmision').text
            ruc = cdata_root.find('.//ruc').text
            razon_social = cdata_root.find('.//razonSocial').text
            identificacion_comprador = cdata_root.find('.//identificacionComprador').text

            info_tributaria = cdata_root.find('.//infoTributaria')
            estab = info_tributaria.find('.//estab').text
            ptoEmi = info_tributaria.find('.//ptoEmi').text
            secuencial = info_tributaria.find('.//secuencial').text

            serie = f"{estab}{ptoEmi}"

            subtotal_0 = subtotal_12 = subtotal_5 = subtotal_15 = subtotal_no_objeto_de_impuesto = subtotal_exento_iva = subtotal_iva_diferenciado = 0.0
            iva_12 = iva_5 = iva_15 = iva_no_objeto_impuesto = iva_exento = iva_diferenciado = 0.0

            total_sin_impuestos = float(cdata_root.find('.//totalSinImpuestos').text)
            importe_total = float(cdata_root.find('.//importeTotal').text)

            for impuesto in cdata_root.findall('.//totalImpuesto'):
                codigo_porcentaje = int(impuesto.find('codigoPorcentaje').text)
                base_imponible = float(impuesto.find('baseImponible').text)
                valor = float(impuesto.find('valor').text)

                if codigo_porcentaje == 0:
                    subtotal_0 += base_imponible
                elif codigo_porcentaje == 2:
                    subtotal_12 += base_imponible
                    iva_12 += valor
                elif codigo_porcentaje == 5:
                    subtotal_5 += base_imponible
                    iva_5 += valor
                elif codigo_porcentaje == 4:
                    subtotal_15 += base_imponible
                    iva_15 += valor
                elif codigo_porcentaje == 6:
                    subtotal_no_objeto_de_impuesto += base_imponible
                elif codigo_porcentaje == 7:
                    subtotal_exento_iva += base_imponible
                elif codigo_porcentaje == 8:
                    subtotal_iva_diferenciado += base_imponible

            data = {
                "RUC Proveedor": [ruc],
                "Proveedor": [razon_social],
                "Fecha Emisión": [fecha_emision],
                "Serie": [serie],
                "Secuencial": [secuencial],
                "Número Autorización": [numero_autorizacion],
                "Clave de acceso": [numero_autorizacion],
                "Subtotal 0": [subtotal_0],
                "Subtotal 12": [subtotal_12],
                "Subtotal 5": [subtotal_5],
                "Subtotal 15": [subtotal_15],
                "Subtotal": [total_sin_impuestos],
                "IVA 12": [iva_12],
                "IVA 5": [iva_5],
                "IVA 15": [iva_15],
                "Total": [importe_total],
                "Estado": [estado]
            }
            df = pd.DataFrame(data)

            if len(identificacion_comprador) > 10:
                dfs_compras.append(df)
            elif len(identificacion_comprador) == 10:
                cedula_dfs_compras.append(df)

        if dfs_compras:
            final_compras_df = pd.concat(dfs_compras, ignore_index=True)
        else:
            final_compras_df = pd.DataFrame()

        if cedula_dfs_compras:
            final_cedula_compras_df = pd.concat(cedula_dfs_compras, ignore_index=True)
        else:
            final_cedula_compras_df = pd.DataFrame()

        if not final_compras_df.empty:
            sumas_totales_compras = final_compras_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales_compras["RUC Proveedor"] = ""
            sumas_totales_compras["Proveedor"] = ""
            sumas_totales_compras["Fecha Emisión"] = "Sumas Totales"
            sumas_totales_compras["Serie"] = ""
            sumas_totales_compras["Secuencial"] = ""
            sumas_totales_compras["Número Autorización"] = ""
            sumas_totales_compras["Clave de acceso"] = ""
            sumas_totales_compras["Estado"] = ""
            sumas_totales_compras_df = pd.DataFrame([sumas_totales_compras])
            final_compras_df = pd.concat([final_compras_df, sumas_totales_compras_df], ignore_index=True)

        if not final_cedula_compras_df.empty:
            sumas_totales_cedula_compras = final_cedula_compras_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales_cedula_compras["RUC Proveedor"] = ""
            sumas_totales_cedula_compras["Proveedor"] = ""
            sumas_totales_cedula_compras["Fecha Emisión"] = "Sumas Totales"
            sumas_totales_cedula_compras["Serie"] = ""
            sumas_totales_cedula_compras["Secuencial"] = ""
            sumas_totales_cedula_compras["Número Autorización"] = ""
            sumas_totales_cedula_compras["Clave de acceso"] = ""
            sumas_totales_cedula_compras["Estado"] = ""
            sumas_totales_cedula_compras_df = pd.DataFrame([sumas_totales_cedula_compras])
            final_cedula_compras_df = pd.concat([final_cedula_compras_df, sumas_totales_cedula_compras_df],
                                                ignore_index=True)

        return final_compras_df, final_cedula_compras_df


    def procesar_archivos_liquidacion(xml_files):
        dfs_liquidacion = []
        cedula_dfs_liquidacion = []

        for file_path in xml_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()

            root = ET.fromstring(xml_data)
            estado = root.find('.//estado').text
            fecha_autorizacion = root.find('.//fechaAutorizacion').text
            numero_autorizacion = root.find('.//numeroAutorizacion').text
            cdata_node = root.find('.//comprobante').text
            cdata_root = ET.fromstring(cdata_node)

            fecha_emision = cdata_root.find('.//fechaEmision').text
            ruc = cdata_root.find('.//ruc').text

            info_tributaria = cdata_root.find('.//infoTributaria')
            estab = info_tributaria.find('.//estab').text
            ptoEmi = info_tributaria.find('.//ptoEmi').text
            secuencial = info_tributaria.find('.//secuencial').text

            numero_doc = f"{estab}{ptoEmi}{secuencial}"

            identificacion_proveedor = cdata_root.find('.//infoLiquidacionCompra/identificacionProveedor').text
            razonsocial_proveedor = cdata_root.find('.//infoLiquidacionCompra/razonSocialProveedor').text

            subtotal_0 = subtotal_12 = subtotal_5 = subtotal_15 = subtotal_no_objeto_de_impuesto = subtotal_exento_iva = subtotal_iva_diferenciado = 0.0
            iva_12 = iva_5 = iva_15 = iva_no_objeto_impuesto = iva_exento = iva_diferenciado = 0.0

            total_sin_impuestos = float(cdata_root.find('.//totalSinImpuestos').text)
            importe_total = float(cdata_root.find('.//importeTotal').text)

            for impuesto in cdata_root.findall('.//totalImpuesto'):
                codigo_porcentaje = int(impuesto.find('codigoPorcentaje').text)
                base_imponible = float(impuesto.find('baseImponible').text)
                valor = float(impuesto.find('valor').text)

                if codigo_porcentaje == 0:
                    subtotal_0 += base_imponible
                elif codigo_porcentaje == 2:
                    subtotal_12 += base_imponible
                    iva_12 += valor
                elif codigo_porcentaje == 5:
                    subtotal_5 += base_imponible
                    iva_5 += valor
                elif codigo_porcentaje == 4:
                    subtotal_15 += base_imponible
                    iva_15 += valor
                elif codigo_porcentaje == 6:
                    iva_no_objeto_impuesto += base_imponible
                elif codigo_porcentaje == 7:
                    iva_exento += base_imponible
                elif codigo_porcentaje == 8:
                    iva_diferenciado += base_imponible

            data = {
                "Fecha Emisión": [fecha_emision],
                "Fecha Autorización": [fecha_autorizacion],
                "Identificacion Proveedor": [identificacion_proveedor],
                "#Doc": [numero_doc],
                "# Autorizacion": [numero_autorizacion],
                "Proveedor": [razonsocial_proveedor],
                "Identificación Comprador": [ruc],
                "Subtotal 15": [subtotal_15],
                "Subtotal 0": [subtotal_0],
                "Subtotal 12": [subtotal_12],
                "Subtotal 5": [subtotal_5],
                "Subtotal 15": [subtotal_15],
                "Subtotal": [total_sin_impuestos],
                "IVA 12": [iva_12],
                "IVA 5": [iva_5],
                "IVA 15": [iva_15],
                "Total": [importe_total],
                "Estado": [estado]

            }
            df = pd.DataFrame(data)

            if len(ruc) > 10:
                dfs_liquidacion.append(df)
            elif len(ruc) == 10:
                cedula_dfs_liquidacion.append(df)

        if dfs_liquidacion:
            final_liquidacion_df = pd.concat(dfs_liquidacion, ignore_index=True)
        else:
            final_liquidacion_df = pd.DataFrame()

        if cedula_dfs_liquidacion:
            final_cedula_liquidacion_df = pd.concat(cedula_dfs_liquidacion, ignore_index=True)
        else:
            final_cedula_liquidacion_df = pd.DataFrame()

        if not final_liquidacion_df.empty:
            sumas_totales = final_liquidacion_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales["Fecha Emisión"] = "Sumas Totales"
            sumas_totales["Fecha Autorización"] = ""
            sumas_totales["Identificacion Proveedor"] = ""
            sumas_totales["Proveedor"] = ""
            sumas_totales["Identificación Empresa"] = ""
            sumas_totales["Estado"] = ""
            sumas_totales_df = pd.DataFrame([sumas_totales])
            final_liquidacion_df = pd.concat([final_liquidacion_df, sumas_totales_df], ignore_index=True)

        return final_liquidacion_df, final_cedula_liquidacion_df


    def procesar_archivos_retenciones(xml_files):
        dfs = []

        for file_path in xml_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()

            try:
                root = ET.fromstring(xml_data)
                estado = root.find("estado").text
                fecha_autorizacion = root.find("fechaAutorizacion").text
                numero_autorizacion = root.find("numeroAutorizacion").text

                comprobante_cdata = root.find(".//comprobante").text
                comprobante_xml = ET.fromstring(comprobante_cdata)
                version = comprobante_xml.attrib.get("version", "")

                if version == "1.0.0":
                    info_tributaria = comprobante_xml.find("infoTributaria")
                    nombre_comercial = info_tributaria.find("razonSocial").text if info_tributaria.find(
                        "razonSocial") is not None else ""
                    ruc = info_tributaria.find("ruc").text
                    estab = info_tributaria.find("estab").text
                    ptoEmi = info_tributaria.find("ptoEmi").text
                    secuencial = info_tributaria.find("secuencial").text
                    serie = f"{estab}{ptoEmi}"
                    info_comp_retencion = comprobante_xml.find("infoCompRetencion")
                    fecha_emision = info_comp_retencion.find("fechaEmision").text

                    for impuesto in comprobante_xml.findall("impuestos/impuesto"):
                        codigo_retencion = impuesto.find("codigoRetencion").text
                        base_imponible = float(impuesto.find("baseImponible").text)
                        porcentaje_retener = float(impuesto.find("porcentajeRetener").text)
                        valor_retenido = float(impuesto.find("valorRetenido").text)

                        data = {
                            "Fecha Emisión": [fecha_emision],
                            "Fecha Autorización": [fecha_autorizacion],
                            "Serie": [serie],
                            "Secuencial": [secuencial],
                            "# Autorización": [numero_autorizacion],
                            "RUC": [ruc],
                            "Razon Social": [nombre_comercial],
                            "Codigo Retencion": [codigo_retencion],
                            "Base Imponible": [base_imponible],
                            "Porcentaje Retener": [porcentaje_retener],
                            "Valor Retenido": [valor_retenido],
                            "Estado": [estado],
                            "Versión": [version]
                        }

                        df = pd.DataFrame(data)
                        dfs.append(df)
                elif version == "2.0.0":
                    info_tributaria = comprobante_xml.find("infoTributaria")
                    nombre_comercial = info_tributaria.find("nombreComercial").text if info_tributaria.find(
                        "nombreComercial") is not None else ""
                    razon_social = info_tributaria.find("razonSocial").text if info_tributaria.find(
                        "razonSocial") is not None else ""
                    proveedor = nombre_comercial if nombre_comercial else razon_social
                    ruc = info_tributaria.find("ruc").text
                    estab = info_tributaria.find("estab").text
                    ptoEmi = info_tributaria.find("ptoEmi").text
                    secuencial = info_tributaria.find("secuencial").text
                    serie = f"{estab}{ptoEmi}"
                    info_comp_retencion = comprobante_xml.find("infoCompRetencion")
                    fecha_emision = info_comp_retencion.find("fechaEmision").text
                    doc_sustento = comprobante_xml.find(".//docSustento")
                    num_doc_sustento = doc_sustento.find("numDocSustento").text if doc_sustento is not None else ""

                    for retencion in comprobante_xml.findall(".//retencion"):
                        codigo_retencion = retencion.find("codigoRetencion").text
                        base_imponible = float(retencion.find("baseImponible").text)
                        porcentaje_retener = float(retencion.find("porcentajeRetener").text)
                        valor_retenido = float(retencion.find("valorRetenido").text)
                        codigo = retencion.find("codigo").text
                        codigo = int(codigo)

                        if codigo == 1:
                            descripcion = 'Renta'
                        elif codigo == 2:
                            descripcion = 'Iva'
                        elif codigo == 3:
                            descripcion = 'ICE'
                        elif codigo == 6:
                            descripcion = 'Rendimientos Financieros'
                        elif codigo == 7:
                            descripcion = 'ISD'
                        elif codigo == 8:
                            descripcion = 'Operaciones de Exportación'
                        elif codigo == 9:
                            descripcion = 'Operaciones de Importación'
                        elif codigo == 10:
                            descripcion = 'Servicios Profesionales'

                        data = {
                            "Fecha Emisión": [fecha_emision],
                            "Fecha Autorización": [fecha_autorizacion],
                            "Serie": [serie],
                            "Secuencial": [secuencial],
                            "# Autorización": [numero_autorizacion],
                            "RUC": [ruc],
                            "Razon Social": [proveedor],
                            "Codigo Retencion": [codigo_retencion],
                            "Base Imponible": [base_imponible],
                            "Porcentaje Retener": [porcentaje_retener],
                            "Valor Retenido": [valor_retenido],
                            "Estado": [estado],
                            "Versión": [version],
                            "Tipo de Retención": [descripcion]
                        }

                        df = pd.DataFrame(data)
                        dfs.append(df)
                else:
                    print(f"Versión del comprobante no compatible: {version}. Saltando archivo.")
                    continue

            except Exception as e:
                print(f"Error al procesar el archivo {file_path}: {e}")

        if dfs:
            final_df = pd.concat(dfs, ignore_index=True)
            subtotals = final_df.groupby("Codigo Retencion").agg({
                'Base Imponible': 'sum',
                'Valor Retenido': 'sum'
            }).reset_index()

            output_data = []

            for codigo_retencion, group in final_df.groupby("Codigo Retencion"):
                output_data.append(group)
                subtotal = subtotals[subtotals["Codigo Retencion"] == codigo_retencion]
                subtotal_row = {
                    "Fecha Emisión": "Subtotal",
                    "Fecha Autorización": "",
                    "Serie": "",
                    "Secuencial": "",
                    "# Autorización": "",
                    "RUC": "",
                    "Razon Social": "",
                    "Codigo Retencion": codigo_retencion,
                    "Base Imponible": subtotal["Base Imponible"].values[0],
                    "Porcentaje Retener": "",
                    "Valor Retenido": subtotal["Valor Retenido"].values[0],
                    "Estado": "",
                    "Versión": ""
                }
                output_data.append(pd.DataFrame([subtotal_row]))

            output_df = pd.concat(output_data, ignore_index=True)
        else:
            output_df = pd.DataFrame()

        return output_df


    def procesar_archivos_notas_credito(xml_files):
        dfs_notas_credito = []
        cedula_dfs_notas_credito = []

        for file_path in xml_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()

            root = ET.fromstring(xml_data)
            estado = root.find('.//estado').text
            fecha_autorizacion = root.find('.//fechaAutorizacion').text
            numero_autorizacion = root.find('.//numeroAutorizacion').text
            cdata_node = root.find('.//comprobante').text
            cdata_root = ET.fromstring(cdata_node)

            fecha_emision = cdata_root.find('.//fechaEmision').text
            ruc = cdata_root.find('.//ruc').text
            razon_social = cdata_root.find('.//razonSocial').text
            identificacion_comprador = cdata_root.find('.//identificacionComprador').text

            info_tributaria = cdata_root.find('.//infoTributaria')
            estab = info_tributaria.find('.//estab').text
            ptoEmi = info_tributaria.find('.//ptoEmi').text
            secuencial = info_tributaria.find('.//secuencial').text

            serie = f"{estab}{ptoEmi}"

            subtotal_0 = subtotal_12 = subtotal_5 = subtotal_15 = subtotal_no_objeto_de_impuesto = subtotal_exento_iva = subtotal_iva_diferenciado = 0.0
            iva_12 = iva_5 = iva_15 = iva_no_objeto_impuesto = iva_exento = iva_diferenciado = 0.0

            total_sin_impuestos = float(cdata_root.find('.//totalSinImpuestos').text)
            importe_total = float(cdata_root.find('.//valorModificacion').text)

            for impuesto in cdata_root.findall('.//totalImpuesto'):
                codigo_porcentaje = int(impuesto.find('codigoPorcentaje').text)
                base_imponible = float(impuesto.find('baseImponible').text)
                valor = float(impuesto.find('valor').text)

                if codigo_porcentaje == 0:
                    subtotal_0 += base_imponible
                elif codigo_porcentaje == 2:
                    subtotal_12 += base_imponible
                    iva_12 += valor
                elif codigo_porcentaje == 5:
                    subtotal_5 += base_imponible
                    iva_5 += valor
                elif codigo_porcentaje == 4:
                    subtotal_15 += base_imponible
                    iva_15 += valor

            data = {
                "RUC Proveedor": [ruc],
                "Proveedor": [razon_social],
                "Fecha Emisión": [fecha_emision],
                "Serie": [serie],
                "Secuencial": [secuencial],
                "Número Autorización": [numero_autorizacion],
                "Clave de acceso": [numero_autorizacion],
                "Subtotal 0": [subtotal_0],
                "Subtotal 12": [subtotal_12],
                "Subtotal 5": [subtotal_5],
                "Subtotal 15": [subtotal_15],
                "Subtotal": [total_sin_impuestos],
                "IVA 12": [iva_12],
                "IVA 5": [iva_5],
                "IVA 15": [iva_15],
                "Total": [importe_total],
                "Estado": [estado]
            }
            df = pd.DataFrame(data)

            if len(identificacion_comprador) > 10:
                dfs_notas_credito.append(df)
            elif len(identificacion_comprador) == 10:
                cedula_dfs_notas_credito.append(df)

        if dfs_notas_credito:
            final_notas_credito_df = pd.concat(dfs_notas_credito, ignore_index=True)
        else:
            final_notas_credito_df = pd.DataFrame()

        if cedula_dfs_notas_credito:
            final_cedula_notas_credito_df = pd.concat(cedula_dfs_notas_credito, ignore_index=True)
        else:
            final_cedula_notas_credito_df = pd.DataFrame()

        if not final_notas_credito_df.empty:
            sumas_totales = final_notas_credito_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales["RUC Proveedor"] = ""
            sumas_totales["Proveedor"] = ""
            sumas_totales["Fecha Emisión"] = "Sumas Totales"
            sumas_totales["Serie"] = ""
            sumas_totales["Secuencial"] = ""
            sumas_totales["Número Autorización"] = ""
            sumas_totales["Clave de acceso"] = ""
            sumas_totales["Estado"] = ""
            sumas_totales_df = pd.DataFrame([sumas_totales])
            final_notas_credito_df = pd.concat([final_notas_credito_df, sumas_totales_df], ignore_index=True)

        if not final_cedula_notas_credito_df.empty:
            sumas_totales_cedula = final_cedula_notas_credito_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales_cedula["RUC Proveedor"] = ""
            sumas_totales_cedula["Proveedor"] = ""
            sumas_totales_cedula["Fecha Emisión"] = "Sumas Totales"
            sumas_totales_cedula["Serie"] = ""
            sumas_totales_cedula["Secuencial"] = ""
            sumas_totales_cedula["Número Autorización"] = ""
            sumas_totales_cedula["Clave de acceso"] = ""
            sumas_totales_cedula["Estado"] = ""
            sumas_totales_cedula_df = pd.DataFrame([sumas_totales_cedula])
            final_cedula_notas_credito_df = pd.concat([final_cedula_notas_credito_df, sumas_totales_cedula_df],
                                                    ignore_index=True)

        return final_notas_credito_df, final_cedula_notas_credito_df


    def procesar_archivos_notas_debito(xml_files):
        dfs_notas_debito = []
        cedula_dfs_notas_debito = []

        for file_path in xml_files:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()

            root = ET.fromstring(xml_data)
            estado = root.find('.//estado').text
            fecha_autorizacion = root.find('.//fechaAutorizacion').text
            numero_autorizacion = root.find('.//numeroAutorizacion').text
            cdata_node = root.find('.//comprobante').text
            cdata_root = ET.fromstring(cdata_node)

            fecha_emision = cdata_root.find('.//fechaEmision').text
            ruc = cdata_root.find('.//ruc').text
            razon_social = cdata_root.find('.//razonSocial').text
            identificacion_comprador = cdata_root.find('.//identificacionComprador').text

            info_tributaria = cdata_root.find('.//infoTributaria')
            estab = info_tributaria.find('.//estab').text
            ptoEmi = info_tributaria.find('.//ptoEmi').text
            secuencial = info_tributaria.find('.//secuencial').text

            serie = f"{estab}{ptoEmi}"

            subtotal_0 = subtotal_12 = subtotal_5 = subtotal_15 = subtotal_no_objeto_de_impuesto = subtotal_exento_iva = subtotal_iva_diferenciado = 0.0
            iva0 = iva_12 = iva_5 = iva_15 = iva_no_objeto_impuesto = iva_exento = iva_diferenciado = 0.0

            total_sin_impuestos = float(cdata_root.find('.//totalSinImpuestos').text)
            importe_total = float(cdata_root.find('.//valorTotal').text)

            for impuesto in cdata_root.findall('.//impuesto'):
                codigo_porcentaje = int(impuesto.find('codigoPorcentaje').text)
                base_imponible = float(impuesto.find('baseImponible').text)
                valor = float(impuesto.find('valor').text)

                if codigo_porcentaje == 0:
                    subtotal_0 += base_imponible
                    iva0 += valor
                elif codigo_porcentaje == 2:
                    subtotal_12 += base_imponible
                    iva_12 += valor
                elif codigo_porcentaje == 5:
                    subtotal_5 += base_imponible
                    iva_5 += valor
                elif codigo_porcentaje == 4:
                    subtotal_15 += base_imponible
                    iva_15 += valor
                elif codigo_porcentaje == 6:
                    subtotal_no_objeto_de_impuesto += base_imponible
                    iva_no_objeto_impuesto += valor

            data = {
                "RUC Proveedor": [ruc],
                "Proveedor": [razon_social],
                "Fecha Emisión": [fecha_emision],
                "Serie": [serie],
                "Secuencial": [secuencial],
                "Número Autorización": [numero_autorizacion],
                "Clave de acceso": [numero_autorizacion],
                "Subtotal 0": [subtotal_0],
                "Subtotal 12": [subtotal_12],
                "Subtotal 5": [subtotal_5],
                "Subtotal 15": [subtotal_15],
                "Subtotal": [total_sin_impuestos],
                "IVA 12": [iva_12],
                "IVA 5": [iva_5],
                "IVA 15": [iva_15],
                "Total": [importe_total],
                "Estado": [estado]
            }
            df = pd.DataFrame(data)

            if len(identificacion_comprador) > 10:
                dfs_notas_debito.append(df)
            elif len(identificacion_comprador) == 10:
                cedula_dfs_notas_debito.append(df)

        if dfs_notas_debito:
            final_notas_debito_df = pd.concat(dfs_notas_debito, ignore_index=True)
        else:
            final_notas_debito_df = pd.DataFrame()

        if cedula_dfs_notas_debito:
            final_cedula_notas_debito_df = pd.concat(cedula_dfs_notas_debito, ignore_index=True)
        else:
            final_cedula_notas_debito_df = pd.DataFrame()

        if not final_notas_debito_df.empty:
            sumas_totales = final_notas_debito_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales["RUC Proveedor"] = ""
            sumas_totales["Proveedor"] = ""
            sumas_totales["Fecha Emisión"] = "Sumas Totales"
            sumas_totales["Serie"] = ""
            sumas_totales["Secuencial"] = ""
            sumas_totales["Número Autorización"] = ""
            sumas_totales["Clave de acceso"] = ""
            sumas_totales["Estado"] = ""
            sumas_totales_df = pd.DataFrame([sumas_totales])
            final_notas_debito_df = pd.concat([final_notas_debito_df, sumas_totales_df], ignore_index=True)

        if not final_cedula_notas_debito_df.empty:
            sumas_totales_cedula = final_cedula_notas_debito_df[
                ["Subtotal 0", "Subtotal 12", "Subtotal 5", "Subtotal 15", "Subtotal", "IVA 12", "IVA 5", "IVA 15",
                "Total"]].sum()
            sumas_totales_cedula["RUC Proveedor"] = ""
            sumas_totales_cedula["Proveedor"] = ""
            sumas_totales_cedula["Fecha Emisión"] = "Sumas Totales"
            sumas_totales_cedula["Serie"] = ""
            sumas_totales_cedula["Secuencial"] = ""
            sumas_totales_cedula["Número Autorización"] = ""
            sumas_totales_cedula["Clave de acceso"] = ""
            sumas_totales_cedula["Estado"] = ""
            sumas_totales_cedula_df = pd.DataFrame([sumas_totales_cedula])
            final_cedula_notas_debito_df = pd.concat([final_cedula_notas_debito_df, sumas_totales_cedula_df],
                                                    ignore_index=True)

        return final_notas_debito_df, final_cedula_notas_debito_df

    def guardar_en_excel(filename, sheets_data):
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            for sheet_name, df in sheets_data.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    workbook = writer.book
                    worksheet = writer.sheets[sheet_name]

                    # Aplicar formato de texto explícitamente
                    text_format = workbook.add_format({'num_format': '@'})
                    if '#Doc' in df.columns:
                        col_idx = df.columns.get_loc('#Doc')
                        worksheet.set_column(col_idx + 1, col_idx + 1, None, text_format)
                    if 'Número Autorización' in df.columns:
                        col_idx = df.columns.get_loc('Número Autorización')
                        worksheet.set_column(col_idx + 1, col_idx + 1, None, text_format)

    def seleccionar_y_guardar(sheets_data):
        Tk().withdraw()  # Ocultar la ventana principal de Tkinter
        filename = asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if filename:
            guardar_en_excel(filename, sheets_data)
            return f"Los datos se han guardado en {filename}"
        else:
            return "No se seleccionó ningún archivo. Los datos no se han guardado."

    def main():
        directory_compras = os.path.join(directory,'XML',aniomodal,nombremesmodal,'EMITIDAS', 'FacturasE')
    
        directory_retenciones = os.path.join(directory,'XML',aniomodal,nombremesmodal,'EMITIDAS', 'RetencionesE')
        directory_notas_credito = os.path.join(directory,'XML',aniomodal,nombremesmodal,'EMITIDAS', 'NotasCreditoE')
        directory_notas_debito = os.path.join(directory,'XML',aniomodal,nombremesmodal,'EMITIDAS', 'NotasDebitoE')
        directory_liquidacion = os.path.join(directory,'XML',aniomodal,nombremesmodal,'EMITIDAS', 'LiquidacionesE')

        xml_files_compras = obtener_archivos_xml(directory_compras)
        xml_files_retenciones = obtener_archivos_xml(directory_retenciones)
        xml_files_notas_credito = obtener_archivos_xml(directory_notas_credito)
        xml_files_notas_debito = obtener_archivos_xml(directory_notas_debito)
        xml_files_liquidacion = obtener_archivos_xml(directory_liquidacion)

        final_compras_df, final_cedula_compras_df = procesar_archivos_compras(xml_files_compras)
        final_retenciones_df = procesar_archivos_retenciones(xml_files_retenciones)
        final_notas_credito_df, final_cedula_notas_credito_df = procesar_archivos_notas_credito(xml_files_notas_credito)
        final_notas_debito_df, final_cedula_notas_debito_df = procesar_archivos_notas_debito(xml_files_notas_debito)
        final_liquidaciones_df, final_cedula_liquidaciones = procesar_archivos_liquidacion(xml_files_liquidacion)

        sheets_data = {
            "Facturas Emitidas": final_compras_df,
            "Compras Cédula Emitidas": final_cedula_compras_df,
            "Retenciones Emitidas": final_retenciones_df,
            "Notas de Crédito Emitidas": final_notas_credito_df,
            "Notas de Crédito Cédula Emitidas": final_cedula_notas_credito_df,
            "Notas de Débito Emitidas": final_notas_debito_df,
            "Notas de Débito Cédula Emitidas": final_cedula_notas_debito_df,
            "Liquidacion Emitidas": final_liquidaciones_df,
            "Liquidaciones Cédula Emitidas": final_cedula_liquidaciones
        }

        return seleccionar_y_guardar(sheets_data)

    return main()

# Crear ATS
def ejecutar_script_crearats(directory, nombremesmodal, aniomodal):
    def leer_anulados(file_path, mes_ats, anio_ats):
        anulados = []
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                lines = file.readlines()
                for line in lines[1:]:  # Omitir la primera línea (cabecera)
                    fields = line.strip().split('\t')
                    if len(fields) == 6:
                        autorizacion = fields[1]
                        mes_autorizacion = autorizacion[2:4]
                        anio_autorizacion = autorizacion[4:8]
                        if mes_autorizacion == mes_ats and anio_autorizacion == anio_ats:
                            anulados.append({
                                'tipoComprobante': fields[0],
                                'autorizacion': fields[1],
                                'establecimiento': fields[2],
                                'puntoEmision': fields[3],
                                'secuencialInicio': fields[4],
                                'secuencialFin': fields[5]  # Puedes ajustar esto según tus necesidades
                            })
        return anulados

    def parsear_xml_desde_archivo(ruta_archivo):
        with open(ruta_archivo, 'r', encoding='UTF-8') as archivo:
            data = archivo.read()
            root = ET.fromstring(data)
            
            numero_autorizacion = root.find('.//numeroAutorizacion').text if root.find('.//numeroAutorizacion') is not None else 'N/A'
            
            cdata = root.find('.//comprobante').text
            if cdata:
                root_cdata = ET.fromstring(cdata)
                return root_cdata, numero_autorizacion
            else:
                return None, None

    def encontrar_retencion_correspondiente(ruta_carpeta_retenciones, numDocSustento, ruc_proveedor):
        for archivo in os.listdir(ruta_carpeta_retenciones):
            if archivo.endswith('.xml'):
                ruta_archivo = os.path.join(ruta_carpeta_retenciones, archivo)
                retencion_root, numero_autorizacion_retencion = parsear_xml_desde_archivo(ruta_archivo)
                if retencion_root is not None:
                    num_doc_sustento_retencion = retencion_root.find('.//numDocSustento').text if retencion_root.find('.//numDocSustento') is not None else ''
                    identificacion_sujeto_retenido = retencion_root.find('.//identificacionSujetoRetenido').text if retencion_root.find('.//identificacionSujetoRetenido') is not None else ''
                    if num_doc_sustento_retencion == numDocSustento and identificacion_sujeto_retenido == ruc_proveedor:
                        return retencion_root, numero_autorizacion_retencion
        return None, None

    def agrupar_ventas(factura_roots):
        ventas_agrupadas = defaultdict(lambda: {
            'tpIdCliente': None,
            'idCliente': None,
            'parteRelVtas': 'NO',
            'tipoComprobante': '18',
            'tipoEmision': 'E',
            'numeroComprobantes': 0,
            'baseNoGraIva': 0.00,
            'baseImponible': 0.00, # items0
            'baseImpGrav': 0.00, # items 15%
            'montoIva': 0.00,
            'montoIce': 0.00,
            'valorRetIva': 0.00,
            'valorRetRenta': 0.00,
            'formasDePago': set(),
            'totalesFormaPago': defaultdict(float),
            'denoCli': None  # Añadido para almacenar razonSocialComprador cuando tpIdCliente es 6
        })

        for factura_root, numero_autorizacion_factura in factura_roots:
            info_tributaria = factura_root.find('.//infoTributaria')
            info_factura = factura_root.find('.//infoFactura')
            
            id_cliente = info_factura.find('.//identificacionComprador').text if info_factura.find('.//identificacionComprador') is not None else 'N/A'
            tipo_id_cliente = info_factura.find('.//tipoIdentificacionComprador').text if info_factura.find('.//tipoIdentificacionComprador') is not None else 'N/A'
            
            razon_social_comprador = info_factura.find('.//razonSocialComprador').text if info_factura.find('.//razonSocialComprador') is not None else None
            
            totalImpuesto = info_factura.find('.//totalConImpuestos/totalImpuesto')
            baseImpGrav = float(totalImpuesto.find('baseImponible').text) if totalImpuesto.find('baseImponible') is not None else 0.00
            montoIva = float(totalImpuesto.find('valor').text) if totalImpuesto.find('valor') is not None else 0.00
            forma_pago = info_factura.find('.//formaPago').text if info_factura.find('.//formaPago') is not None else 'N/A'
            total = float(info_factura.find('.//importeTotal').text) if info_factura.find('.//importeTotal') is not None else 0.00

            if id_cliente in ventas_agrupadas:
                ventas_agrupadas[id_cliente]['numeroComprobantes'] += 1
                ventas_agrupadas[id_cliente]['baseImpGrav'] += baseImpGrav
                ventas_agrupadas[id_cliente]['montoIva'] += montoIva
            else:
                ventas_agrupadas[id_cliente]['tpIdCliente'] = tipo_id_cliente
                ventas_agrupadas[id_cliente]['idCliente'] = id_cliente
                ventas_agrupadas[id_cliente]['numeroComprobantes'] = 1
                ventas_agrupadas[id_cliente]['baseImpGrav'] = baseImpGrav
                ventas_agrupadas[id_cliente]['montoIva'] = montoIva
                if tipo_id_cliente == '06':
                    ventas_agrupadas[id_cliente]['denoCli'] = razon_social_comprador

            ventas_agrupadas[id_cliente]['formasDePago'].add(forma_pago)
            ventas_agrupadas[id_cliente]['totalesFormaPago'][forma_pago] += total

        return ventas_agrupadas

    def extraer_encabezado(ruta_carpeta_retenciones):
        for archivo in os.listdir(ruta_carpeta_retenciones):
            if archivo.endswith('.xml'):
                ruta_archivo = os.path.join(ruta_carpeta_retenciones, archivo)
                root, _ = parsear_xml_desde_archivo(ruta_archivo)
                if root is not None:
                    razon_social = root.find('.//razonSocial')
                    ruc = root.find('.//ruc')
                    if razon_social is not None and ruc is not None:
                        return razon_social.text, ruc.text
        return 'RAZON_SOCIAL', 'RUC_RETENCION'  # Valores por defecto si no se encuentran

    def crear_ats(factura_emitidas_roots, factura_recibidas_roots, ruta_carpeta_retenciones, ruta_salida,ruta_anulados):
        ats_root = ET.Element('iva')
        
        numero_autorizacion_factura = factura_emitidas_roots[0][1]
        anio = numero_autorizacion_factura[4:8]
        mes = numero_autorizacion_factura[2:4]
        
        razon_social, ruc_retencion = extraer_encabezado(ruta_carpeta_retenciones)

        ET.SubElement(ats_root, 'TipoIDInformante').text = 'R'
        ET.SubElement(ats_root, 'IdInformante').text = ruc_retencion
        ET.SubElement(ats_root, 'razonSocial').text = razon_social
        ET.SubElement(ats_root, 'Anio').text = anio
        ET.SubElement(ats_root, 'Mes').text = mes
        ET.SubElement(ats_root, 'numEstabRuc').text = '001'
        ET.SubElement(ats_root, 'totalVentas').text = '0.00'
        ET.SubElement(ats_root, 'codigoOperativo').text = 'IVA'
        
        compras = ET.SubElement(ats_root, 'compras')
        ventas = ET.SubElement(ats_root, 'ventas')
        
        ventasEstablecimiento = ET.SubElement(ats_root, 'ventasEstablecimiento')
        detalle_ventas_establecimiento = ET.SubElement(ventasEstablecimiento, 'ventaEst')

        anulados = ET.SubElement(ats_root, 'anulados')
        

        # Añadir detalles de compras
        for root, numero_autorizacion_factura in factura_recibidas_roots:
            detalle_compras = ET.SubElement(compras, 'detalleCompras')

            tipo_comprobante = numero_autorizacion_factura[8:10] if len(numero_autorizacion_factura) > 9 else 'N/A'

            info_tributaria = root.find('.//infoTributaria')
            ruc = info_tributaria.find('ruc').text if info_tributaria.find('ruc') is not None else 'N/A'
            estab = info_tributaria.find('estab').text if info_tributaria.find('estab') is not None else 'N/A'
            ptoEmi = info_tributaria.find('ptoEmi').text if info_tributaria.find('ptoEmi') is not None else 'N/A'
            secuencial = info_tributaria.find('secuencial').text if info_tributaria.find('secuencial') is not None else 'N/A'

            info_factura = root.find('.//infoFactura')
            fechaEmision = info_factura.find('fechaEmision').text if info_factura.find('fechaEmision') is not None else 'N/A'
            
            baseImponible_0 = 0.00
            baseImpGrav_4 = 0.00
            montoIva = 0.00
            
            for totalImpuesto in root.findall('.//totalConImpuestos/totalImpuesto'):
                baseImponible = float(totalImpuesto.find('baseImponible').text) if totalImpuesto.find('baseImponible') is not None else 0.00
                valor = float(totalImpuesto.find('valor').text) if totalImpuesto.find('valor').text is not None else 0.00
                codigo_porcentaje = totalImpuesto.find('codigoPorcentaje').text if totalImpuesto.find('codigoPorcentaje') is not None else 'N/A'

                if codigo_porcentaje == '4':
                    baseImpGrav_4 += baseImponible
                    montoIva += valor
                elif codigo_porcentaje == '0':
                    baseImponible_0 += baseImponible

            ET.SubElement(detalle_compras, 'codSustento').text = '01'
            ET.SubElement(detalle_compras, 'tpIdProv').text = '01'
            ET.SubElement(detalle_compras, 'idProv').text = ruc 
            ET.SubElement(detalle_compras, 'tipoComprobante').text = tipo_comprobante
            ET.SubElement(detalle_compras, 'parteRel').text = 'NO'
            ET.SubElement(detalle_compras, 'fechaRegistro').text = fechaEmision
            ET.SubElement(detalle_compras, 'establecimiento').text = estab
            ET.SubElement(detalle_compras, 'puntoEmision').text = ptoEmi
            ET.SubElement(detalle_compras, 'secuencial').text = secuencial
            ET.SubElement(detalle_compras, 'fechaEmision').text = fechaEmision
            ET.SubElement(detalle_compras, 'autorizacion').text = numero_autorizacion_factura

            ET.SubElement(detalle_compras, 'baseNoGraIva').text = '0.00'
            ET.SubElement(detalle_compras, 'baseImponible').text = f'{baseImponible_0:.2f}'
            ET.SubElement(detalle_compras, 'baseImpGrav').text = f'{baseImpGrav_4:.2f}'
            ET.SubElement(detalle_compras, 'baseImpExe').text = '0.00'
            ET.SubElement(detalle_compras, 'montoIce').text = '0.00'
            ET.SubElement(detalle_compras, 'montoIva').text = f'{montoIva:.2f}'
            ET.SubElement(detalle_compras, 'valRetBien10').text = '0.00'
            ET.SubElement(detalle_compras, 'valRetServ20').text = '0.00'
            ET.SubElement(detalle_compras, 'valorRetBienes').text = '0.00'
            ET.SubElement(detalle_compras, 'valRetServ50').text = '0.00'
            ET.SubElement(detalle_compras, 'valorRetServicios').text = '0.00'
            ET.SubElement(detalle_compras, 'valRetServ100').text = '0.00'
            ET.SubElement(detalle_compras, 'totbasesImpReemb').text = '0.00'

            pago_exterior = ET.SubElement(detalle_compras, 'pagoExterior')
            ET.SubElement(pago_exterior, 'pagoLocExt').text = '01'
            ET.SubElement(pago_exterior, 'paisEfecPago').text = 'NA'
            ET.SubElement(pago_exterior, 'aplicConvDobTrib').text = 'NA'
            ET.SubElement(pago_exterior, 'pagExtSujRetNorLeg').text = 'NA'

            # Añadir el nodo formasDePago si baseImpGrav es mayor a 500
            if baseImpGrav_4 >= 500 or baseImponible_0 >= 500:
                formas_de_pago = ET.SubElement(detalle_compras, 'formasDePago')
                for pago in info_factura.findall('.//pagos/pago'):
                    forma_pago = pago.find('formaPago')
                    if forma_pago is not None:
                        ET.SubElement(formas_de_pago, 'formaPago').text = forma_pago.text

            air = ET.SubElement(detalle_compras, 'air')

            retencion_root, numero_autorizacion_retencion = encontrar_retencion_correspondiente(ruta_carpeta_retenciones, estab + ptoEmi + secuencial, ruc)

            if retencion_root is not None:
                for retencion in retencion_root.findall('.//retencion'):
                    codigo = retencion.find('codigo')
                    codigoRetencion = retencion.find('codigoRetencion')
                    valor_retenido = retencion.find('valorRetenido')
                    baseImponible_air = retencion.find('baseImponible')
                    porcentajeRetener = retencion.find('porcentajeRetener')
                    
                    if codigo is not None and codigo.text == '1':
                        detalle_air = ET.SubElement(air, 'detalleAir')
                        ET.SubElement(detalle_air, 'codRetAir').text = codigoRetencion.text if codigoRetencion is not None else 'N/A'
                        ET.SubElement(detalle_air, 'baseImpAir').text = baseImponible_air.text if baseImponible_air is not None else 'N/A'
                        ET.SubElement(detalle_air, 'porcentajeAir').text = porcentajeRetener.text if porcentajeRetener is not None else 'N/A'
                        ET.SubElement(detalle_air, 'valRetAir').text = valor_retenido.text if valor_retenido is not None else 'N/A'
                    elif codigo is not None and codigo.text == '2':
                        if codigoRetencion is not None and codigoRetencion.text == '1':
                            detalle_compras.find('valorRetBienes').text = valor_retenido.text if valor_retenido is not None else '0.00'
                        elif codigoRetencion is not None and codigoRetencion.text == '2':
                            detalle_compras.find('valorRetServicios').text = valor_retenido.text if valor_retenido is not None else '0.00'
                        elif codigoRetencion is not None and codigoRetencion.text == '3':
                            detalle_compras.find('valRetServ100').text = valor_retenido.text if valor_retenido is not None else '0.00'
                            

                estab_retencion = retencion_root.find('.//infoTributaria/estab').text if retencion_root.find('.//infoTributaria/estab') is not None else 'N/A'
                ptoEmi_retencion = retencion_root.find('.//infoTributaria/ptoEmi').text if retencion_root.find('.//infoTributaria/ptoEmi') is not None else 'N/A'
                secuencial_ret = retencion_root.find('.//infoTributaria/secuencial').text if retencion_root.find('.//infoTributaria/secuencial') is not None else 'N/A'
                secuencial_ret_limpio = secuencial_ret.lstrip('0')

                info_compretencion_retencion = retencion_root.find('.//infoCompRetencion')
                fechaemisionret = info_compretencion_retencion.find('fechaEmision').text if info_compretencion_retencion.find('fechaEmision') is not None else 'N/A'

                ET.SubElement(detalle_compras, 'estabRetencion1').text = estab_retencion
                ET.SubElement(detalle_compras, 'ptoEmiRetencion1').text = ptoEmi_retencion
                ET.SubElement(detalle_compras, 'secRetencion1').text = secuencial_ret_limpio
                ET.SubElement(detalle_compras, 'autRetencion1').text = numero_autorizacion_retencion
                ET.SubElement(detalle_compras, 'fechaEmiRet1').text = fechaemisionret

        # Añadir detalles de ventas
        ventas_agrupadas = agrupar_ventas(factura_emitidas_roots)
        for id_cliente, datos in ventas_agrupadas.items():
            detalle_ventas = ET.SubElement(ventas, 'detalleVentas')
            ET.SubElement(detalle_ventas, 'tpIdCliente').text = datos['tpIdCliente']
            ET.SubElement(detalle_ventas, 'idCliente').text = datos['idCliente']
        # Condicional para parteRelVtas si es = 7 no se muestra
            if datos['tpIdCliente'] != '07':
                ET.SubElement(detalle_ventas, 'parteRelVtas').text = datos['parteRelVtas']
            # Añadir denoCli si tpIdCliente es 06
            if datos['tpIdCliente'] == '06' and datos['denoCli']:
                ET.SubElement(detalle_ventas, 'tipoCliente').text = '01'
                ET.SubElement(detalle_ventas, 'denoCli').text = datos['denoCli']

            ET.SubElement(detalle_ventas, 'tipoComprobante').text = datos['tipoComprobante']
            ET.SubElement(detalle_ventas, 'tipoEmision').text = datos['tipoEmision']
            ET.SubElement(detalle_ventas, 'numeroComprobantes').text = str(datos['numeroComprobantes'])
            ET.SubElement(detalle_ventas, 'baseNoGraIva').text = f'{datos["baseNoGraIva"]:.2f}'
            ET.SubElement(detalle_ventas, 'baseImponible').text = f'{datos["baseImponible"]:.2f}'
            ET.SubElement(detalle_ventas, 'baseImpGrav').text = f'{datos["baseImpGrav"]:.2f}'
            ET.SubElement(detalle_ventas, 'montoIva').text = f'{datos["montoIva"]:.2f}'
            ET.SubElement(detalle_ventas, 'montoIce').text = f'{datos["montoIce"]:.2f}'
            ET.SubElement(detalle_ventas, 'valorRetIva').text = f'{datos["valorRetIva"]:.2f}'
            ET.SubElement(detalle_ventas, 'valorRetRenta').text = f'{datos["valorRetRenta"]:.2f}'

            

            # Añadir el nodo formasDePago si baseImpGrav es mayor o igual a 500
            if datos['baseImpGrav'] >= 0:
                formas_de_pago = ET.SubElement(detalle_ventas, 'formasDePago')
                for forma_pago in datos['formasDePago']:
                    ET.SubElement(formas_de_pago, 'formaPago').text = forma_pago

        ET.SubElement(detalle_ventas_establecimiento, 'codEstab').text = '001'
        ET.SubElement(detalle_ventas_establecimiento, 'ventasEstab').text = '0.00'

        # Leer el archivo de anulados y añadir al XML
        ruta_anulados = os.path.join(r'C:\ia\SRIBOT\XML\ANULADOS', 'comprobantes_anulados.txt')
        anulados_data = leer_anulados(ruta_anulados, mes, anio)

        
        for anulado in anulados_data:
            detalle_anulados = ET.SubElement(anulados, 'detalleAnulados')
            ET.SubElement(detalle_anulados, 'tipoComprobante').text = anulado['tipoComprobante']
            ET.SubElement(detalle_anulados, 'establecimiento').text = anulado['establecimiento']
            ET.SubElement(detalle_anulados, 'puntoEmision').text = anulado['puntoEmision']
            ET.SubElement(detalle_anulados, 'secuencialInicio').text = anulado['secuencialInicio'].lstrip('0')
            ET.SubElement(detalle_anulados, 'secuencialFin').text = anulado['secuencialFin'].lstrip('0')
            ET.SubElement(detalle_anulados, 'autorizacion').text = anulado['autorizacion']

        
        tree = ET.ElementTree(ats_root)
        nombre_archivo = f'ATS{mes}{anio}.xml'
        ruta_archivo_ats = os.path.join(directory, 'XML', aniomodal, nombremesmodal, nombre_archivo)
        # Crear directorios si no existen
        os.makedirs(os.path.dirname(ruta_archivo_ats), exist_ok=True)
        with open(ruta_archivo_ats, 'wb') as xml_file:
            xml_file.write(b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            xml_file.write(b'<!--  Generado por Ishida Asociados   -->\n')
            xml_file.write(b'<!--  Dir: Presidente Rocafuerte y Octavio Diaz -->\n')
            xml_file.write(b'<!--  Telf: 098499003, 072870346, 072871094      -->\n')
            xml_file.write(b'<!--  email: ishidacue@hotmail.com, aquizhpe@ibzssoft.com    -->\n')
            xml_file.write(b'<!--  www.ishidaapp.com   -->\n')
            xml_file.write(b'<!--  Cuenca - Ecuador                -->\n')
            xml_file.write(b'<!--  SISTEMAS DE GESTION EMPRESARIAL -->\n')
            tree.write(xml_file, encoding='utf-8', xml_declaration=False)

    # Ruta de la carpeta con los archivos XML de las facturas emitidas y recibidas
    ruta_carpeta_facturas_emitidas = os.path.join(directory,'XML',aniomodal,nombremesmodal,'EMITIDAS', 'FacturasE')



    ruta_carpeta_facturas_recibidas = os.path.join(directory,'XML',aniomodal,nombremesmodal,'RECIBIDAS', 'Facturas')

    ruta_carpeta_retenciones = os.path.join(directory,'XML',aniomodal,nombremesmodal,'EMITIDAS', 'RetencionesE')


    ruta_anulados = r'C:\IA\SRIBOT\XML\ANULADOS\comprobantes_anulados.txt'


    # Parsear los archivos XML de la carpeta de facturas emitidas
    factura_emitidas_roots = []
    for archivo in os.listdir(ruta_carpeta_facturas_emitidas):
        if archivo.endswith('.xml'):
            ruta_archivo = os.path.join(ruta_carpeta_facturas_emitidas, archivo)
            root, numero_autorizacion = parsear_xml_desde_archivo(ruta_archivo)
            if root is not None and numero_autorizacion is not None:
                factura_emitidas_roots.append((root, numero_autorizacion))

    # Parsear los archivos XML de la carpeta de facturas recibidas
    factura_recibidas_roots = []
    for archivo in os.listdir(ruta_carpeta_facturas_recibidas):
        if archivo.endswith('.xml'):
            ruta_archivo = os.path.join(ruta_carpeta_facturas_recibidas, archivo)
            root, numero_autorizacion = parsear_xml_desde_archivo(ruta_archivo)
            if root is not None and numero_autorizacion is not None:
                factura_recibidas_roots.append((root, numero_autorizacion))


    crear_ats(factura_emitidas_roots, factura_recibidas_roots, ruta_carpeta_retenciones, r'C:\IA\SRIBOT\XML', ruta_anulados)
    result_message = f"Archivo ATS creado exitosamente en {os.path.join(directory, 'XML', aniomodal, nombremesmodal)}"
    return result_message

    
def go_view_generatoXML(request):
    return render(request, 'view_generator.html')

def guardar_anulados(request):
    if request.method == 'POST':
        tipo_comprobante = request.POST.get('tipoComprobante')
        autorizacion = request.POST.get('autorizacion')

        # Extraer los campos del campo 'autorizacion'
        establecimiento = autorizacion[24:27]
        puntoEmision = autorizacion[27:30]
        secuencialInicio = autorizacion[30:39]
        secuencialFin = autorizacion[30:39]

        # Ruta del archivo en C:\ia\SRIBOT\XML\ANULADOS
        folder_path = os.path.join('C:\\', 'ia', 'SRIBOT', 'XML', 'ANULADOS')
        file_path = os.path.join(folder_path, 'comprobantes_anulados.txt')

        # Crear la carpeta si no existe
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Verificar si la autorización ya existe en el archivo
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    if autorizacion in line:
                        return JsonResponse({'output': "La autorización ya existe en el archivo"}, status=400)

        # Verificar si el archivo está vacío
        is_empty = not os.path.exists(file_path) or os.path.getsize(file_path) == 0

        with open(file_path, 'a') as file:
            # Escribir los encabezados si el archivo está vacío
            if is_empty:
                file.write('tipoComprobante\tautorizacion\testablecimiento\tpuntoEmision\tsecuencialInicio\tsecuencialFin\n')
            # Escribir la nueva línea de datos
            file.write(f'{tipo_comprobante}\t{autorizacion}\t{establecimiento}\t{puntoEmision}\t{secuencialInicio}\t{secuencialFin}\n')

        return JsonResponse({'output': "Comprobante anulado guardado correctamente"})
    return JsonResponse({'output': "Método no permitido"}, status=405)


def crearats(request):
    query = """
    SELECT id, 
           CONVERT(VARCHAR(MAX), DECRYPTBYPASSPHRASE('0102070612aq', RUC)) AS RUC, 
           password 
    FROM users;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    users = []
    for row in rows:
        users.append({
            "id": row[0],
            "ruc": row[1],
            "password": row[2]
        })
        
    if request.method == 'POST':
        action = request.POST.get('action')
        username = request.POST.get('username')
        password = request.POST.get('password')
        mes = request.POST.get('mes')
        mesemitidos = request.POST.get('mesemitidos')
        nombremesmodal = request.POST.get('nombremesmodal')
        nombremesrecibidos = request.POST.get('nombremesrecibidos')
        nombremesemitidos = request.POST.get('nombremesemitidos')
        anio = request.POST.get('anio')
        aniomodal = request.POST.get('aniomodal')
        anioemitidos = request.POST.get('anioemitidos')
        dia = request.POST.get('dia')
        diaemitidos =  request.POST.get('diaemitidos')
        tipo_comprobante = request.POST.get('tipo_comprobante')
        tipo_comprobante_emitidos = request.POST.get('tipo_comprobante_emitidos')
        
        directory = request.POST.get('directory')

        result_message = ""

        if action == 'BOTATS':
            thread = threading.Thread(target=ejecutar_script, args=(username, password, mes, nombremesrecibidos, dia, tipo_comprobante, directory,anio))
            thread.start()
            result_message = "El script se está ejecutando en segundo plano"
        elif action == 'BOTEMITIDOS':
            thread = threading.Thread(target=ejecutar_script_botemitidos, args=(username, password, mesemitidos, nombremesemitidos, diaemitidos,
                                                                                 directory,anioemitidos,tipo_comprobante_emitidos))
            thread.start()
            result_message = "El script se está ejecutando en segundo plano"
        elif action == 'ReporteRecibidos':
            thread = threading.Thread(target=ejecutar_script_reporterecibidos, args=(directory, nombremesmodal, aniomodal))
            thread.start()
        elif action == 'ReporteEmitidos':
            thread = threading.Thread(target=ejecutar_script_reporteemitidos, args=(directory, nombremesmodal, aniomodal))
            thread.start()
            
        elif action == 'CrearAts':
            def thread_func():
                result_message = ejecutar_script_crearats(directory, nombremesmodal, aniomodal)
                return result_message

            thread = threading.Thread(target=thread_func)
            thread.start()
            thread.join()  # Espera a que el thread termine para capturar el mensaje
            result_message = thread_func()  # Captura el mensaje generado por la función

        return JsonResponse({'output': result_message})

    days = list(range(1, 32))  # Generar la lista de días del 1 al 31
    current_year = datetime.datetime.now().year
    last_five_years = list(range(current_year, current_year - 5, -1))  #
    sendState('')
    return render(request, 'crearats.html', {'days': days, 'years': last_five_years, 'users': json.dumps(users)})

def check_xml_files(request):
    if request.method == 'POST':
        button_id = request.POST.get('button_id')
        nombremesrecibidos = request.POST.get('nombremesrecibidos')
        directory = request.POST.get('directorys')
        anio = request.POST.get('anio')
        
        full = os.path.join(f"{directory}\\XML",f"{anio}", f"{nombremesrecibidos}",'RECIBIDAS', button_id)

        # Imprimir el directorio para verificar que es correcto
        print(f"Directorio a verificar: {full}")

        # Ruta al script y al intérprete Python
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'comprobantesrecibidos.py')
        python_executable = 'python'  # Cambia esto a la ruta de tu intérprete Python si es necesario

        try:
            result = subprocess.run([python_executable, script_path, full], capture_output=True, text=True)
            output = result.stdout.strip()
            if result.returncode == 0:
                if "No se encontraron archivos XML" in output or "[WinError 3]" in output:
                    return JsonResponse({'status': 'error', 'output': output})
                else:
                    return JsonResponse({'status': 'success', 'output': output})
            else:
                return JsonResponse({'status': 'error', 'output': result.stderr.strip()})
        except Exception as e:
            return JsonResponse({'status': 'error', 'output': str(e)})

    return JsonResponse({'status': 'error', 'output': 'Invalid request method.'})

from django.db import connections
import re

def verify_data(directoryXml):
    # Consultar y verificar los registros con de la base de datos
    xml_files = glob.glob(os.path.join(directoryXml, '*.xml'))
    num_xml_files = len(xml_files)
    # Informacion de la base de datos
    parts = directoryXml.split(os.path.sep)
    directoryDb = os.path.join(*parts[2:])
    dbName = directoryDb.replace(os.path.sep, '_')
    continue_proccess = True
    # Condicion para la creacion de la base de datos
    with connections['xml_db_content'].cursor() as cursor:
        cursor.execute(f"""
            IF OBJECT_ID('{dbName}', 'U') IS NOT NULL
            BEGIN
                SELECT 1
            END
            ELSE
            BEGIN
                SELECT 0
            END
        """)
        resultado = cursor.fetchone()
        
        if resultado[0] == 1:
            print(f"La tabla '{dbName}' ya existe.")
        else:
            cursor.execute(f"""
                CREATE TABLE {dbName} (
                    id INT PRIMARY KEY IDENTITY,
                    clave NVARCHAR(255),
                    contenido xml,
                    fecha_registro DATETIME, 
                    fecha_emision DATE, 
                    hora_emision TIME
                )
            """)

    # Ver los registros de la base de datos
    with connections['xml_db_content'].cursor() as cursor:
        cursor.execute(f"SELECT * FROM {dbName}")
        registrosXml = cursor.fetchall()
    claves = [registro[1] for registro in registrosXml]

    with connections['xml_db_content'].cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {dbName}")
        resultado = cursor.fetchone()
        num_registros = resultado[0]

    # Guardar en un arreglo todos los nombres de los archivos para luego compararlos con las claves de acceso en la base de datos
    if num_registros < num_xml_files:
        names_files = [os.path.splitext(os.path.basename(file))[0] for file in xml_files]
        # Buscar que elemento falta en el arreglo de la base de datos, esto con el fin de que se pueda registrar en la base.
        missing_elements = list(set(names_files) - set(claves))
        continue_proccess = True
        return continue_proccess, dbName, missing_elements
    # En caso de que el numero de registros en la base y la carpeta sean iguales
    if num_registros == num_xml_files:
        # Ahora la condicion en caso de que ambos este vacios
        if num_registros == 0 and num_xml_files == 0:
            continue_proccess = True
            missing_elements = []
            return continue_proccess, dbName, missing_elements
        else:
            continue_proccess = False
            missing_elements = []
            return continue_proccess, dbName, missing_elements
    if num_registros >  num_xml_files:
        # Aqui debe haber un  proceso para generar los xml desde la base a la carpeta
        continue_proccess = False
        names_files = [os.path.splitext(os.path.basename(file))[0] for file in xml_files]
        create_xml(dbName, claves, names_files, directoryXml)
        missing_elements = []
        return continue_proccess, dbName, missing_elements
    

def control_acent(xml, simbolo='�'):
    reemplazos = {
        'á': simbolo,
        'é': simbolo,
        'í': simbolo,
        'ó': simbolo,
        'ú': simbolo,
        'Á': simbolo,
        'É': simbolo,
        'Í': simbolo,
        'Ó': simbolo,
        'Ú': simbolo,
        'ñ': simbolo,
        'Ñ': simbolo
    }
    for acentuada, reemplazo in reemplazos.items():
        xml = xml.replace(acentuada, reemplazo)
    return xml

def save_xml_db(dbName, xml_files, missing_array_db):
    if len(missing_array_db) != 0:
        filtered_files = [file for file in xml_files if os.path.splitext(os.path.basename(file))[0] in missing_array_db]
        for file in filtered_files:
            with open(file, 'r', encoding='utf-8') as f:
                xml_content_aut = f.read()
            try:
                root = ET.fromstring(xml_content_aut)
            except ET.ParseError as e:
                print(f"Error en el contenido XML: {e}")
                continue

            numero_autorizacion = root.find('.//numeroAutorizacion').text
            cdata_node = root.find('.//comprobante').text
            try:
                cdata_root = ET.fromstring(cdata_node)
            except ET.ParseError as e:
                print(f"Error al parsear CDATA: {e}")
                continue
            fecha_emision_str = cdata_root.find('.//fechaEmision').text
            fecha_emision = datetime.datetime.strptime(fecha_emision_str, "%d/%m/%Y").date()
            fecha_registro = datetime.datetime.now()
            hora_emision = fecha_registro.time()
            with open(file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            try:
                xml_content = ET.fromstring(xml_content)
            except ET.ParseError as e:
                print(f"Error al parsear CDATA: {e}")
                continue
            xml_content = ET.tostring(root, encoding='unicode')
            xml_content = re.sub(r'<\?xml version="1.0" encoding="UTF-8" standalone="yes"\?>', '', xml_content)
            xml_content = re.sub(r'<!\[CDATA\[\s*\s*\]\]>', '', xml_content)
            xml_content = xml_content.replace('&lt;', '<').replace('&gt;', '>')
            xml_content = xml_content.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
            # Identificar los caracteres especiales y reemplazarlos
            xml_content = control_acent(xml_content, '�')
            # Creación del registro en la base de datos
            with connections['xml_db_content'].cursor() as cursorSave:
                sql = f"""
                INSERT INTO {dbName} (clave, contenido, fecha_registro, fecha_emision, hora_emision)
                VALUES (%s, CAST(%s AS XML), %s, %s, %s)
                """
                cursorSave.execute(sql, (numero_autorizacion, xml_content, fecha_registro, fecha_emision, hora_emision))
                print(f"Registros filtrados insertados correctamente para {file}")
    else:
        for xml_file in xml_files:
            try:
                with open(xml_file, 'r', encoding='utf-8') as file:
                    xml_content_autorizacion = file.read()
                # Verificacion del XML
                try:
                    root = ET.fromstring(xml_content_autorizacion)
                except ET.ParseError as e:
                    print(f"Error en el contenido XML: {e}")
                    continue

                numero_autorizacion = root.find('.//numeroAutorizacion').text
                cdata_node = root.find('.//comprobante').text
                try:
                    cdata_root = ET.fromstring(cdata_node)
                except ET.ParseError as e:
                    print(f"Error al parsear CDATA: {e}")
                    continue
                fecha_emision_str = cdata_root.find('.//fechaEmision').text
                fecha_emision = datetime.datetime.strptime(fecha_emision_str, "%d/%m/%Y").date()
                fecha_registro = datetime.datetime.now()
                hora_emision = fecha_registro.time()
                
                # Registro de XML para poder obtener todo el archivo completo
                with open(xml_file, 'r', encoding='utf-8') as file:
                    xml_content = file.read()
                try:
                    xml_content = ET.fromstring(xml_content)
                except ET.ParseError as e:
                    print(f"Error al parsear CDATA: {e}")
                    continue

                xml_content = ET.tostring(root, encoding='unicode')
                xml_content = re.sub(r'<\?xml version="1.0" encoding="UTF-8" standalone="yes"\?>', '', xml_content)
                xml_content = re.sub(r'<!\[CDATA\[\s*\s*\]\]>', '', xml_content)
                xml_content = xml_content.replace('&lt;', '<').replace('&gt;', '>')
                xml_content = xml_content.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
                # Identificar los caracteres especiales y reemplazarlos
                xml_content = control_acent(xml_content, '�')
                # Creación del registro en la base de datos
                with connections['xml_db_content'].cursor() as cursorSave:
                    sql = f"""
                    INSERT INTO {dbName} (clave, contenido, fecha_registro, fecha_emision, hora_emision)
                    VALUES (%s, CAST(%s AS XML), %s, %s, %s)
                    """
                    cursorSave.execute(sql, (numero_autorizacion, xml_content, fecha_registro, fecha_emision, hora_emision))
                    print(f"Registro insertado correctamente para {xml_file}")
            except Exception as e:
                print(f"Error al insertar en la base de datos para {xml_file}: {e}")

def create_xml(dbName, claves, names_files, directoryXml):
    missing_elements = list(set(claves) - set(names_files))
    for clave in missing_elements:
        # Consulta para ver los registros de la base de datos
        with connections['xml_db_content'].cursor() as cursor:
            cursor.execute(f"SELECT * FROM {dbName} WHERE clave = '{clave}'")
            registrosXml = cursor.fetchall()

        content_xml = [registro[2] for registro in registrosXml]
        # Estructura del XML
        xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        contenido_completo = ''.join(content_xml)
        contenido_completo = xml_declaration + contenido_completo
        contenido_completo = re.sub(r'(</[^>]+>)', r'\1\n', contenido_completo)
        contenido_completo = re.sub(
            r'(<comprobante>)(.*?)(</comprobante>)',
            r'\1<![CDATA[\2]]>\3',
            contenido_completo,
            flags=re.DOTALL
        )

        nombre_archivo = f"{clave}.xml"
        ruta_archivo = os.path.join(directoryXml, nombre_archivo)

        with open(ruta_archivo, 'w', encoding='utf-8') as archivo_xml:
            archivo_xml.write(contenido_completo)

        print(f"Archivo XML creado: {ruta_archivo}")

def check_xml_files_emitidos(request):
    if request.method == 'POST':
        button_id = request.POST.get('button_id')
        nombremesemitidos = request.POST.get('nombremesemitidos')
        directory = request.POST.get('directorys')
        anioemitidos = request.POST.get('anioemitidos')


        full = os.path.join(f"{directory}\\XML",f"{anioemitidos}", f"{nombremesemitidos}",'EMITIDAS', button_id)
        
        # Imprimir el directorio para verificar que es correcto
        print(f"Directorio a verificar: {full}")

        # Ruta al script y al intérprete Python
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'comprobantesemitidos.py')
        python_executable = 'python'  # Cambia esto a la ruta de tu intérprete Python si es necesario

        try:
            result = subprocess.run([python_executable, script_path, full], capture_output=True, text=True)
            output = result.stdout.strip()
            if result.returncode == 0:
                if "No se encontraron archivos XML" in output or "[WinError 3]" in output:
                    return JsonResponse({'status': 'error', 'output': output})
                else:
                    return JsonResponse({'status': 'success', 'output': output})
            else:
                return JsonResponse({'status': 'error', 'output': result.stderr.strip()})
        except Exception as e:
            return JsonResponse({'status': 'error', 'output': str(e)})

    return JsonResponse({'status': 'error', 'output': 'Invalid request method.'})

@csrf_exempt
def delete_files(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            directory = data.get('ruta')
            if not directory:
                return JsonResponse({'error': 'No se proporcionó ninguna ruta.'})
            
            if not os.path.exists(directory):
                return JsonResponse({'error': 'La ruta no existe.'})

            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    return JsonResponse({'error': str(e)})
            return JsonResponse({'message': 'Todos los archivos han sido eliminados'})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    return JsonResponse({'error': 'Método no permitido.'})