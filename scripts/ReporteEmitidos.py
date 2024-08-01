import os
import pandas as pd
import xml.etree.ElementTree as ET
from tkinter import Tk
from tkinter.filedialog import asksaveasfilename


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
    directory_compras = r'C:\ia\SRIBOT\XML\EMITIDAS\FacturasE'
    directory_retenciones = r'C:\ia\SRIBOT\XML\EMITIDAS\RetencionesE'
    directory_notas_credito = r'C:\ia\SRIBOT\XML\EMITIDAS\NotasCreditoE'
    directory_notas_debito = r'C:\Users\DESA03\Documents\SRIBOT\XML\EMITIDAS\Notas de Débito'
    directory_liquidacion = r'C:\Users\DESA03\Documents\SRIBOT\XML\EMITIDAS\Liquidación de compra de bienes y prestación de servicios'

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

if __name__ == "__main__":
    print(main())