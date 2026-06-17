import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

import customtkinter as ctk
from PIL import Image as PILImage
from PIL import ImageTk

# Librería para el Calendario Visual
from tkcalendar import Calendar

# ReportLab para la ficha PDF Premium
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Table, TableStyle
from reportlab.platypus import Image as RLImage
from reportlab.lib import colors

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DB = "database/inmobiliaria.db"

# Asegurar directorios de trabajo
os.makedirs("database", exist_ok=True)
os.makedirs("fotos", exist_ok=True)
os.makedirs("pdfs", exist_ok=True)

# Variables de control para ventanas únicas y widgets globales
ventana_inventario = None
ventana_cartera = None
combo_asesor_inm = None
combo_asesor_cli = None

# --------------------------------------------------------
# BASE DE DATOS: INICIALIZACIÓN COMPLETA
# --------------------------------------------------------
def inicializar_bd():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asesores (
                id_asesor INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                telefono TEXT,
                correo TEXT,
                activo INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inmuebles (
                id_inmueble INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_operacion TEXT,
                tipo_inmueble TEXT,
                titulo TEXT,
                precio REAL,
                colonia TEXT,
                municipio TEXT,
                estado TEXT,
                descripcion TEXT,
                m2_terreno REAL,
                m2_construccion REAL,
                id_asesor INTEGER,
                eliminado INTEGER DEFAULT 0,
                FOREIGN KEY(id_asesor) REFERENCES asesores(id_asesor)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fotos_inmueble (
                id_foto INTEGER PRIMARY KEY AUTOINCREMENT,
                id_inmueble INTEGER,
                ruta_archivo TEXT,
                descripcion TEXT,
                principal INTEGER,
                FOREIGN KEY(id_inmueble) REFERENCES inmuebles(id_inmueble)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                telefono TEXT,
                correo TEXT,
                presupuesto_max REAL,
                zona_interes TEXT,
                tipo_buscado TEXT,
                operacion_buscada TEXT DEFAULT 'VENTA',
                m2_minimos REAL DEFAULT 0.0,
                id_asesor INTEGER,
                FOREIGN KEY(id_asesor) REFERENCES asesores(id_asesor)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id_cita INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER,
                id_inmueble INTEGER,
                fecha TEXT,
                hora TEXT,
                notas TEXT,
                FOREIGN KEY(id_cliente) REFERENCES clientes(id_cliente),
                FOREIGN KEY(id_inmueble) REFERENCES inmuebles(id_inmueble)
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM asesores")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO asesores (nombre, telefono, correo, activo) VALUES ('Asesor General', '5500000000', 'general@garanzia.com', 1)")
        
        conn.commit()

inicializar_bd()

# --------------------------------------------------------
# FUNCIONES DE UTILIDAD (DROPDOWNS Y ASESORES)
# --------------------------------------------------------
def obtener_lista_asesores():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM asesores WHERE activo = 1")
        return [row[0] for row in cursor.fetchall()]

def obtener_lista_clientes_combo():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_cliente, nombre FROM clientes")
        return [f"{row[0]} - {row[1]}" for row in cursor.fetchall()]

def obtener_lista_inmuebles_combo():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_inmueble, titulo FROM inmuebles WHERE eliminado = 0")
        return [f"{row[0]} - {row[1]}" for row in cursor.fetchall()]

def actualizar_combos_asesores():
    lista = obtener_lista_asesores()
    if combo_asesor_inm and combo_asesor_inm.winfo_exists():
        combo_asesor_inm.configure(values=lista)
        combo_asesor_inm.set(lista[0] if lista else "Seleccionar Asesor...")
    if combo_asesor_cli and combo_asesor_cli.winfo_exists():
        combo_asesor_cli.configure(values=lista)
        combo_asesor_cli.set(lista[0] if lista else "Seleccionar Asesor...")

def obtener_id_asesor_por_nombre(nombre_asesor):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_asesor FROM asesores WHERE nombre = ?", (nombre_asesor,))
        res = cursor.fetchone()
        return res[0] if res else 1

# --------------------------------------------------------
# LÓGICA DE CRUCE / MATCH AUTOMÁTICO
# --------------------------------------------------------
def calcular_y_mostrar_match(tipo_buscado, presupuesto_max, zona_interes, nombre_cliente):
    ventana_match = ctk.CTkToplevel(app)
    ventana_match.title(f"Coincidencias de Inventario para: {nombre_cliente}")
    ventana_match.geometry("900x450")
    ventana_match.after(100, lambda: ventana_match.focus())

    ctk.CTkLabel(ventana_match, text=f"Propiedades encontradas para {nombre_cliente}", font=("Arial", 16, "bold"), text_color="#1A237E").pack(pady=10)
    ctk.CTkLabel(ventana_match, text=f"Criterio: {tipo_buscado} | Presupuesto Máx: ${presupuesto_max:,.2f} | Zona: {zona_interes}", font=("Arial", 11, "italic")).pack(pady=2)

    frame_tabla_match = ctk.CTkFrame(ventana_match)
    frame_tabla_match.pack(fill="both", expand=True, padx=15, pady=15)

    columnas = ("ID", "OPERACIÓN", "TIPO", "TÍTULO", "PRECIO", "COLONIA", "MUNICIPIO")
    tree_match = ttk.Treeview(frame_tabla_match, columns=columnas, show="headings")
    for col in columnas: 
        tree_match.heading(col, text=col)
        tree_match.column(col, width=110, anchor="center")
    tree_match.pack(side="left", fill="both", expand=True)

    zona_query = f"%{zona_interes.strip()}%"
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_inmueble, tipo_operacion, tipo_inmueble, titulo, precio, colonia, municipio 
            FROM inmuebles 
            WHERE eliminado = 0 
              AND LOWER(tipo_inmueble) = LOWER(?) 
              AND precio <= ? 
              AND (LOWER(colonia) LIKE LOWER(?) OR LOWER(municipio) LIKE LOWER(?))
        """, (tipo_buscado, presupuesto_max, zona_query, zona_query))
        
        filas = cursor.fetchall()
        for r in filas: 
            tree_match.insert("", "end", values=r)

    if not filas:
        messagebox.showinfo("Sin Coincidencias", "No se encontraron propiedades en inventario que cumplan todos los filtros de este cliente por el momento.", parent=ventana_match)

# --------------------------------------------------------
# VENTANA PRINCIPAL Y CONFIGURACIÓN DE NAVEGACIÓN
# --------------------------------------------------------
app = ctk.CTk()
app.title("CRM Inmobiliario Garanzia v2.8")
app.geometry("1350x850")

frame_dashboard = ctk.CTkFrame(app, corner_radius=0, fg_color="#F5F5F5")
frame_alta_inmuebles = ctk.CTkFrame(app, corner_radius=0, fg_color="transparent")
frame_alta_clientes = ctk.CTkFrame(app, corner_radius=0, fg_color="transparent")
frame_agenda = ctk.CTkFrame(app, corner_radius=0, fg_color="#F5F5F5") 
frame_asesores = ctk.CTkFrame(app, corner_radius=0, fg_color="#F5F5F5")
frame_papelera = ctk.CTkFrame(app, corner_radius=0, fg_color="#F5F5F5")

def cambiar_vista(vista_destino):
    frame_dashboard.pack_forget()
    frame_alta_inmuebles.pack_forget()
    frame_alta_clientes.pack_forget()
    frame_agenda.pack_forget()
    frame_asesores.pack_forget()
    frame_papelera.pack_forget()
    
    if vista_destino == frame_dashboard:
        actualizar_metricas_dashboard()
    elif vista_destino in (frame_alta_inmuebles, frame_alta_clientes):
        actualizar_combos_asesores()
    elif vista_destino == frame_agenda:
        actualizar_componentes_agenda()
    elif vista_destino == frame_asesores:
        actualizar_tabla_asesores()
    elif vista_destino == frame_papelera:
        actualizar_tabla_papelera()
        
    vista_destino.pack(side="right", fill="both", expand=True)

# Menú Lateral Fijo
menu = ctk.CTkFrame(app, width=240, corner_radius=0, fg_color="#1A237E")
menu.pack(side="left", fill="y")

ctk.CTkLabel(menu, text="GARANZIA", font=("Arial", 24, "bold"), text_color="white").pack(pady=(30, 2))
ctk.CTkLabel(menu, text="CRM INMOBILIARIO", font=("Arial", 11, "italic"), text_color="#B0BEC5").pack(pady=(0, 35))

estilo_btn = {"fg_color": "transparent", "text_color": "white", "hover_color": "#283593", "anchor": "w", "height": 40}

ctk.CTkButton(menu, text="📊 Dashboard / Inicio", command=lambda: cambiar_vista(frame_dashboard), **estilo_btn).pack(fill="x", padx=15, pady=3)
ctk.CTkButton(menu, text="🏠 Alta de Inmuebles", command=lambda: cambiar_vista(frame_alta_inmuebles), **estilo_btn).pack(fill="x", padx=15, pady=3)
ctk.CTkButton(menu, text="📂 Ver Inventario", command=lambda: mostrar_inmuebles(), **estilo_btn).pack(fill="x", padx=15, pady=3)
ctk.CTkButton(menu, text="👤 Registrar Cliente", command=lambda: cambiar_vista(frame_alta_clientes), **estilo_btn).pack(fill="x", padx=15, pady=3)
ctk.CTkButton(menu, text="👥 Cartera de Clientes", command=lambda: mostrar_clientes(), **estilo_btn).pack(fill="x", padx=15, pady=3)
ctk.CTkButton(menu, text="📅 Agenda de Citas", command=lambda: cambiar_vista(frame_agenda), **estilo_btn).pack(fill="x", padx=15, pady=3)
ctk.CTkButton(menu, text="💼 Administrar Asesores", command=lambda: cambiar_vista(frame_asesores), **estilo_btn).pack(fill="x", padx=15, pady=3)
ctk.CTkButton(menu, text="🗑️ Papelera de Reciclaje", command=lambda: cambiar_vista(frame_papelera), **estilo_btn).pack(fill="x", padx=15, pady=3)

# --------------------------------------------------------
# VISTA: DASHBOARD PANELS
# --------------------------------------------------------
contenedor_tarjetas = ctk.CTkFrame(frame_dashboard, fg_color="transparent")
contenedor_tarjetas.pack(fill="x", padx=30, pady=10)

def crear_tarjeta_kpi(master, titulo, color_borde):
    f = ctk.CTkFrame(master, width=280, height=120, corner_radius=10, border_width=2, border_color=color_borde, fg_color="white")
    f.pack_propagate(False)
    f.pack(side="left", padx=10)
    ctk.CTkLabel(f, text=titulo, font=("Arial", 12, "bold"), text_color="gray").pack(pady=(15, 2))
    lbl_val = ctk.CTkLabel(f, text="0", font=("Arial", 18, "bold"), text_color="black")
    lbl_val.pack()
    return lbl_val

ctk.CTkLabel(frame_dashboard, text="Panel de Control General", font=("Arial", 28, "bold"), text_color="#1A237E").pack(pady=(25, 20), padx=30, anchor="w")
lbl_kpi_inmuebles = crear_tarjeta_kpi(contenedor_tarjetas, "PROPIEDADES EN INVENTARIO", "#1E88E5")
lbl_kpi_clientes = crear_tarjeta_kpi(contenedor_tarjetas, "CLIENTES ACTIVOS", "#43A047")
lbl_kpi_valor = crear_tarjeta_kpi(contenedor_tarjetas, "VALOR ACTIVO DEL PORTAFOLIO", "#E65100")

contenedor_detalles = ctk.CTkFrame(frame_dashboard, fg_color="white", corner_radius=10)
contenedor_detalles.pack(fill="both", expand=True, padx=40, pady=25)

lbl_sub_promedio = ctk.CTkLabel(contenedor_detalles, text="📊 Valor Promedio: $0.00", font=("Arial", 14), text_color="black")
lbl_sub_promedio.pack(pady=5, padx=20, anchor="w")
lbl_sub_citas = ctk.CTkLabel(contenedor_detalles, text="📅 Agenda: 0 hoy", font=("Arial", 14), text_color="black")
lbl_sub_citas.pack(pady=5, padx=20, anchor="w")

def actualizar_metricas_dashboard():
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inmuebles WHERE eliminado = 0")
        total_inm = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_cli = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(precio) FROM inmuebles WHERE eliminado = 0")
        valor_portafolio = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT AVG(precio) FROM inmuebles WHERE eliminado = 0")
        promedio_prop = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT COUNT(*) FROM citas WHERE fecha = ?", (hoy_str,))
        citas_hoy = cursor.fetchone()[0]

        lbl_kpi_inmuebles.configure(text=f"Total: {total_inm}")
        lbl_kpi_clientes.configure(text=str(total_cli))
        lbl_kpi_valor.configure(text=f"${valor_portafolio:,.2f}")
        lbl_sub_promedio.configure(text=f"📊 Valor Promedio de Propiedad: ${promedio_prop:,.2f}")
        lbl_sub_citas.configure(text=f"📅 Agenda: {citas_hoy} citas agendadas para hoy")

# --------------------------------------------------------
# VISTA: ALTA DE INMUEBLES
# --------------------------------------------------------
def guardar_inmueble():
    if not txt_titulo.get().strip() or not txt_precio.get().strip():
        messagebox.showwarning("Campos incompletos", "Título y Precio son obligatorios.")
        return
    try:
        precio = float(txt_precio.get().replace(",", "").replace("$", "").strip())
        m2_t = float(txt_m2_terreno.get().strip()) if txt_m2_terreno.get() else 0.0
        m2_c = float(txt_m2_construccion.get().strip()) if txt_m2_construccion.get() else 0.0
    except ValueError:
        messagebox.showerror("Error", "Inserta valores numéricos válidos.")
        return

    id_ase = obtener_id_asesor_por_nombre(combo_asesor_inm.get())
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inmuebles (tipo_operacion, tipo_inmueble, titulo, precio, colonia, municipio, estado, descripcion, m2_terreno, m2_construccion, id_asesor, eliminado)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,0)
        """, (combo_operacion.get(), combo_tipo.get(), txt_titulo.get().strip(), precio, txt_colonia.get().strip(), txt_municipio.get().strip(), txt_estado.get().strip(), txt_descripcion.get().strip(), m2_t, m2_c, id_ase))
        conn.commit()
    messagebox.showinfo("Éxito", "Inmueble añadido exitosamente.")
    limpiar_inmueble()

def limpiar_inmueble():
    txt_titulo.delete(0, 'end'); txt_precio.delete(0, 'end'); txt_colonia.delete(0, 'end')
    txt_municipio.delete(0, 'end'); txt_estado.delete(0, 'end'); txt_descripcion.delete(0, 'end')
    txt_m2_terreno.delete(0, 'end'); txt_m2_construccion.delete(0, 'end')

ctk.CTkLabel(frame_alta_inmuebles, text="Alta de Inmuebles", font=("Arial", 26, "bold")).pack(pady=15)
combo_operacion = ctk.CTkComboBox(frame_alta_inmuebles, values=["VENTA", "RENTA"], width=400); combo_operacion.pack(pady=4)
combo_tipo = ctk.CTkComboBox(frame_alta_inmuebles, values=["Casa", "Departamento", "Terreno", "Local", "Oficina"], width=400); combo_tipo.pack(pady=4)
txt_titulo = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Título Comercial"); txt_titulo.pack(pady=4)
txt_precio = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Precio Venta/Renta"); txt_precio.pack(pady=4)
txt_colonia = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Colonia"); txt_colonia.pack(pady=4)
txt_municipio = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Municipio / Alcaldía"); txt_municipio.pack(pady=4)
txt_estado = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Estado"); txt_estado.pack(pady=4)
txt_descripcion = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Descripción o Notas Internas"); txt_descripcion.pack(pady=4)
txt_m2_terreno = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="M2 Terreno"); txt_m2_terreno.pack(pady=4)
txt_m2_construccion = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="M2 Construcción"); txt_m2_construccion.pack(pady=4)
combo_asesor_inm = ctk.CTkComboBox(frame_alta_inmuebles, values=[], width=400); combo_asesor_inm.pack(pady=4)

