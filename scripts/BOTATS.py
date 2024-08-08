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
import tkinter as tk
from tkinter import messagebox, ttk
from selenium.common.exceptions import TimeoutException

# Obtener los argumentos de usuario y contraseña
username = sys.argv[1]
password = sys.argv[2]
mes = sys.argv[3]
nombremesrecibidos = sys.argv[4]
dia = sys.argv[5]
tipo_comprobante = sys.argv[6]
directory = sys.argv[7]
anio = sys.argv[8]

tipo_comprobante_nombres = {
    "1": "Facturas",
    "2": "Liquidaciones",
    "3": "NotasCredito",
    "4": "NotasDebito",
    "6": "Retenciones"
}

# Crear Carpeta SRIBOT EN DOCUMENTOS
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

# Configuración del Bot
chrome_options.add_extension("C:\\Resolver.crx")

# Iniciar el navegador
driver = webdriver.Chrome(options=chrome_options)

# URL de la pagina del SRI
url = "https://srienlinea.sri.gob.ec/auth/realms/Internet/protocol/openid-connect/auth?client_id=app-sri-claves-angular&redirect_uri=https%3A%2F%2Fsrienlinea.sri.gob.ec%2Fsri-en-linea%2F%2Fcontribuyente%2Fperfil&state=f535d2b5-e613-4f17-8669-fac1a601b292&nonce=089fd62c-1ea9-4f7f-b502-1617eeb0a8ba&response_mode=fragment&response_type=code&scope=openid"

