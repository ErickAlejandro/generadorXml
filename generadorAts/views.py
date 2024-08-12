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

def ejecutar_script(username, password, mes, nombremesrecibidos, dia, tipo_comprobante, directory, anio):
    try:
        print(username, password, mes, nombremesrecibidos, dia, tipo_comprobante, directory, anio)
        tipo_comprobante_nombres = {
            "1": "Facturas",
            "2": "Liquidaciones",
            "3": "NotasCredito",
            "4": "NotasDebito",
            "6": "Retenciones"
        }
        sendState('')
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
            sendState('Ingresando al portal')

            try:
                # Saltarse encuesta 24/04/2024
                ubicarse = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//*[@id="mat-dialog-0"]/sri-modal-perfil/sri-titulo-modal-mat/div/div[2]/button/span'))
                )

                ubicarse.click()
                sendState('Encuesta encontrada y saltada')
            except TimeoutException:
                sendState('La encuesta no se encontró. Continuando con el resto del código.')

            driver.get("https://srienlinea.sri.gob.ec/tuportal-internet/accederAplicacion.jspa?redireccion=57&idGrupo=55")

            # Seleccionar el año
            select_anio_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'frmPrincipal:ano'))
            )
            select_anio = Select(select_anio_element)
            select_anio.select_by_value(anio)

            # Seleccionar el mes
            select_mes_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'frmPrincipal:mes'))
            )
            select_mes = Select(select_mes_element)
            select_mes.select_by_value(mes)

            # Seleccionar el día
            select_dia_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'frmPrincipal:dia'))
            )
            select_dia = Select(select_dia_element)
            select_dia.select_by_value(dia)

            # Seleccionar el tipo de comprobante
            tipo_comprobante_select_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'frmPrincipal:cmbTipoComprobante'))
            )
            tipo_comprobante_select = Select(tipo_comprobante_select_element)
            tipo_comprobante_select.select_by_value(tipo_comprobante)

            # Obtener el nombre de la carpeta del tipo de comprobante
            tipo_comprobante_nombre = tipo_comprobante_nombres.get(tipo_comprobante, "Desconocido")
            tipo_comprobante_folder = os.path.join(f"{directory}\\XML\\{anio}\\{nombremesrecibidos}\\RECIBIDAS", tipo_comprobante_nombre)
            os.makedirs(tipo_comprobante_folder, exist_ok=True)
            sendState('Creando carpetas ...')

            # Hacer clic en el elemento recaptcha
            recaptcha_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="btnRecaptcha"]'))
            )
            recaptcha_button.click()
            print("Clic en el botón Recaptcha exitoso.", flush=True)

            # Esperar que la IA resuelva el captcha
            time.sleep(60)

            # Verificar el texto de la paginación y hacer clic si los números no son iguales
            try:
                paginacion_texto_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="frmPrincipal:tablaCompRecibidos_paginator_bottom"]/span[3]'))
                )
                paginacion_texto = paginacion_texto_element.text.strip()
                print(f"Paginación detectada: {paginacion_texto}", flush=True)

                # Extraer los números del texto
                numeros = paginacion_texto.split(" of ")
                if len(numeros) == 2 and numeros[0] != numeros[1]:
                    print(f"Los números en la paginación no son iguales: {numeros[0]} y {numeros[1]}. Procediendo a hacer clic en la siguiente página.", flush=True)

                    # Hacer clic en el botón para ir a la siguiente página
                    siguiente_pagina_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="frmPrincipal:tablaCompRecibidos_paginator_bottom"]/span[5]'))
                    )
                    siguiente_pagina_button.click()
                    print("Clic en el botón de la siguiente página.", flush=True)

                    # Esperar a que la tabla se recargue
                    time.sleep(2)  # Espera para asegurar que la tabla se recargue

                    # Obtener el último `tr` de la tabla
                    tabla_elementos = driver.find_elements(By.XPATH, '/html/body/div[2]/div[2]/div[3]/form[2]/div[5]/div/div[2]/table/tbody/tr')
                    ultimo_tr = tabla_elementos[-1]  # Selecciona el último `tr`
                    ultimo_texto = ultimo_tr.text.strip()
                    print(f"Texto extraído del último `tr`: {ultimo_texto}", flush=True)
                    
                    # Extraer el texto específico que necesitas del `tr` (ajusta según la estructura de la fila)
                    texto_especifico = ultimo_tr.find_element(By.XPATH, 'td[1]').text.strip()
                    print(f"Texto específico extraído: {texto_especifico}", flush=True)

                    volver = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="frmPrincipal:tablaCompRecibidos_paginator_bottom"]/span[1]'))
                    )
                    volver.click()
                    print("Clic en el volver", flush=True)

                    action = ActionChains(driver)
                    action.move_to_element(recaptcha_button).perform()



            except Exception as e:
                print(f"Error al intentar verificar y extraer información de la paginación: {e}", flush=True)

            # Descargar listado txt
            listado_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="frmPrincipal:lnkTxtlistado"]'))
            )
            listado_button.click()
            print("Clic en el enlace para obtener el listado.", flush=True)

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
                        print(f"Archivo {file} renombrado como {new_filename}", flush=True)

                        # Mover el archivo a la carpeta correspondiente del tipo de comprobante en RECIBIDAS
                        shutil.move(new_filename, tipo_comprobante_folder)
                        print(f"Archivo {new_filename} movido a {tipo_comprobante_folder}", flush=True)
                    except Exception as e:
                        print(f"Error al procesar el archivo {file}: {e}", flush=True)

            # Función para hacer clic en los enlaces y descargar los archivos XML
            def hacer_clic_en_enlace():
                paginacion_previa = ""
                while True:
                    try:
                        # Verificar si es la última página
                        span_paginacion = driver.find_element(By.XPATH,
                                                            '/html/body/div[2]/div[2]/div[3]/form[2]/div[5]/div/div[2]/table/tfoot/tr/td/span[3]')
                        texto_paginacion = span_paginacion.text
                        print("Texto de paginación:", texto_paginacion, flush=True)

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
                            print(f"Clic en el enlace {enlace.text}", flush=True)
                            time.sleep(1)  # Espera 1 segundo antes de continuar

                        # Hacer clic en el enlace de paginación
                        enlace_siguiente = driver.find_element(By.XPATH,
                                                            '//*[@id="frmPrincipal:tablaCompRecibidos_paginator_bottom"]/span[4]')
                        enlace_siguiente.click()
                        print("Clic en enlace de paginación.", flush=True)
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
            print("Error:", e, flush=True)

    except Exception as e:
        print("Excepción al intentar ejecutar el script:", str(e), flush=True)


