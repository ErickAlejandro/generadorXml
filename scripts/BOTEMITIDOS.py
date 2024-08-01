import os
import time
import shutil
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import tkinter as tk
from tkinter import ttk
from selenium.common.exceptions import TimeoutException

from datetime import datetime
import requests
import xml.etree.ElementTree as ET
import glob

# Obtener los argumentos de usuario y contraseña
username = sys.argv[1]
password = sys.argv[2]

# Crear Carpeta SRIBOT EN DOCUMENTOS
documents_folder = 'C:\\ia\\SRIBOT'
os.makedirs(documents_folder, exist_ok=True)

# Crear carpeta XML dentro de SRIBOT
xml_folder = os.path.join(documents_folder, 'XML', 'EMITIDAS')

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

    # Buscar en todas las subcarpetas de la carpeta recibidas
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
                            print(
                                f"No se encontró el elemento 'RespuestaAutorizacionComprobante' para la clave {clave_acceso}.")
                    else:
                        print(
                            f"No se encontró el elemento 'autorizacionComprobanteResponse' para la clave {clave_acceso}.")
                else:
                    print(f"Error en la solicitud para la clave {clave_acceso}. Estado: {response.status_code}")


# Ventana emergente para seleccionar la opción de procesamiento
def seleccionar_opcion():
    def enviar_seleccion():
        opcion_seleccionada = combobox.get()
        if opcion_seleccionada == "Sí":
            ventana.destroy()
            procesar_archivos_txt()
        elif opcion_seleccionada == "No":
            ventana.destroy()
            iniciar_proceso_completo()

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
    combobox = ttk.Combobox(ventana, values=opciones, state="readonly")
    combobox.pack(pady=10)
    combobox.current(0)  # Selecciona la primera opción por defecto

    tk.Button(ventana, text="Aceptar", command=enviar_seleccion).pack(pady=10)

    ventana.mainloop()


