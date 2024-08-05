import xml.etree.ElementTree as ET
import os
from collections import defaultdict
import sys

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
    ruta_archivo_ats = os.path.join(ruta_salida, nombre_archivo)
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
ruta_carpeta_facturas_emitidas = r'C:\IA\SRIBOT\XML\EMITIDAS\FacturasE'
ruta_carpeta_facturas_recibidas = r'C:\IA\SRIBOT\XML\RECIBIDAS\Facturas'
ruta_carpeta_retenciones = r'C:\IA\SRIBOT\XML\EMITIDAS\RetencionesE'
ruta_anulados = r'C:\ia\SRIBOT\XML\ANULADOS\comprobantes_anulados.txt'


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


crear_ats(factura_emitidas_roots, factura_recibidas_roots, ruta_carpeta_retenciones, r'C:\ia\SRIBOT\XML', ruta_anulados)
print(f"Archivo ATS creado exitosamente en C:\\ia\\SRIBOT\\XML")