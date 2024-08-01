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


# Crear Carpeta SRIBOT EN DOCUMENTOS
documents_folder = 'C:\\ia\\SRIBOT'
os.makedirs(documents_folder, exist_ok=True)

xml_folder = os.path.join(documents_folder, 'XML')
os.makedirs(xml_folder, exist_ok=True)

# Obtener las subcarpetas dentro de la carpeta RECIBIDAS
recibidas_folder = os.path.join(xml_folder, 'RECIBIDAS')
os.makedirs(recibidas_folder, exist_ok=True)
subcarpetas_recibidas = [name for name in os.listdir(recibidas_folder) if
                         os.path.isdir(os.path.join(recibidas_folder, name))]


# Función para limpiar carpetas seleccionadas
def limpiar_carpetas():
    seleccion_subcarpeta = subcarpeta_var.get()
    if seleccion_subcarpeta == "No":
        messagebox.showinfo("Información", "No se ha limpiado ninguna carpeta.")
    elif seleccion_subcarpeta == "Todas":
        for subcarpeta in subcarpetas_recibidas:
            shutil.rmtree(os.path.join(recibidas_folder, subcarpeta))
            os.makedirs(os.path.join(recibidas_folder, subcarpeta), exist_ok=True)
        messagebox.showinfo("Éxito", "Todas las subcarpetas de RECIBIDAS han sido limpiadas.")
    else:
        shutil.rmtree(os.path.join(recibidas_folder, seleccion_subcarpeta))
        os.makedirs(os.path.join(recibidas_folder, seleccion_subcarpeta), exist_ok=True)
        messagebox.showinfo("Éxito", f"La subcarpeta {seleccion_subcarpeta} de RECIBIDAS ha sido limpiada.")
    ventana_opciones.destroy()


# Crear ventana Tkinter para opciones de limpieza
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
subcarpeta_combo['values'] = ["No", "Todas"] + subcarpetas_recibidas
subcarpeta_combo.pack(pady=5)

boton_aceptar = tk.Button(ventana_opciones, text="Aceptar", command=limpiar_carpetas)
boton_aceptar.pack(pady=10)