ctk.CTkButton(frame_alta_inmuebles, text="💾 Guardar Inmueble", command=guardar_inmueble, fg_color="#1E88E5").pack(pady=15)

# --------------------------------------------------------
# VISTA: REGISTRAR CLIENTES
# --------------------------------------------------------
def guardar_cliente():
    nombre_cli = txt_nombre_cli.get().strip()
    zona_cli = txt_zona_cli.get().strip()
    tipo_interes = combo_tipo_buscado.get()

    if not nombre_cli:
        messagebox.showwarning("Campos vacíos", "El nombre del cliente es obligatorio.")
        return
    try:
        presupuesto = float(txt_presupuesto.get().replace(",", "").replace("$", "").strip()) if txt_presupuesto.get() else 0.0
    except ValueError:
        messagebox.showerror("Error", "Por favor ingresa un presupuesto numérico válido.")
        return

    id_ase = obtener_id_asesor_por_nombre(combo_asesor_cli.get())
    
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clientes (nombre, telefono, correo, presupuesto_max, zona_interes, tipo_buscado, operacion_buscada, id_asesor)
            VALUES (?, ?, ?, ?, ?, ?, 'VENTA', ?)
        """, (nombre_cli, txt_tel_cli.get().strip(), txt_correo_cli.get().strip(), presupuesto, zona_cli, tipo_interes, id_ase))
        conn.commit()
        
    messagebox.showinfo("Éxito", f"¡Cliente registrado con éxito!\nIniciando cruce automático de requerimientos...")
    calcular_y_mostrar_match(tipo_interes, presupuesto, zona_cli, nombre_cli)
    limpiar_cliente()

def limpiar_cliente():
    txt_nombre_cli.delete(0, 'end'); txt_tel_cli.delete(0, 'end'); txt_correo_cli.delete(0, 'end')
    txt_presupuesto.delete(0, 'end'); txt_zona_cli.delete(0, 'end')

ctk.CTkLabel(frame_alta_clientes, text="Registro de Nuevos Prospectos", font=("Arial", 26, "bold")).pack(pady=20)
txt_nombre_cli = ctk.CTkEntry(frame_alta_clientes, width=400, placeholder_text="Nombre del Lead"); txt_nombre_cli.pack(pady=5)
txt_tel_cli = ctk.CTkEntry(frame_alta_clientes, width=400, placeholder_text="Teléfono Celular"); txt_tel_cli.pack(pady=5)
txt_correo_cli = ctk.CTkEntry(frame_alta_clientes, width=400, placeholder_text="Correo Electrónico"); txt_correo_cli.pack(pady=5)
txt_presupuesto = ctk.CTkEntry(frame_alta_clientes, width=400, placeholder_text="Presupuesto Máximo de Compra"); txt_presupuesto.pack(pady=5)
txt_zona_cli = ctk.CTkEntry(frame_alta_clientes, width=400, placeholder_text="Zonas de interés"); txt_zona_cli.pack(pady=5)
combo_tipo_buscado = ctk.CTkComboBox(frame_alta_clientes, values=["Casa", "Departamento", "Terreno", "Local", "Oficina"], width=400); combo_tipo_buscado.pack(pady=5)
combo_asesor_cli = ctk.CTkComboBox(frame_alta_clientes, values=[], width=400); combo_asesor_cli.pack(pady=5)

ctk.CTkButton(frame_alta_clientes, text="👥 Registrar Cliente", command=guardar_cliente, fg_color="#2E7D32").pack(pady=15)

# --------------------------------------------------------
# VISTA: CARTERA DE CLIENTES
# --------------------------------------------------------
def mostrar_clientes():
    global ventana_cartera
    if ventana_cartera is not None and ventana_cartera.winfo_exists():
        ventana_cartera.focus()
        return

    ventana_cartera = ctk.CTkToplevel(app)
    ventana_cartera.title("Cartera de Clientes Activos")
    ventana_cartera.geometry("1050x580")
    ventana_cartera.after(100, lambda: ventana_cartera.focus())

    frame_acciones_cli = ctk.CTkFrame(ventana_cartera)
    frame_acciones_cli.pack(fill="x", padx=15, pady=10)

    frame_t = ctk.CTkFrame(ventana_cartera)
    frame_t.pack(fill="both", expand=True, padx=15, pady=5)

    columnas = ("ID", "NOMBRE", "TELEFONO", "CORREO", "PRESUPUESTO", "ZONA", "TIPO BUSCADO")
    tree = ttk.Treeview(frame_t, columns=columnas, show="headings")
    for col in columnas: 
        tree.heading(col, text=col)
        tree.column(col, anchor="center")
    tree.pack(side="left", fill="both", expand=True)

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_cliente, nombre, telefono, correo, presupuesto_max, zona_interes, tipo_buscado FROM clientes")
        for r in cursor.fetchall(): tree.insert("", "end", values=r)

    def ejecutar_match_desde_tabla():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Selección vacía", "Por favor, selecciona un cliente de la lista para ver sus propiedades cruzadas.")
            return
        
        datos = tree.item(sel[0], "values")
        nombre = datos[1]
        try: presupuesto = float(datos[4])
        except: presupuesto = 0.0
        zona = datos[5]
        tipo = datos[6]

        calcular_y_mostrar_match(tipo, presupuesto, zona, nombre)

    ctk.CTkButton(frame_acciones_cli, text="⚡ Encontrar Inmuebles (Auto-Match)", fg_color="#E65100", command=ejecutar_match_desde_tabla).pack(side="left", padx=5)

# --------------------------------------------------------
# VISTA: AGENDA DE CITAS
# --------------------------------------------------------
def agendar_cita():
    cli_sel = combo_agenda_cliente.get()
    inm_sel = combo_agenda_inmueble.get()
    if " - " not in cli_sel or " - " not in inm_sel:
        messagebox.showwarning("Error", "Selecciona un cliente e inmueble válidos.")
        return
    
    id_c = cli_sel.split(" - ")[0]
    id_i = inm_sel.split(" - ")[0]
    fecha_sel = calendario.get_date()
    hora_sel = f"{combo_hora.get()}:{combo_minuto.get()}"
    
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO citas (id_cliente, id_inmueble, fecha, hora, notas) VALUES (?,?,?,?,?)",
                       (id_c, id_i, fecha_sel, hora_sel, txt_notas_cita.get().strip()))
        conn.commit()
    messagebox.showinfo("Éxito", "Cita agendada correctamente.")
    actualizar_componentes_agenda()

def eliminar_cita():
    seleccion = tree_agenda.selection()
    if not seleccion:
        messagebox.showwarning("Selección vacía", "Por favor, selecciona una cita de la tabla inferior para poder eliminarla.")
        return
    
    datos_cita = tree_agenda.item(seleccion[0], "values")
    id_cita = datos_cita[0]
    cliente_nom = datos_cita[1]
    
    if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas cancelar y eliminar permanentemente la cita de {cliente_nom}?"):
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM citas WHERE id_cita = ?", (id_cita,))
            conn.commit()
        messagebox.showinfo("Eliminado", "La cita ha sido removida de la agenda.")
        actualizar_componentes_agenda()

def actualizar_componentes_agenda():
    combo_agenda_cliente.configure(values=obtener_lista_clientes_combo())
    combo_agenda_inmueble.configure(values=obtener_lista_inmuebles_combo())
    
    for item in tree_agenda.get_children(): tree_agenda.delete(item)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id_cita, cl.nombre, i.titulo, c.fecha, c.hora 
            FROM citas c
            JOIN clientes cl ON c.id_cliente = cl.id_cliente
            JOIN inmuebles i ON c.id_inmueble = i.id_inmueble
            ORDER BY c.fecha ASC, c.hora ASC
        """)
        for r in cursor.fetchall(): tree_agenda.insert("", "end", values=r)

