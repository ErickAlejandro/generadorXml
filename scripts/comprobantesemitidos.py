import os
import sys

def check_xml_files(directory):
    try:
        # Listar archivos en el directorio
        files = os.listdir(directory)
        # Filtrar archivos XML
        xml_files = [f for f in files if f.endswith('.xml')]
        if len(xml_files) > 0:
            return True, xml_files
        else:
            return False, f"No se encontraron archivos XML en el directorio {directory}."
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python comprobanterecibidos.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    exists, result = check_xml_files(directory)
    if exists:
        print(f"Se encontraron {len(result)} archivos XML en el directorio {directory}.")
    else:
        print(result)