# Abrir la página en el navegador
driver.get(url)
try:
    # Esperar hasta que el campo de usuario esté presente en la página
    input_usuario = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "usuario"))
    )

    # Ingresar el usuario
    input_usuario.send_keys(username)
    print("Usuario ingresado con éxito.")

    # Esperar hasta que el campo de contraseña esté presente en la página
    input_password = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="password"]'))
    )

    # Ingresar la contraseña
    input_password.send_keys(password)
    print("Contraseña ingresada con éxito.")

    # Encontrar el botón de inicio de sesión y hacer clic en él
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="kc-login"]'))
    )
    login_button.click()
    print("Inicio de sesión exitoso.")

    try:
        # Saltarse encuesta 24/04/2024
        ubicarse = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="mat-dialog-0"]/sri-modal-perfil/sri-titulo-modal-mat/div/div[2]/button/span'))
        )

        ubicarse.click()
        print("Encuesta encontrada y saltada.")
    except TimeoutException:
        print("La encuesta no se encontró. Continuando con el resto del código.")

    driver.get("https://srienlinea.sri.gob.ec/tuportal-internet/accederAplicacion.jspa?redireccion=57&idGrupo=55")

    # Seleccionar el año
    select_anio_element = WebDriverWait(driver, 10).until(
       EC.presence_of_element_located((By.ID, 'frmPrincipal:ano'))
    )
    select_anio = Select(select_anio_element)
    select_anio.select_by_value(anio)
    print("Año seleccionado:", anio)

    # Seleccionar el mes
    select_mes_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'frmPrincipal:mes'))
    )
    select_mes = Select(select_mes_element)
    select_mes.select_by_value(mes)
    print("Mes seleccionado:", mes)

    # Seleccionar el día
    select_dia_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'frmPrincipal:dia'))
    )
    select_dia = Select(select_dia_element)
    select_dia.select_by_value(dia)
    print("Día seleccionado:", dia)

    # Seleccionar el tipo de comprobante
    tipo_comprobante_select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'frmPrincipal:cmbTipoComprobante'))
    )
    tipo_comprobante_select = Select(tipo_comprobante_select_element)
    tipo_comprobante_select.select_by_value(tipo_comprobante)
    print("Tipo de comprobante seleccionado:", tipo_comprobante)

    # Obtener el nombre de la carpeta del tipo de comprobante
    tipo_comprobante_nombre = tipo_comprobante_nombres.get(tipo_comprobante, "Desconocido")
    tipo_comprobante_folder = os.path.join(f"{directory}\\XML\\{anio}\\{nombremesrecibidos}\\RECIBIDAS", tipo_comprobante_nombre)
    os.makedirs(tipo_comprobante_folder, exist_ok=True)
    print("Carpeta creada para el tipo de comprobante:", tipo_comprobante_nombre)

    # Hacer clic en el elemento recaptcha
    recaptcha_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="btnRecaptcha"]'))
    )
    recaptcha_button.click()
    print("Clic en el botón Recaptcha exitoso.")

    # Esperar que la IA resuelva el captcha
    time.sleep(60)

    # Descargar listado txt
    listado_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="frmPrincipal:lnkTxtlistado"]'))
    )
    listado_button.click()
    print("Clic en el enlace para obtener el listado.")

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
                # Obtener el valor de numero_autorizacion
                numero_autorizacion = obtener_numero_autorizacion(file)

                # Renombrar el archivo con el valor de numero_autorizacion
                new_filename = f"{xml_folder}\\{numero_autorizacion}.xml"
                os.rename(file, new_filename)
                print(f"Archivo {file} renombrado como {new_filename}")

                # Mover el archivo a la carpeta correspondiente del tipo de comprobante en RECIBIDAS
                shutil.move(new_filename, tipo_comprobante_folder)
                print(f"Archivo {new_filename} movido a {tipo_comprobante_folder}")
            except Exception as e:
                print(f"Error al procesar el archivo {file}: {e}")

    # Función para hacer clic en los enlaces y descargar los archivos XML
    def hacer_clic_en_enlace():
        paginacion_previa = ""
        while True:
            try:
                # Verificar si es la última página
                span_paginacion = driver.find_element(By.XPATH,
                                                      '/html/body/div[2]/div[2]/div[3]/form[2]/div[5]/div/div[2]/table/tfoot/tr/td/span[3]')
                texto_paginacion = span_paginacion.text
                print("Texto de paginación:", texto_paginacion)

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
                    print(f"Clic en el enlace {enlace.text}")
                    time.sleep(1)  # Espera 1 segundo antes de continuar

                # Hacer clic en el enlace de paginación
                enlace_siguiente = driver.find_element(By.XPATH,
                                                       '//*[@id="frmPrincipal:tablaCompRecibidos_paginator_bottom"]/span[4]')
                enlace_siguiente.click()
                print("Clic en enlace de paginación.")
                time.sleep(5)  # Espera 5 segundos para cargar la página siguiente

                # Mover el cursor del mouse sobre el botón de captcha
                action = ActionChains(driver)
                action.move_to_element(recaptcha_button).perform()

            except:
                break  # Salir del bucle si no hay más páginas

        # Llamada a la función para renombrar los archivos XML
        renombrar_xmls()

    # Llamada a la función para hacer clic en los enlaces y descargar los archivos XML
    hacer_clic_en_enlace()

    # Crear una ventana emergente para mostrar el mensaje
    ventana_emergente = tk.Tk()
    ventana_emergente.title("Descarga exitosa")

    # Función para cerrar la ventana emergente y finalizar el programa
    def cerrar_ventana():
        ventana_emergente.destroy()
        driver.quit()  # Cerrar el navegador y finalizar el programa

    # Mensaje para mostrar en la ventana emergente
    mensaje = "Comprobantes descargados correctamente."

    # Etiqueta para mostrar el mensaje
    etiqueta = tk.Label(ventana_emergente, text=mensaje)
    etiqueta.pack(padx=20, pady=10)

    # Botón "Aceptar" para cerrar la ventana emergente
    boton_aceptar = tk.Button(ventana_emergente, text="Aceptar", command=cerrar_ventana)
    boton_aceptar.pack(pady=5)

    # Mostrar la ventana emergente
    ventana_emergente.mainloop()

except Exception as e:
    print("Error:", e)

finally:
    # Cerrar el navegador
    driver.quit()