ctk.CTkLabel(frame_agenda, text="Calendario y Agenda de Citas", font=("Arial", 24, "bold"), text_color="#1A237E").pack(pady=(20, 10), padx=30, anchor="w")

frame_modulo_agenda = ctk.CTkFrame(frame_agenda, fg_color="transparent")
frame_modulo_agenda.pack(fill="x", padx=30, pady=10)

frame_calendario_izq = ctk.CTkFrame(frame_modulo_agenda, fg_color="white", corner_radius=10)
frame_calendario_izq.pack(side="left", fill="y", padx=(0, 15))


# --- CONFIGURACIÓN DE CONTRASSTE DE ESTILOS DEL MOTOR GRÁFICO (TTK) ---
# Esto obliga al sistema a pintar las fuentes del calendario en colores visibles.
estilo_ttk = ttk.Style()
estilo_ttk.theme_use('clam')  # Forzar tema nativo limpio para evitar bloqueos de CustomTkinter

# Configura los días activos dentro de la cuadrícula seleccionada
estilo_ttk.configure('custom.Calendar.ttk', background='#1A237E', foreground='white')
estilo_ttk.map('custom.Calendar.ttk',
    foreground=[('selected', '#FFFFFF'), ('active', '#1A237E')],
    background=[('selected', '#1E88E5'), ('active', '#E8EAF6')]
)