ventana_opciones.mainloop()

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
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="mat-dialog-0"]/sri-modal-perfil/sri-titulo-modal-mat/div/div[2]/button/span'))
        )

        ubicarse.click()
        print("Encuesta encontrada y saltada.")
    except TimeoutException:
        print("La encuesta no se encontró. Continuando con el resto del código.")

    driver.get("https://srienlinea.sri.gob.ec/tuportal-internet/accederAplicacion.jspa?redireccion=57&idGrupo=55")

    # VENTANA MES
    select_mes_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'frmPrincipal:mes'))
    )


    # Función para seleccionar el mes y continuar con el proceso
    def seleccionar_mes():
        global select_mes_element
        mes_nombre = mes_var.get()
        mes_valor = opciones_mes[mes_nombre]  # Obtener el valor del mes
        select_mes = Select(select_mes_element)
        select_mes.select_by_value(mes_valor)
        print("Mes seleccionado:", mes_nombre)
        ventana_mes.destroy()


    # Crear ventana Tkinter para seleccionar el mes
    ventana_mes = tk.Tk()
    ventana_mes.title("Selección de Mes")

    ancho_ventana_mes = 250  # Ancho de la ventana de selección de mes
    alto_ventana_mes = 200  # Alto de la ventana de selección de mes

    ancho_pantalla = ventana_mes.winfo_screenwidth()
    alto_pantalla = ventana_mes.winfo_screenheight()

    # Calcular la posición para centrar la ventana
    x = (ancho_pantalla // 2) - (ancho_ventana_mes // 2)
    y = (alto_pantalla // 2) - (alto_ventana_mes // 2)

    # Establecer la geometría de la ventana
    ventana_mes.geometry(f"{ancho_ventana_mes}x{alto_ventana_mes}+{x}+{y}")

    mes_var = tk.StringVar(ventana_mes)
    mes_var.set("Seleccione el Mes")  # Establecer valor predeterminado
    opciones_mes = {"Enero": "1", "Febrero": "2", "Marzo": "3", "Abril": "4", "Mayo": "5", "Junio": "6", "Julio": "7",
                    "Agosto": "8", "Septiembre": "9", "Octubre": "10", "Noviembre": "11", "Diciembre": "12"}
    mes_menu = tk.OptionMenu(ventana_mes, mes_var, *opciones_mes.keys())
    mes_menu.pack(pady=10)

    boton_aceptar_mes = tk.Button(ventana_mes, text="Aceptar", command=seleccionar_mes)
    boton_aceptar_mes.pack(pady=5)

    # Iniciar el bucle principal de la ventana Tkinter
    ventana_mes.mainloop()

    # VENTANA DIA
    select_dia_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'frmPrincipal:dia'))
    )


    def seleccionar_dia():
        global select_dia_element
        dia = dia_var.get()
        if dia == "Todos":
            print("Seleccionado todos los días.")
            select_dia = Select(select_dia_element)
            select_dia.select_by_value("0")  # Seleccionar la opción "Todos" (value 0)
        else:
            select_dia = Select(select_dia_element)
            select_dia.select_by_value(dia)
            print("Día seleccionado:", dia)
        ventana_dia.destroy()


    # Crear ventana Tkinter para seleccionar el día
    ventana_dia = tk.Tk()
    ventana_dia.title("Selección de Día")

    ancho_ventana_dia = 200  # Ancho de la ventana de selección de día
    alto_ventana_dia = 150  # Alto de la ventana de selección de día

    ancho_pantalla = ventana_dia.winfo_screenwidth()
    alto_pantalla = ventana_dia.winfo_screenheight()

    # Calcular la posición para centrar la ventana
    x = (ancho_pantalla // 2) - (ancho_ventana_dia // 2)
    y = (alto_pantalla // 2) - (alto_ventana_dia // 2)

    # Establecer la geometría de la ventana
    ventana_dia.geometry(f"{ancho_ventana_dia}x{alto_ventana_dia}+{x}+{y}")

    dia_var = tk.StringVar(ventana_dia)
    dia_var.set("Seleccione el Día")  # Establecer valor predeterminado
    opciones_dia = ["Todos"] + [str(i) for i in range(1, 32)]  # Días del 1 al 31
    dia_menu = tk.OptionMenu(ventana_dia, dia_var, *opciones_dia)
    dia_menu.pack(pady=10)

    boton_aceptar_dia = tk.Button(ventana_dia, text="Aceptar", command=seleccionar_dia)
    boton_aceptar_dia.pack(pady=5)

    # Iniciar el bucle principal de la ventana Tkinter
    ventana_dia.mainloop()

    # VENTANA TIPO DE COMPROBANTE
    tipo_comprobante_select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'frmPrincipal:cmbTipoComprobante'))
    )


    # Función para seleccionar el tipo de comprobante y continuar con el proceso
    def seleccionar_tipo_comprobante():
        global tipo_comprobante_select_element  # Declarar la variable como global para poder modificarla dentro de la función
        tipo_comprobante = tipo_comprobante_var.get()
        tipo_comprobante_select = Select(tipo_comprobante_select_element)
        if tipo_comprobante == "Facturas":
            tipo_comprobante_select.select_by_value("1")
        elif tipo_comprobante == "Liquidaciones":
            tipo_comprobante_select.select_by_value("2")
        elif tipo_comprobante == "NotasCredito":
            tipo_comprobante_select.select_by_value("3")
        elif tipo_comprobante == "NotasDebito":
            tipo_comprobante_select.select_by_value("4")
        elif tipo_comprobante == "Retenciones":
            tipo_comprobante_select.select_by_value("6")

        # Crear una carpeta para el tipo de comprobante seleccionado
        global tipo_comprobante_folder
        tipo_comprobante_folder = os.path.join("C:\\ia\\SRIBOT\\XML\\RECIBIDAS", tipo_comprobante)
        os.makedirs(tipo_comprobante_folder, exist_ok=True)
        print("Carpeta creada para el tipo de comprobante:", tipo_comprobante)

        ventana.destroy()


    # Crear ventana Tkinter
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
    opciones_tipo_comprobante = ["Seleccione el Tipo de Comprobante", "Facturas",
                                 "Liquidaciones", "NotasCredito",
                                 "NotasDebito", "Retenciones"]
    tipo_comprobante_menu = tk.OptionMenu(ventana, tipo_comprobante_var, *opciones_tipo_comprobante)
    tipo_comprobante_menu.pack(pady=10)

    boton_aceptar = tk.Button(ventana, text="Aceptar", command=seleccionar_tipo_comprobante)
    boton_aceptar.pack(pady=5)

    # Iniciar el bucle principal de la ventana Tkinter
    ventana.mainloop()

    # Hacer clic en el elemento //*[@id="btnRecaptcha"]
    recaptcha_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="btnRecaptcha"]'))
    )

    recaptcha_button.click()
    print("Clic en el botón Recaptcha exitoso.")

    # Esperar que la IA resuelva el captcha
    time.sleep(40)

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
                tipo_comprobante_recibidas_folder = os.path.join(recibidas_folder, tipo_comprobante_folder)
                os.makedirs(tipo_comprobante_recibidas_folder, exist_ok=True)
                shutil.move(new_filename, tipo_comprobante_recibidas_folder)
                print(f"Archivo {new_filename} movido a {tipo_comprobante_recibidas_folder}")
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