# Función para iniciar el proceso completo
def iniciar_proceso_completo():
    # Iniciar el navegador
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # URL de la página del SRI
        url = "https://srienlinea.sri.gob.ec/auth/realms/Internet/protocol/openid-connect/auth?client_id=app-sri-claves-angular&redirect_uri=https%3A%2F%2Fsrienlinea.sri.gob.ec%2Fsri-en-linea%2F%2Fcontribuyente%2Fperfil&state=f535d2b5-e613-4f17-8669-fac1a601b292&nonce=089fd62c-1ea9-4a7f-b502-1617eeb0a8ba&response_mode=fragment&response_type=code&scope=openid"

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
                    EC.element_to_be_clickable((By.XPATH,
                                                '//*[@id="mat-dialog-0"]/sri-modal-perfil/sri-titulo-modal-mat/div/div[2]/button/span'))
                )
                ubicarse.click()
            except TimeoutException:
                print("La encuesta no se encontró. Continuando con el resto del código.")

            menu_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="sri-menu"]/span'))
            )
            menu_button.click()
            print("Menú desplegable abierto con éxito.")

            # Esperar a que el elemento mySidebar se cargue
            sidebar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "mySidebar"))
            )

            # Buscar el texto 'FACTURACIÓN ELECTRÓNICA' dentro del sidebar
            facturacion_electronica = WebDriverWait(sidebar, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'FACTURACIÓN ELECTRÓNICA')]"))
            )
            facturacion_electronica.click()

            produccion = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="mySidebar"]/p-panelmenu/div/div[4]/div[2]/div/p-panelmenusub/ul/li[4]/a'))
            )
            produccion.click()

            consulta = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                                            '//*[@id="mySidebar"]/p-panelmenu/div/div[4]/div[2]/div/p-panelmenusub/ul/li[4]/p-panelmenusub/ul/li[2]/a'))
            )
            consulta.click()

            emitidos = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="consultaDocumentoForm:panelPrincipal"]/ul/li[2]/a'))
            )
            emitidos.click()

            # Función para manejar la selección del mes y actualizar la fecha en el formulario
            def seleccionar_mes():
                def enviar_seleccion():
                    mes_seleccionado = combobox.get()
                    mes_numerico = meses[mes_seleccionado]
                    fecha = f"01/{mes_numerico}/{time.strftime('%Y')}"

                    # Ingresar la fecha en el campo correspondiente
                    fecha_desde_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="frmPrincipal:calendarFechaDesde_input"]'))
                    )
                    fecha_desde_input.clear()
                    fecha_desde_input.send_keys(fecha)
                    print(f"Fecha {fecha} ingresada con éxito.")

                    # Cerrar la ventana de selección
                    root.destroy()

                root = tk.Tk()
                root.title("Seleccione el mes")

                tk.Label(root, text="Seleccione el mes que desea descargar:").pack(pady=10)

                meses = {
                    "Enero": "01", "Febrero": "02", "Marzo": "03", "Abril": "04",
                    "Mayo": "05", "Junio": "06", "Julio": "07", "Agosto": "08",
                    "Septiembre": "09", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"
                }

                combobox = ttk.Combobox(root, values=list(meses.keys()), state="readonly")
                combobox.pack(pady=10)
                combobox.current(0)

                tk.Button(root, text="Aceptar", command=enviar_seleccion).pack(pady=10)

                root.mainloop()

            # Función para seleccionar el tipo de comprobante y continuar con el proceso
            def seleccionar_tipo_comprobante():
                def enviar_seleccion():
                    tipo_comprobante_value = tipo_comprobante_var.get()

                    # Crear carpeta para el tipo de comprobante
                    global comprobante_folder
                    comprobante_folder = os.path.join(xml_folder, tipo_comprobante_value)
                    os.makedirs(comprobante_folder, exist_ok=True)

                    print(f"Carpeta creada para el tipo de comprobante: {comprobante_folder}")
                    global tipo_comprobante_value_global
                    tipo_comprobante_value_global = tipo_comprobante_value
                    ventana.destroy()

                ventana = tk.Tk()
                ventana.title("Selección de Tipo de Comprobante")

                ancho_ventana = 350
                alto_ventana = 150

                ancho_pantalla = ventana.winfo_screenwidth()
                alto_pantalla = ventana.winfo_screenheight()

                # Calcular la posición para centrar la ventana
                x = (ancho_pantalla // 2) - (ancho_ventana // 2)
                y = (alto_pantalla // 2) - (alto_ventana // 2)

                ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")

                tipo_comprobante_var = tk.StringVar(ventana)
                tipo_comprobante_var.set("Seleccione el Tipo de Comprobante")  # Establecer valor predeterminado
                opciones_tipo_comprobante = ["Seleccione el Tipo de Comprobante", "FacturasE",
                                             "LiquidacionesE",
                                             "NotasCreditoE", "NotasDebitoE", "RetencionesE"]
                tipo_comprobante_menu = tk.OptionMenu(ventana, tipo_comprobante_var, *opciones_tipo_comprobante)
                tipo_comprobante_menu.pack(pady=10)

                boton_aceptar = tk.Button(ventana, text="Aceptar", command=enviar_seleccion)
                boton_aceptar.pack(pady=5)

                # Iniciar el bucle principal de la ventana Tkinter
                ventana.mainloop()

            # Función para verificar el mensaje de alerta
            def alert_message():
                for dia in range(1, 32):
                    print("Descargando del Día: ", dia)
                    try:
                        fecha_input = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="frmPrincipal:calendarFechaDesde_input"]'))
                        )
                        texto_input = fecha_input.get_attribute('value')
                        day_current, mes, anio = texto_input.split('/')
                        fecha = f"{dia}/{mes}/{anio}"

                        fecha_actual = datetime.now()
                        fecha_verificar = datetime.strptime(fecha, "%d/%m/%Y")

                        if fecha_verificar >= fecha_actual:
                            print("La fecha es mayor o igual a la fecha actual. Terminando el proceso.")
                            break

                        fecha_input.clear()
                        fecha_input.send_keys(fecha)
                        time.sleep(2)

                        # Seleccionar el tipo de comprobante
                        tipo_comprobante_select_element = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="frmPrincipal:cmbTipoComprobante"]'))
                        )

                        # Seleccionar el tipo de comprobante
                        tipo_comprobante_select = Select(tipo_comprobante_select_element)
                        if tipo_comprobante_value_global == "FacturasE":
                            tipo_comprobante_select.select_by_value("1")
                        elif tipo_comprobante_value_global == "LiquidacionesE":
                            tipo_comprobante_select.select_by_value("2")
                        elif tipo_comprobante_value_global == "NotasCreditoE":
                            tipo_comprobante_select.select_by_value("3")
                        elif tipo_comprobante_value_global == "NotasDebitoE":
                            tipo_comprobante_select.select_by_value("4")
                        elif tipo_comprobante_value_global == "RetencionesE":
                            tipo_comprobante_select.select_by_value("6")

                        # Ejecutar el botón de búsqueda
                        print("click en la consulta ...")
                        recaptcha_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="btnRecaptcha"]'))
                        )
                        recaptcha_button.click()
                        time.sleep(45)

                        # Dar click en el botón de descarga
                        print("click en el boton de descarga ...")
                        listado_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="frmPrincipal:lnkTxtlistado"]'))
                        )
                        listado_button.click()
                        time.sleep(5)
                        continue
                    except Exception as e:
                        print(f'Error en el dia {dia}: {str(e)}')
                        continue

            # Llamar a la función para seleccionar el mes
            seleccionar_mes()

            # Seleccionar el tipo de comprobante una sola vez
            seleccionar_tipo_comprobante()

            # Ejecutar la función de revisión para la alerta
            alert_message()

            # Mover todos los archivos descargados a la carpeta correspondiente
            for file_name in os.listdir(xml_folder):
                file_path = os.path.join(xml_folder, file_name)
                if os.path.isfile(file_path) and file_path.endswith('.txt'):
                    shutil.move(file_path, comprobante_folder)
                    print(f"Archivo {file_name} movido a {comprobante_folder}")

            procesar_archivos_txt()

        except Exception as e:
            print("Error:", e)

        finally:

            driver.quit()

    except Exception as e:
        print("Error:", e)


# Mostrar la ventana emergente de selección
seleccionar_opcion()