# Inicialización del objeto Calendario con redefiniciones estrictas de color
calendario = Calendar(
    frame_calendario_izq, 
    selectmode='day', 
    date_pattern='yyyy-mm-dd', 
    style='custom.Calendar.ttk',     # Pasar el mapeo limpio corregido
    background='#808080',            # Barra superior (Fondo)
    foreground='#FFFFFF',            # Texto de la barra superior (Mes y Año en BLANCO)
    headersbackground='#1A237E',     # Fondo de la barra de días de la semana
    headersforeground='#FFFFFF',     # Letras de los días L M M J V S D (En BLANCO)
    normalbackground='#FFFFFF',      # Fondo del cuerpo de días
    normalforeground='#111111',      # Números de los días (Negro/Gris oscuro nítido)
    weekendbackground='#F5F5F5',     # Fines de semana
    weekendforeground='#D32F2F',     # Sábados y domingos (Rojo oscuro nítido)
    selectbackground='#1E88E5',      # Fondo del día seleccionado (Azul claro)
    selectforeground='#FFFFFF',      # TEXTO DEL NÚMERO SELECCIONADO (Fijado en BLANCO)
    tooltipalpha=0.0
)
calendario.pack(padx=15, pady=15)


frame_form_der = ctk.CTkFrame(frame_modulo_agenda, corner_radius=10, fg_color="white")
frame_form_der.pack(side="left", fill="both", expand=True)

