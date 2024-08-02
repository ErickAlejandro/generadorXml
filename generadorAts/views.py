from django.shortcuts import render

# Create your views here.


from django.shortcuts import render
from django.http import JsonResponse
import subprocess
import os
import threading


def ejecutar_script(username, password):
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'BOTATS.py')
    python_executable = os.path.join(os.path.dirname(__file__), '..', '..', 'venv', 'Scripts', 'python.exe')
    print(os.path.join(os.path.dirname(__file__)))
    try:
        result = subprocess.run([python_executable, script_path, username, password], capture_output=True, text=True)
        if result.returncode == 0:
            print("Script ejecutado con éxito")
            print("Salida:", result.stdout)
        else:
            print("Error al ejecutar el script")
            print("Error:", result.stderr)
    except Exception as e:
        print("Excepción al intentar ejecutar el script:", str(e))

def ejecutar_script_botemitidos(username, password):
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'BOTEMITIDOS.py')
    python_executable = os.path.join(os.path.dirname(__file__), '..', 'venv', 'Scripts', 'python.exe')

    try:
        result = subprocess.run([python_executable, script_path, username, password], capture_output=True, text=True)
        if result.returncode == 0:
            print("Script ejecutado con éxito")
            print("Salida:", result.stdout)
        else:
            print("Error al ejecutar el script")
            print("Error:", result.stderr)
    except Exception as e:
        print("Excepción al intentar ejecutar el script:", str(e))


def ejecutar_script_reporterecibidos():
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'ReporteRecibidos.py')
    python_executable = os.path.join(os.path.dirname(__file__), '..', 'venv', 'Scripts', 'python.exe')
    result_message = ""

    try:
        result = subprocess.run([python_executable, script_path], capture_output=True, text=True, encoding='utf-8')
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

def ejecutar_script_reporteemitidos():
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'ReporteEmitidos.py')
    python_executable = os.path.join(os.path.dirname(__file__), '..', 'venv', 'Scripts', 'python.exe')
    result_message = ""

    try:
        result = subprocess.run([python_executable, script_path], capture_output=True, text=True, encoding='utf-8')
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


def go_view_generatoXML(request):
    return render(request, 'view_generator.html')


def crearats(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        username = request.POST.get('username')
        password = request.POST.get('password')


        result_message = ""

        if action == 'BOTATS':
            thread = threading.Thread(target=ejecutar_script, args=(username, password))
            thread.start()
            result_message = "El script se está ejecutando en segundo plano"
        elif action == 'BOTEMITIDOS':
            thread = threading.Thread(target=ejecutar_script_botemitidos, args=(username, password))
            thread.start()
            result_message = "El script se está ejecutando en segundo plano"
        elif action == 'ReporteRecibidos':
            result_message = ejecutar_script_reporterecibidos()
        elif action == 'ReporteEmitidos':
            result_message = ejecutar_script_reporteemitidos()

        return JsonResponse({'output': result_message})

    return render(request, 'crearats.html')



def check_xml_files(request):
    if request.method == 'POST':
        button_id = request.POST.get('button_id')
        directory = os.path.join('C:\\', 'ia', 'SRIBOT', 'XML', 'RECIBIDAS', button_id)

        # Imprimir el directorio para verificar que es correcto
        print(f"Directorio a verificar: {directory}")

        # Ruta al script y al intérprete Python
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'comprobantesrecibidos.py')
        python_executable = 'python'  # Cambia esto a la ruta de tu intérprete Python si es necesario

        try:
            result = subprocess.run([python_executable, script_path, directory], capture_output=True, text=True)
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
        directory = os.path.join('C:\\', 'ia', 'SRIBOT', 'XML', 'EMITIDAS', button_id)

        # Imprimir el directorio para verificar que es correcto
        print(f"Directorio a verificar: {directory}")

        # Ruta al script y al intérprete Python
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'comprobantesemitidos.py')
        python_executable = 'python'  # Cambia esto a la ruta de tu intérprete Python si es necesario

        try:
            result = subprocess.run([python_executable, script_path, directory], capture_output=True, text=True)
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