def sendState(text):
    if text == '':
        cache.set('estado_actual', 'Esperando ejecucion')
    else:
        cache.set('estado_actual', text)

def getEstado(request):
    estado = cache.get('estado_actual', 'Sin estado')
    return JsonResponse({'estado': estado})

def ejecutar_script_botemitidos(username, password, mesemitidos, nombremesemitidos, diaemitidos, directory,anioemitidos):
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'BOTEMITIDOS.py')
    python_executable = os.path.join(os.path.dirname(__file__), '..', 'venv', 'Scripts', 'python.exe')
    
    try:
        result = subprocess.run([python_executable, script_path, username, password, mesemitidos, nombremesemitidos, diaemitidos, directory,anioemitidos], capture_output=True, text=True)
        if result.returncode == 0:
            print("Script ejecutado con éxito")
            print("Salida:", result.stdout)
        else:
            print("Error al ejecutar el script")
            print("Error:", result.stderr)
    except Exception as e:
        print("Excepción al intentar ejecutar el script:", str(e))


def ejecutar_script_reporterecibidos(directory, nombremesmodal, aniomodal):
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'ReporteRecibidos.py')
    python_executable = os.path.join(os.path.dirname(__file__), '..', 'venv', 'Scripts', 'python.exe')
    result_message = ""

    try:
        print(f"Ejecutando script con: {directory}, {nombremesmodal}, {aniomodal}")
        result = subprocess.run([python_executable, script_path, directory, nombremesmodal, aniomodal], capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            result_message = result.stdout.strip()
            print("Script ejecutado con éxito")
            print("Salida:", result_message)
        else:
            result_message = "Error al ejecutar el script."
            print("Error al ejecutar el script")
            print("Error:", result.stderr.strip())
    except Exception as e:
        result_message = f"Excepción al intentar ejecutar el script: {str(e)}"
        print(result_message)

    return result_message

def ejecutar_script_reporteemitidos(directory, nombremesmodal, aniomodal):
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'ReporteEmitidos.py')
    python_executable = os.path.join(os.path.dirname(__file__), '..','venv', 'Scripts', 'python.exe')
    result_message = ""

    try:
        result = subprocess.run([python_executable, script_path,directory, nombremesmodal, aniomodal], capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            result_message = result.stdout.strip()
            print("Script ejecutado con éxito")
            print("Salida:", result_message)
        else:
            result_message = "Error al ejecutar el script."
            print("Error al ejecutar el script")
            print("Error:", result.stderr.strip())
    except Exception as e:
        result_message = f"Excepción al intentar ejecutar el script: {str(e)}"
        print(result_message)

    return result_message


def ejecutar_script_crearats(directory, nombremesmodal, aniomodal):
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'CrearAts.py')
    python_executable = os.path.join(os.path.dirname(__file__), '..','venv', 'Scripts', 'python.exe')
    result_message = ""
    state = ''
    try:
        result = subprocess.run([python_executable, script_path,directory, nombremesmodal, aniomodal], capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            # Si hay archivos
            result_message = result.stdout.strip()
            state = 'success'
        else:
            # NO hay archivo
            result_message = result.stderr.strip()
            state = 'None'
    except Exception as e:
        # Error en la ejecucion del scrip
        result_message = f"Excepción al intentar ejecutar el script: {str(e)}"
        state = 'error'
        print(result_message)

    context = {'state': state, 'result': result_message}
    return context




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
        directory = request.POST.get('directory')
        

        result_message = ""

        if action == 'BOTATS':
            thread = threading.Thread(target=ejecutar_script, args=(username, password, mes, nombremesrecibidos, dia, tipo_comprobante, directory,anio))
            thread.start()
            result_message = "El script se está ejecutando en segundo plano"
        elif action == 'BOTEMITIDOS':
            thread = threading.Thread(target=ejecutar_script_botemitidos, args=(username, password, mesemitidos, nombremesemitidos, diaemitidos,
                                                                                 directory,anioemitidos))
            thread.start()
            result_message = "El script se está ejecutando en segundo plano"
        elif action == 'ReporteRecibidos':
            result_message = ejecutar_script_reporterecibidos(directory, nombremesmodal, aniomodal)
            print(result_message)
        elif action == 'ReporteEmitidos':
            result_message = ejecutar_script_reporteemitidos(directory, nombremesmodal, aniomodal)
        elif action == 'CrearAts':
            result_message = ejecutar_script_crearats(directory, nombremesmodal, aniomodal)
        return JsonResponse({'output': result_message})

    days = list(range(1, 32))  # Generar la lista de días del 1 al 31
    current_year = datetime.datetime.now().year
    last_five_years = list(range(current_year, current_year - 5, -1))  # Generar los últimos 5 años incluyendo el actual
    return render(request, 'crearats.html', {'days': days, 'years': last_five_years})

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