ctk.CTkLabel(frame_form_der, text="Agendar Nueva Cita", font=("Arial", 14, "bold"), text_color="black").pack(anchor="w", pady=(15, 10), padx=15)

combo_agenda_cliente = ctk.CTkComboBox(frame_form_der, width=350, values=[])
combo_agenda_cliente.pack(pady=5, padx=15, anchor="w")
combo_agenda_cliente.set("Seleccionar Cliente Prospecto...")

combo_agenda_inmueble = ctk.CTkComboBox(frame_form_der, width=350, values=[])
combo_agenda_inmueble.pack(pady=5, padx=15, anchor="w")
combo_agenda_inmueble.set("Seleccionar Propiedad de Interés...")

frame_hora_linea = ctk.CTkFrame(frame_form_der, fg_color="transparent")
frame_hora_linea.pack(pady=5, padx=15, anchor="w")
ctk.CTkLabel(frame_hora_linea, text="Hora de la Cita: ", text_color="black").pack(side="left", padx=(0, 5))

combo_hora = ctk.CTkComboBox(frame_hora_linea, width=80, values=[f"{i:02d}" for i in range(8, 21)])
combo_hora.pack(side="left", padx=2)
combo_minuto = ctk.CTkComboBox(frame_hora_linea, width=80, values=["00", "15", "30", "45"])
combo_minuto.pack(side="left", padx=2)

txt_notas_cita = ctk.CTkEntry(frame_form_der, width=350, placeholder_text="Objetivo de la visita (Ej: Cierre, Segunda muestra)")
txt_notas_cita.pack(pady=10, padx=15, anchor="w")

ctk.CTkButton(frame_form_der, text="📅 Confirmar y Registrar Cita", fg_color="#1A237E", hover_color="#283593", command=agendar_cita).pack(pady=(5, 15), padx=15, anchor="w")

# Panel inferior de visualización de agenda y botones de acción
frame_lista_agenda = ctk.CTkFrame(frame_agenda, fg_color="transparent")
frame_lista_agenda.pack(fill="both", expand=True, padx=30, pady=(10, 20))

ctk.CTkLabel(frame_lista_agenda, text="📋 Próximas Citas en Agenda", font=("Arial", 14, "bold"), text_color="black").pack(anchor="w", pady=(0, 5))

tree_agenda = ttk.Treeview(frame_lista_agenda, columns=("ID", "CLIENTE", "PROPIEDAD", "FECHA", "HORA"), show="headings")
for col in ("ID", "CLIENTE", "PROPIEDAD", "FECHA", "HORA"): 
    tree_agenda.heading(col, text=col)
    tree_agenda.column(col, anchor="center")
tree_agenda.pack(fill="both", expand=True, pady=(0, 10))

# BOTÓN DE ACCIÓN: ELIMINAR CITA SELECCIONADA
ctk.CTkButton(frame_lista_agenda, text="❌ Eliminar Cita Seleccionada", fg_color="#D32F2F", hover_color="#C62828", command=eliminar_cita).pack(anchor="w")

# --------------------------------------------------------
# VISTA: ADMINISTRACIÓN DE ASESORES
# --------------------------------------------------------
def guardar_asesor():
    if not txt_nom_as.get().strip(): return
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO asesores (nombre, telefono, correo, activo) VALUES (?,?,?,1)",
                       (txt_nom_as.get().strip(), txt_tel_as.get().strip(), txt_cor_as.get().strip()))
        conn.commit()
    txt_nom_as.delete(0, 'end'); txt_tel_as.delete(0, 'end'); txt_cor_as.delete(0, 'end')
    actualizar_tabla_asesores()

def borrar_asesor_seleccionado():
    seleccion = tree_asesores.selection()
    if not seleccion:
        messagebox.showwarning("Selección vacía", "Por favor, selecciona un asesor de la lista para poder eliminarlo.")
        return
    
    datos_asesor = tree_asesores.item(seleccion[0], "values")
    id_asesor = datos_asesor[0]
    nombre_asesor = datos_asesor[1]
    
    if int(id_asesor) == 1:
        messagebox.showerror("Error", "El 'Asesor General' es el sistema por defecto y no puede ser eliminado.")
        return
        
    if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas dar de baja a {nombre_asesor}?\n\nNota: Sus clientes e inmuebles serán reasignados al Asesor General."):
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            # 1. Reasignar inmuebles de este asesor al Asesor General (ID 1)
            cursor.execute("UPDATE inmuebles SET id_asesor = 1 WHERE id_asesor = ?", (id_asesor,))
            # 2. Reasignar clientes de este asesor al Asesor General (ID 1)
            cursor.execute("UPDATE clientes SET id_asesor = 1 WHERE id_asesor = ?", (id_asesor,))
            # 3. Desactivar lógicamente al asesor
            cursor.execute("UPDATE asesores SET activo = 0 WHERE id_asesor = ?", (id_asesor,))
            conn.commit()
            
        messagebox.showinfo("Baja Exitosa", f"El asesor {nombre_asesor} ha sido dado de baja y sus cuentas transferidas.")
        actualizar_tabla_asesores()

def actualizar_tabla_asesores():
    for item in tree_asesores.get_children(): tree_asesores.delete(item)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_asesor, nombre, telefono, correo FROM asesores WHERE activo = 1")
        for r in cursor.fetchall(): tree_asesores.insert("", "end", values=r)

ctk.CTkLabel(frame_asesores, text="Administración de Fuerza de Ventas", font=("Arial", 24, "bold")).pack(pady=10)
frame_form_as = ctk.CTkFrame(frame_asesores)
frame_form_as.pack(fill="x", padx=20, pady=10)

txt_nom_as = ctk.CTkEntry(frame_form_as, placeholder_text="Nombre Completo"); txt_nom_as.pack(side="left", padx=5, pady=10, expand=True, fill="x")
txt_tel_as = ctk.CTkEntry(frame_form_as, placeholder_text="Teléfono"); txt_tel_as.pack(side="left", padx=5, pady=10, expand=True, fill="x")
txt_cor_as = ctk.CTkEntry(frame_form_as, placeholder_text="Correo Electrónico"); txt_cor_as.pack(side="left", padx=5, pady=10, expand=True, fill="x")
ctk.CTkButton(frame_form_as, text="➕ Añadir Asesor", fg_color="#2E7D32", command=guardar_asesor).pack(side="left", padx=10)

tree_asesores = ttk.Treeview(frame_asesores, columns=("ID", "NOMBRE", "TELEFONO", "CORREO"), show="headings")
for col in ("ID", "NOMBRE", "TELEFONO", "CORREO"): tree_asesores.heading(col, text=col)
tree_asesores.pack(fill="both", expand=True, padx=20, pady=10)

# BOTÓN DE ACCIÓN AGREGADO: BORRAR ASESOR SELECCIONADO
ctk.CTkButton(frame_asesores, text="❌ Dar de Baja Asesor Seleccionado", fg_color="#D32F2F", hover_color="#C62828", command=borrar_asesor_seleccionado).pack(anchor="w", padx=20, pady=(0, 20))

# --------------------------------------------------------
# VISTA: PAPELERA DE RECICLAJE
# --------------------------------------------------------
def actualizar_tabla_papelera():
    for item in tree_papelera.get_children(): tree_papelera.delete(item)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_inmueble, titulo, precio, colonia FROM inmuebles WHERE eliminado = 1")
        for r in cursor.fetchall(): tree_papelera.insert("", "end", values=r)

def restaurar_inmueble():
    sel = tree_papelera.selection()
    if not sel: return
    id_i = tree_papelera.item(sel[0], "values")[0]
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE inmuebles SET eliminado = 0 WHERE id_inmueble = ?", (id_i,))
        conn.commit()
    actualizar_tabla_papelera()
    messagebox.showinfo("Éxito", "Propiedad restaurada al inventario activo.")

ctk.CTkLabel(frame_papelera, text="Papelera de Reciclaje (Inmuebles)", font=("Arial", 24, "bold")).pack(pady=10)
ctk.CTkButton(frame_papelera, text="🔄 Restaurar Propiedad Seleccionada", fg_color="#2E7D32", command=restaurar_inmueble).pack(pady=5)

tree_papelera = ttk.Treeview(frame_papelera, columns=("ID", "TITULO", "PRECIO", "COLONIA"), show="headings")
for col in ("ID", "TITULO", "PRECIO", "COLONIA"): tree_papelera.heading(col, text=col)
tree_papelera.pack(fill="both", expand=True, padx=20, pady=15)

# --------------------------------------------------------
# VENTANA DINÁMICA: INVENTARIO ACTIVO
# --------------------------------------------------------
def mostrar_inmuebles():
    global ventana_inventario
    if ventana_inventario is not None and ventana_inventario.winfo_exists():
        ventana_inventario.focus()
        return

    ventana_inventario = ctk.CTkToplevel(app)
    ventana_inventario.title("Inventario de Inmuebles Activos")
    ventana_inventario.geometry("1150x650")
    ventana_inventario.after(100, lambda: ventana_inventario.focus())

    frame_filtros = ctk.CTkFrame(ventana_inventario)
    frame_filtros.pack(fill="x", padx=10, pady=10)

    txt_colonia_buscar = ctk.CTkEntry(frame_filtros, width=180, placeholder_text="Filtrar por Colonia")
    txt_colonia_buscar.pack(side="left", padx=5)
    txt_precio_max = ctk.CTkEntry(frame_filtros, width=150, placeholder_text="Precio Máximo")
    txt_precio_max.pack(side="left", padx=5)

    frame_tabla = ctk.CTkFrame(ventana_inventario)
    frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

    columnas = ("ID", "OPERACION", "TIPO", "TITULO", "PRECIO", "COLONIA")
    tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
    for col in columnas: tree.heading(col, text=col)
    tree.pack(side="left", fill="both", expand=True)

    def cargar_datos():
        for item in tree.get_children(): tree.delete(item)
        colonia_f = f"%{txt_colonia_buscar.get().strip()}%"
        
        try:
            raw_p = txt_precio_max.get().replace(",", "").replace("$", "").strip()
            precio_f = float(raw_p) if raw_p else 999999999.0
        except ValueError:
            precio_f = 999999999.0

        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_inmueble, tipo_operacion, tipo_inmueble, titulo, precio, colonia 
                FROM inmuebles 
                WHERE eliminado = 0 AND colonia LIKE ? AND precio <= ?
            """, (colonia_f, precio_f))
            for row in cursor.fetchall(): tree.insert("", "end", values=row)

    ctk.CTkButton(frame_filtros, text="🔍 Filtrar", command=cargar_datos, width=100).pack(side="left", padx=5)
    cargar_datos()

    def enviar_a_papelera():
        seleccion = tree.selection()
        if not seleccion: return
        id_inmueble = tree.item(seleccion[0], "values")[0]
        if messagebox.askyesno("Confirmar", f"¿Mover la propiedad #{id_inmueble} a la papelera?"):
            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE inmuebles SET eliminado = 1 WHERE id_inmueble = ?", (id_inmueble,))
                conn.commit()
            cargar_datos()

    ctk.CTkButton(frame_filtros, text="🗑️ Mover a Papelera", fg_color="#E65100", command=enviar_a_papelera).pack(side="right", padx=10)

    def editar_inmueble(event):
        seleccion = tree.selection()
        if not seleccion: return
        id_inmueble = tree.item(seleccion[0], "values")[0]

        ventana_edit = ctk.CTkToplevel(ventana_inventario)
        ventana_edit.title(f"Ficha de Edición — ID #{id_inmueble}")
        ventana_edit.geometry("500x780")
        ventana_edit.after(100, lambda: ventana_edit.focus())

        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT titulo, precio, colonia, municipio, descripcion, m2_terreno, m2_construccion, tipo_operacion, tipo_inmueble, estado FROM inmuebles WHERE id_inmueble=?", (id_inmueble,))
            reg = cursor.fetchone()

        ctk.CTkLabel(ventana_edit, text="Título Comercial").pack()
        txt_titulo_edit = ctk.CTkEntry(ventana_edit, width=380); txt_titulo_edit.pack(pady=2); txt_titulo_edit.insert(0, str(reg[0]))
        ctk.CTkLabel(ventana_edit, text="Precio").pack()
        txt_precio_edit = ctk.CTkEntry(ventana_edit, width=380); txt_precio_edit.pack(pady=2); txt_precio_edit.insert(0, str(reg[1]))
        ctk.CTkLabel(ventana_edit, text="Colonia").pack()
        txt_colonia_edit = ctk.CTkEntry(ventana_edit, width=380); txt_colonia_edit.pack(pady=2); txt_colonia_edit.insert(0, str(reg[2]))
        ctk.CTkLabel(ventana_edit, text="Municipio / Alcaldía").pack()
        txt_municipio_edit = ctk.CTkEntry(ventana_edit, width=380); txt_municipio_edit.pack(pady=2); txt_municipio_edit.insert(0, str(reg[3]))
        ctk.CTkLabel(ventana_edit, text="Descripción").pack()
        txt_desc_edit = ctk.CTkEntry(ventana_edit, width=380); txt_desc_edit.pack(pady=2); txt_desc_edit.insert(0, str(reg[4]))
        ctk.CTkLabel(ventana_edit, text="M2 Terreno").pack()
        txt_m2t_edit = ctk.CTkEntry(ventana_edit, width=380); txt_m2t_edit.pack(pady=2); txt_m2t_edit.insert(0, str(reg[5]))
        ctk.CTkLabel(ventana_edit, text="M2 Construcción").pack()
        txt_m2c_edit = ctk.CTkEntry(ventana_edit, width=380); txt_m2c_edit.pack(pady=2); txt_m2c_edit.insert(0, str(reg[6]))

        def agregar_fotos_local():
            seleccion_fotos = filedialog.askopenfilenames(title="Agregar imágenes", filetypes=[("Imágenes", "*.jpg *.jpeg *.png")])
            if not seleccion_fotos: return
            carpeta = f"fotos/inmueble_{id_inmueble}"
            os.makedirs(carpeta, exist_ok=True)
            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                for f in seleccion_fotos:
                    dest = os.path.join(carpeta, os.path.basename(f))
                    shutil.copy2(f, dest)
                    cursor.execute("INSERT INTO fotos_inmueble(id_inmueble, ruta_archivo, descripcion, principal) VALUES (?,?,?,0)", (id_inmueble, dest, ""))
                conn.commit()
            messagebox.showinfo("Éxito", "Fotos añadidas.")

        def ver_fotos():
            ventana_fotos = ctk.CTkToplevel(ventana_edit)
            ventana_fotos.title("Galería Fotográfica")
            ventana_fotos.geometry("850x600")
            
            def renderizar_galeria():
                for w in ventana_fotos.winfo_children(): w.destroy()
                scroll = ctk.CTkScrollableFrame(ventana_fotos, width=800, height=550)
                scroll.pack(fill="both", expand=True)
                
                with sqlite3.connect(DB) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id_foto, ruta_archivo, principal FROM fotos_inmueble WHERE id_inmueble=? ORDER BY principal DESC", (id_inmueble,))
                    fotos = cursor.fetchall()

                ventana_fotos.img_refs = []
                r, c = 0, 0
                for id_f, ruta, p in fotos:
                    if not os.path.exists(ruta): continue
                    try:
                        img = PILImage.open(ruta)
                        img.thumbnail((160, 120))
                        tk_img = ImageTk.PhotoImage(img)
                        ventana_fotos.img_refs.append(tk_img)
                    except: continue

                    f_marco = ctk.CTkFrame(scroll)
                    f_marco.grid(row=r, column=c, padx=10, pady=10)
                    tk.Label(f_marco, image=tk_img).pack()
                    
                    lbl_txt = "⭐ PRINCIPAL" if p == 1 else "Alternativa"
                    ctk.CTkLabel(f_marco, text=lbl_txt).pack()

                    def hacer_p(f_id=id_f):
                        with sqlite3.connect(DB) as cn:
                            cr = cn.cursor()
                            cr.execute("UPDATE fotos_inmueble SET principal=0 WHERE id_inmueble=?", (id_inmueble,))
                            cr.execute("UPDATE fotos_inmueble SET principal=1 WHERE id_foto=?", (f_id,))
                        renderizar_galeria()

                    def borrar_foto(f_id=id_f, archivo_ruta=ruta):
                        if messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar permanentemente esta fotografía de la galería?", parent=ventana_fotos):
                            try:
                                with sqlite3.connect(DB) as cn:
                                    cr = cn.cursor()
                                    cr.execute("DELETE FROM fotos_inmueble WHERE id_foto=?", (f_id,))
                                    cn.commit()
                                if os.path.exists(archivo_ruta):
                                    os.remove(archivo_ruta)
                            except Exception as e:
                                messagebox.showerror("Error", f"No se pudo eliminar el archivo físico: {e}", parent=ventana_fotos)
                            renderizar_galeria()

                    ctk.CTkButton(f_marco, text="Principal", width=120, height=24, command=hacer_p).pack(pady=2)
                    ctk.CTkButton(f_marco, text="❌ Eliminar", fg_color="#D32F2F", hover_color="#C62828", width=120, height=24, command=borrar_foto).pack(pady=2)
                    
                    c += 1
                    if c >= 4: c=0; r+=1
            renderizar_galeria()

        def generar_pdf_premium():
            archivo_pdf = f"pdfs/Ficha_Premium_{id_inmueble}.pdf"
            doc = SimpleDocTemplate(archivo_pdf, pagesize=(612, 792), rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            
            estilo_titulo = ParagraphStyle('T1', fontName='Helvetica-Bold', fontSize=24, textColor=colors.HexColor('#1A237E'), spaceAfter=15)
            estilo_sub = ParagraphStyle('T2', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#5C6BC0'), spaceAfter=15)
            estilo_normal = ParagraphStyle('N', fontName='Helvetica', fontSize=10, leading=14)
            estilo_negrita = ParagraphStyle('B', fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=colors.HexColor('#1A237E'))

            elementos = [
                Paragraph("<b>GARANZIA INMOBILIARIA</b>", estilo_titulo),
                Paragraph(f"Ficha Comercial Avanzada — ID Ref: #{id_inmueble}", estilo_sub),
                Spacer(1, 10)
            ]

            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ruta_archivo FROM fotos_inmueble WHERE id_inmueble=? ORDER BY principal DESC LIMIT 1", (id_inmueble,))
                res_f = cursor.fetchone()
            
            if res_f and os.path.exists(res_f[0]):
                try:
                    r_img = RLImage(res_f[0], width=350, height=220)
                    elementos.append(r_img)
                    elementos.append(Spacer(1, 15))
                except: pass

            datos_tabla = [
                [Paragraph("<b>Título:</b>", estilo_negrita), Paragraph(txt_titulo_edit.get(), estilo_normal)],
                [Paragraph("<b>Operación / Tipo:</b>", estilo_negrita), Paragraph(f"{reg[7]} - {reg[8]}", estilo_normal)],
                [Paragraph("<b>Precio de Lista:</b>", estilo_negrita), Paragraph(f"${float(txt_precio_edit.get()):,.2f}", estilo_normal)],
                [Paragraph("<b>Ubicación:</b>", estilo_negrita), Paragraph(f"Col. {txt_colonia_edit.get()}, {txt_municipio_edit.get()} - {reg[9]}", estilo_normal)],
                [Paragraph("<b>Terreno / Construcción:</b>", estilo_negrita), Paragraph(f"T: {txt_m2t_edit.get()}m² | C: {txt_m2c_edit.get()}m²", estilo_normal)],
                [Paragraph("<b>Descripción Completa:</b>", estilo_negrita), Paragraph(txt_desc_edit.get(), estilo_normal)]
            ]

            t = Table(datos_tabla, colWidths=[130, 400])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F9F9F9')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#C5CAE9')),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 6)
            ]))
            elementos.append(t)
            doc.build(elementos)
            messagebox.showinfo("PDF Creado", f"Guardado con éxito en: {archivo_pdf}")

        def actualizar_inmueble():
            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE inmuebles 
                    SET titulo=?, precio=?, colonia=?, municipio=?, descripcion=?, m2_terreno=?, m2_construccion=? 
                    WHERE id_inmueble=?
                """, (txt_titulo_edit.get(), float(txt_precio_edit.get()), txt_colonia_edit.get(), txt_municipio_edit.get(), txt_desc_edit.get(), float(txt_m2t_edit.get()), float(txt_m2c_edit.get()), id_inmueble))
                conn.commit()
            messagebox.showinfo("Modificado", "Datos del inmueble actualizados con éxito.")
            ventana_edit.destroy()
            cargar_datos()

        ctk.CTkButton(ventana_edit, text="➕ Cargar Fotos", command=agregar_fotos_local, fg_color="#43A047").pack(pady=3)
        ctk.CTkButton(ventana_edit, text="🖼️ Ver Galería", command=ver_fotos, fg_color="#E65100").pack(pady=3)
        ctk.CTkButton(ventana_edit, text="📄 PDF Ficha Premium", command=generar_pdf_premium, fg_color="#1A237E").pack(pady=3)
        ctk.CTkButton(ventana_edit, text="💾 Guardar Cambios", command=actualizar_inmueble, fg_color="#2E7D32").pack(pady=50)

    tree.bind("<Double-1>", editar_inmueble)

# --------------------------------------------------------
# ARRANQUE INICIAL DEL SISTEMA
# --------------------------------------------------------
cambiar_vista(frame_dashboard)
app.mainloop()
