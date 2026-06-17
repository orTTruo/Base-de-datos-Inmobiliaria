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

# Variables de control para ventanas únicas
ventana_inventario = None
ventana_cartera = None

# ------------------------
# BASE DE DATOS: INICIALIZACIÓN COMPLETA
# ------------------------
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

# ------------------------
# FUNCIONES DE UTILIDAD PARA ASESORES Y DROPDOWNS DINÁMICOS
# ------------------------
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
    if combo_asesor_inm:
        combo_asesor_inm.configure(values=lista)
        combo_asesor_inm.set(lista[0] if lista else "Seleccionar Asesor...")
    if combo_asesor_cli:
        combo_asesor_cli.configure(values=lista)
        combo_asesor_cli.set(lista[0] if lista else "Seleccionar Asesor...")

def obtener_id_asesor_por_nombre(nombre_asesor):
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_asesor FROM asesores WHERE nombre = ?", (nombre_asesor,))
        res = cursor.fetchone()
        return res[0] if res else 1

# ------------------------
# VENTANA PRINCIPAL Y PRE-DECLARACIÓN DE FRAMES
# ------------------------
app = ctk.CTk()
app.title("CRM Inmobiliario Garanzia v2.0")
app.geometry("1350x850")

frame_dashboard = ctk.CTkFrame(app, corner_radius=0, fg_color="#F5F5F5")
frame_alta_inmuebles = ctk.CTkFrame(app, corner_radius=0, fg_color="transparent")
frame_alta_clientes = ctk.CTkFrame(app, corner_radius=0, fg_color="transparent")
frame_agenda = ctk.CTkFrame(app, corner_radius=0, fg_color="#F5F5F5") # Cambiado a gris claro para estética de agenda
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
    elif vista_destino == frame_alta_inmuebles or vista_destino == frame_alta_clientes:
        actualizar_combos_asesores()
    elif vista_destino == frame_agenda:
        actualizar_componentes_agenda()
    elif vista_destino == frame_asesores:
        actualizar_tabla_asesores()
    elif vista_destino == frame_papelera:
        actualizar_tabla_papelera()
        
    vista_destino.pack(side="right", fill="both", expand=True)

# ------------------------
# MENÚ LATERAL DE NAVEGACIÓN
# ------------------------
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
# VISTA INTERNA: DASHBOARD
# --------------------------------------------------------
frame_dashboard.pack(side="right", fill="both", expand=True)
ctk.CTkLabel(frame_dashboard, text="Panel de Control General", font=("Arial", 28, "bold"), text_color="#1A237E").pack(pady=(25, 20), padx=30, anchor="w")

contenedor_tarjetas = ctk.CTkFrame(frame_dashboard, fg_color="transparent")
contenedor_tarjetas.pack(fill="x", padx=30, pady=10)

def crear_tarjeta_kpi(master, titulo, color_borde):
    f = ctk.CTkFrame(master, width=280, height=120, corner_radius=10, border_width=2, border_color=color_borde, fg_color="white")
    f.pack_propagate(False)
    f.pack(side="left", padx=10)
    ctk.CTkLabel(f, text=titulo, font=("Arial", 12, "bold"), text_color="gray").pack(pady=(15, 2))
    lbl_val = ctk.CTkLabel(f, text="0", font=("Arial", 18, "bold"), text_color="black", justify="center")
    lbl_val.pack()
    return lbl_val

lbl_kpi_inmuebles = crear_tarjeta_kpi(contenedor_tarjetas, "PROPIEDADES EN INVENTARIO", "#1E88E5")
lbl_kpi_clientes = crear_tarjeta_kpi(contenedor_tarjetas, "CLIENTES ACTIVOS", "#43A047")
lbl_kpi_valor = crear_tarjeta_kpi(contenedor_tarjetas, "VALOR ACTIVO DEL PORTAFOLIO", "#E65100")

contenedor_detalles = ctk.CTkFrame(frame_dashboard, fg_color="white", corner_radius=10)
contenedor_detalles.pack(fill="both", expand=True, padx=40, pady=25)

ctk.CTkLabel(contenedor_detalles, text="📈 Resumen Ejecutivo Avanzado", font=("Arial", 18, "bold"), text_color="#1A237E").pack(pady=(15, 5), padx=20, anchor="w")
lbl_sub_promedio = ctk.CTkLabel(contenedor_detalles, text="📊 Valor Promedio de Propiedad: $0.00", font=("Arial", 14), text_color="black")
lbl_sub_promedio.pack(pady=5, padx=20, anchor="w")
lbl_sub_citas = ctk.CTkLabel(contenedor_detalles, text="📅 Agenda: 0 hoy | 0 esta semana", font=("Arial", 14), text_color="black")
lbl_sub_citas.pack(pady=5, padx=20, anchor="w")

ctk.CTkFrame(contenedor_detalles, height=2, fg_color="#E0E0E0").pack(fill="x", padx=20, pady=10)
lbl_kpi_asesores_lista = ctk.CTkLabel(contenedor_detalles, text="Logística de Asesores:\n Cargando datos...", font=("Arial", 14), text_color="black", justify="left")
lbl_kpi_asesores_lista.pack(pady=(5, 15), padx=20, anchor="w")

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
        cursor.execute("SELECT COUNT(*) FROM inmuebles WHERE tipo_operacion = 'VENTA' AND eliminado = 0")
        en_venta = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM inmuebles WHERE tipo_operacion = 'RENTA' AND eliminado = 0")
        en_renta = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(precio) FROM inmuebles WHERE eliminado = 0")
        promedio_prop = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT COUNT(*) FROM citas WHERE fecha = ?", (hoy_str,))
        citas_hoy = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM citas WHERE fecha BETWEEN ? AND date(?, '+7 days')", (hoy_str, hoy_str))
        citas_semana = cursor.fetchone()[0]

        lbl_kpi_inmuebles.configure(text=f"Total: {total_inm}\n(🏠 {en_venta} Venta | 🔑 {en_renta} Renta)")
        lbl_kpi_clientes.configure(text=str(total_cli))
        lbl_kpi_valor.configure(text=f"${valor_portafolio:,.2f}")
        lbl_sub_promedio.configure(text=f"📊 Valor Promedio de Propiedad: ${promedio_prop:,.2f}")
        lbl_sub_citas.configure(text=f"📅 Agenda: {citas_hoy} hoy | {citas_semana} esta semana")

        cursor.execute("""
            SELECT a.nombre, COUNT(c.id_cliente) as conteo 
            FROM asesores a
            LEFT JOIN clientes c ON a.id_asesor = c.id_asesor 
            WHERE a.activo = 1
            GROUP BY a.id_asesor
        """)
        texto_asesores = "👥 Productividad por Asesor:\n"
        for row in cursor.fetchall():
            texto_asesores += f" • {row['nombre']}: {row['conteo']} clientes asignados\n"
        lbl_kpi_asesores_lista.configure(text=texto_asesores)

# --------------------------------------------------------
# VISTA 1: ALTA DE INMUEBLES
# --------------------------------------------------------
def guardar_inmueble():
    if not txt_titulo.get().strip() or not txt_precio.get().strip():
        messagebox.showwarning("Campos incompletos", "El título y el precio son obligatorios.")
        return
    try:
        precio = float(txt_precio.get().replace(",", "").replace("$", "").strip())
        m2_terreno = float(txt_m2_terreno.get().strip()) if txt_m2_terreno.get() else 0.0
        m2_construccion = float(txt_m2_construccion.get().strip()) if txt_m2_construccion.get() else 0.0
    except ValueError:
        messagebox.showerror("Error de datos", "Introduce valores numéricos válidos en Precio y M².")
        return

    id_ase = obtener_id_asesor_por_nombre(combo_asesor_inm.get())

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO inmuebles(tipo_operacion, tipo_inmueble, titulo, precio, colonia, municipio, estado, descripcion, m2_terreno, m2_construccion, id_asesor, eliminado)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,0)
        """, (combo_operacion.get(), combo_tipo.get(), txt_titulo.get().strip(), precio, txt_colonia.get().strip(), txt_municipio.get().strip(), txt_estado.get().strip(), txt_descripcion.get().strip(), m2_terreno, m2_construccion, id_ase))
        conn.commit()
    messagebox.showinfo("Éxito", "Inmueble guardado correctamente")
    limpiar_inmueble()

def agregar_fotos(id_inmueble_directo=None):
    if not id_inmueble_directo:
        messagebox.showerror("Error", "ID de inmueble no válido")
        return

    seleccion = filedialog.askopenfilenames(title="Seleccionar fotografías", filetypes=[("Imágenes", "*.jpg *.jpeg *.png")])
    if not seleccion: return

    carpeta_destino = f"fotos/inmueble_{id_inmueble_directo}"
    os.makedirs(carpeta_destino, exist_ok=True)
    contador = 0
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        for archivo in seleccion:
            nombre = os.path.basename(archivo)
            destino = os.path.join(carpeta_destino, nombre)
            shutil.copy2(archivo, destino)
            cursor.execute("INSERT INTO fotos_inmueble(id_inmueble, ruta_archivo, descripcion, principal) VALUES (?,?,?,?)", (id_inmueble_directo, destino, "", 0))
            contador += 1
        conn.commit()
    messagebox.showinfo("Éxito", f"{contador} fotografías guardadas.")

def limpiar_inmueble():
    txt_titulo.delete(0, 'end'); txt_precio.delete(0, 'end'); txt_colonia.delete(0, 'end')
    txt_municipio.delete(0, 'end'); txt_estado.delete(0, 'end'); txt_descripcion.delete(0, 'end')
    txt_m2_terreno.delete(0, 'end'); txt_m2_construccion.delete(0, 'end')

ctk.CTkLabel(frame_alta_inmuebles, text="Alta de Inmuebles", font=("Arial", 26, "bold")).pack(pady=15)
combo_operacion = ctk.CTkComboBox(frame_alta_inmuebles, values=["VENTA", "RENTA"], width=400); combo_operacion.pack(pady=4)
combo_tipo = ctk.CTkComboBox(frame_alta_inmuebles, values=["Casa", "Departamento", "Terreno", "Local", "Oficina"], width=400); combo_tipo.pack(pady=4)
txt_titulo = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Título o Breve Descripción"); txt_titulo.pack(pady=4)
txt_precio = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Precio (Ej: 2500000)"); txt_precio.pack(pady=4)
txt_colonia = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Colonia"); txt_colonia.pack(pady=4)
txt_municipio = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Municipio / Alcaldía"); txt_municipio.pack(pady=4)
txt_estado = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Estado"); txt_estado.pack(pady=4)
txt_descripcion = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="Detalles generales"); txt_descripcion.pack(pady=4)
txt_m2_terreno = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="M2 Terreno"); txt_m2_terreno.pack(pady=4)
txt_m2_construccion = ctk.CTkEntry(frame_alta_inmuebles, width=400, placeholder_text="M2 Construcción"); txt_m2_construccion.pack(pady=4)
combo_asesor_inm = ctk.CTkComboBox(frame_alta_inmuebles, values=[], width=400); combo_asesor_inm.pack(pady=4)

btn_guardar = ctk.CTkButton(frame_alta_inmuebles, text="💾 Guardar Inmueble", command=guardar_inmueble, fg_color="#1E88E5")
btn_guardar.pack(pady=10)

# --------------------------------------------------------
# VISTA 2: ALTA DE CLIENTES
# --------------------------------------------------------
def guardar_cliente():
    if not txt_nombre_cli.get().strip():
        messagebox.showwarning("Campos vacíos", "El nombre del cliente es obligatorio.")
        return
    try:
        presupuesto = float(txt_presupuesto.get().replace(",", "").replace("$", "").strip()) if txt_presupuesto.get() else 0.0
    except ValueError:
        messagebox.showerror("Error", "Presupuesto debe ser un valor numérico.")
        return

    id_ase = obtener_id_asesor_por_nombre(combo_asesor_cli.get())

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clientes (nombre, telefono, correo, presupuesto_max, zona_interes, tipo_buscado, operacion_buscada, id_asesor)
            VALUES (?,?,?,?,?,?,?,?)
        """, (txt_nombre_cli.get().strip(), txt_tel_cli.get().strip(), txt_correo_cli.get().strip(), presupuesto, txt_zona_cli.get().strip(), combo_tipo_buscado.get(), "VENTA", id_ase))
        conn.commit()

    messagebox.showinfo("Éxito", "Cliente prospecto registrado correctamente.")
    limpiar_cliente()

def limpiar_cliente():
    txt_nombre_cli.delete(0, 'end'); txt_tel_cli.delete(0, 'end'); txt_correo_cli.delete(0, 'end')
    txt_presupuesto.delete(0, 'end'); txt_zona_cli.delete(0, 'end')

ctk.CTkLabel(frame_alta_clientes, text="Registro de Clientes Interesados", font=("Arial", 26, "bold")).pack(pady=20)
txt_nombre_cli = ctk.CTkEntry(frame_alta_clientes, width=400, placeholder_text="Nombre Completo del Cliente"); txt_nombre_cli.pack(pady=5)
txt_tel_cli = ctk.CTkEntry(frame_alta_clientes, width=400, placeholder_text="Teléfono de Contacto"); txt_tel_cli.pack(pady=5)
txt_correo_cli = ctk.CTkEntry(frame_alta_clientes, width=400, placeholder_text="Correo Electrónico"); txt_correo_cli.pack(pady=5)
txt_presupuesto = ctk.CTkEntry(frame_alta_clientes, width=400, placeholder_text="Presupuesto Máximo"); txt_presupuesto.pack(pady=5)
txt_zona_cli = ctk.CTkEntry(frame_alta_clientes, width=400, placeholder_text="Zona de Interés"); txt_zona_cli.pack(pady=5)
combo_tipo_buscado = ctk.CTkComboBox(frame_alta_clientes, values=["Casa", "Departamento", "Terreno", "Local", "Oficina"], width=400); combo_tipo_buscado.pack(pady=5)
combo_asesor_cli = ctk.CTkComboBox(frame_alta_clientes, values=[], width=400); combo_asesor_cli.pack(pady=5)

btn_guardar_cli = ctk.CTkButton(frame_alta_clientes, text="👥 Registrar Cliente", command=guardar_cliente, fg_color="#2E7D32")
btn_guardar_cli.pack(pady=20)

# --------------------------------------------------------
# VISTA: INVENTARIO DE INMUEBLES
# --------------------------------------------------------
def mostrar_inmuebles():
    global ventana_inventario
    if ventana_inventario is not None and ventana_inventario.winfo_exists():
        ventana_inventario.focus()
        return

    ventana_inventario = ctk.CTkToplevel(app)
    ventana_inventario.title("Inventario de Inmuebles")
    ventana_inventario.geometry("1100x650")

    frame_filtros = ctk.CTkFrame(ventana_inventario)
    frame_filtros.pack(fill="x", padx=10, pady=10)

    txt_colonia_buscar = ctk.CTkEntry(frame_filtros, width=180, placeholder_text="Colonia"); txt_colonia_buscar.pack(side="left", padx=5)
    txt_precio_max = ctk.CTkEntry(frame_filtros, width=150, placeholder_text="Precio máximo"); txt_precio_max.pack(side="left", padx=5)

    frame_tabla = ctk.CTkFrame(ventana_inventario)
    frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

    columnas = ("ID", "OPERACION", "TIPO", "TITULO", "PRECIO", "COLONIA")
    tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
    for col in columnas: tree.heading(col, text=col)
    tree.pack(side="left", fill="both", expand=True)

    def enviar_a_papelera():
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una propiedad de la tabla.")
            return
        id_inmueble = tree.item(seleccion[0], "values")[0]
        if messagebox.askyesno("Confirmar", f"¿Mover la propiedad #{id_inmueble} a la Papelera de Reciclaje?"):
            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE inmuebles SET eliminado = 1 WHERE id_inmueble = ?", (id_inmueble,))
                conn.commit()
            messagebox.showinfo("Completado", "Propiedad enviada a la papelera.")
            cargar_datos()

    ctk.CTkButton(frame_filtros, text="🗑️ Mover a Papelera", fg_color="#E65100", command=enviar_a_papelera).pack(side="right", padx=10)

    def editar_inmueble(event):
        seleccion = tree.selection()
        if not seleccion: return
        id_inmueble = tree.item(seleccion[0], "values")[0]

        ventana_edit = ctk.CTkToplevel(ventana_inventario)
        ventana_edit.title(f"Ficha Interna #{id_inmueble}")
        ventana_edit.geometry("500x750")
        ventana_edit.after(100, lambda: ventana_edit.focus())

        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT titulo, precio, colonia, municipio, descripcion, m2_terreno, m2_construccion, tipo_operacion, tipo_inmueble, estado FROM inmuebles WHERE id_inmueble=?", (id_inmueble,))
            registro = cursor.fetchone()

        campos = [
            ("Título", registro[0]), ("Precio", registro[1]), ("Colonia", registro[2]),
            ("Municipio", registro[3]), ("Características", registro[4]),
            ("M2 Terreno", registro[5]), ("M2 Construcción", registro[6])
        ]
        entries = {}

        for etiqueta, valor in campos:
            ctk.CTkLabel(ventana_edit, text=etiqueta).pack(pady=1)
            txt = ctk.CTkEntry(ventana_edit, width=380); txt.pack(pady=2)
            txt.insert(0, str(valor)); entries[etiqueta] = txt

        def ver_fotos():
            ventana_fotos = ctk.CTkToplevel(ventana_edit)
            ventana_fotos.title(f"Fotos Inmueble #{id_inmueble}")
            ventana_fotos.geometry("900x650")
            
            def refrescar_fotos():
                for widget in ventana_fotos.winfo_children(): widget.destroy()
                with sqlite3.connect(DB) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id_foto, ruta_archivo, principal FROM fotos_inmueble WHERE id_inmueble=? ORDER BY principal DESC", (id_inmueble,))
                    fotos = cursor.fetchall()

                if not fotos:
                    ctk.CTkLabel(ventana_fotos, text="Sin fotos asignadas.").pack(pady=20)
                    return

                scroll_frame = ctk.CTkScrollableFrame(ventana_fotos, width=850, height=600)
                scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

                ventana_fotos.imagenes_refs = []
                r, c = 0, 0
                for id_foto, ruta, principal in fotos:
                    if not os.path.exists(ruta): continue
                    try:
                        img_pil = PILImage.open(ruta)
                        img_pil.thumbnail((200, 140))
                        miniatura = ImageTk.PhotoImage(img_pil)
                        ventana_fotos.imagenes_refs.append(miniatura)
                    except: continue

                    marco = ctk.CTkFrame(scroll_frame); marco.grid(row=r, column=c, padx=10, pady=10)
                    tk.Label(marco, image=miniatura).pack(padx=2, pady=2)
                    
                    lbl_texto = f"Foto #{id_foto} " + ("⭐ PRINCIPAL" if principal == 1 else "")
                    ctk.CTkLabel(marco, text=lbl_texto, font=("Arial", 11, "bold" if principal == 1 else "normal")).pack()
                    
                    def hacer_principal(f_id=id_foto):
                        with sqlite3.connect(DB) as cn:
                            cr = cn.cursor()
                            cr.execute("UPDATE fotos_inmueble SET principal=0 WHERE id_inmueble=?", (id_inmueble,))
                            cr.execute("UPDATE fotos_inmueble SET principal=1 WHERE id_foto=?", (f_id,))
                            cn.commit()
                        messagebox.showinfo("Éxito", "Foto principal establecida.")
                        refrescar_fotos()

                    def borrar_foto(f_id=id_foto, f_ruta=ruta):
                        if messagebox.askyesno("Confirmar", "¿Eliminar fotografía?"):
                            try:
                                if os.path.exists(f_ruta): os.remove(f_ruta)
                            except: pass
                            with sqlite3.connect(DB) as cn:
                                cr = cn.cursor()
                                cr.execute("DELETE FROM fotos_inmueble WHERE id_foto=?", (f_id,))
                                cn.commit()
                            refrescar_fotos()

                    ctk.CTkButton(marco, text="⭐ Principal", width=90, command=hacer_principal).pack(pady=1)
                    ctk.CTkButton(marco, text="🗑 Borrar", width=90, fg_color="#C62828", command=borrar_foto).pack(pady=1)
                    c += 1
                    if c >= 4: c = 0; r += 1

            refrescar_fotos()

        def generar_pdf_premium():
            archivo_pdf = f"pdfs/Ficha_Premium_{id_inmueble}.pdf"
            doc = SimpleDocTemplate(archivo_pdf, pagesize=(612, 792), rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()
            
            estilo_titulo = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=24, textColor=colors.HexColor('#1A237E'), spaceAfter=4)
            estilo_sub = ParagraphStyle('SubStyle', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#5C6BC0'), spaceAfter=15)
            estilo_normal = ParagraphStyle('NormStyle', fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#212121'))
            estilo_negrita = ParagraphStyle('BoldStyle', fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=colors.HexColor('#1A237E'))

            elementos = [
                Paragraph("<b>GARANZIA REAL ESTATE</b>", estilo_titulo), 
                Paragraph(f"Ficha Técnica Comercial — Ref ID: #{id_inmueble}", estilo_sub),
                Spacer(1, 10)
            ]
            
            # --- PARCHE DE FOTO PRINCIPAL ---
            ruta_foto_principal = None
            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ruta_archivo FROM fotos_inmueble WHERE id_inmueble = ? AND principal = 1", (id_inmueble,))
                resultado_foto = cursor.fetchone()
                
                if resultado_foto:
                    ruta_foto_principal = resultado_foto[0]
                else:
                    cursor.execute("SELECT ruta_archivo FROM fotos_inmueble WHERE id_inmueble = ? LIMIT 1", (id_inmueble,))
                    resultado_respaldo = cursor.fetchone()
                    if resultado_respaldo:
                        ruta_foto_principal = resultado_respaldo[0]

            if ruta_foto_principal and os.path.exists(ruta_foto_principal):
                try:
                    img_pdf = RLImage(ruta_foto_principal, width=400, height=260)
                    img_pdf.hAlign = 'CENTER'
                    elementos.append(img_pdf)
                    elementos.append(Spacer(1, 20))
                except:
                    elementos.append(Paragraph(f"<i>(Error al cargar la imagen principal)</i>", estilo_normal))
                    elementos.append(Spacer(1, 10))
            else:
                elementos.append(Paragraph("<i>Esta propiedad no cuenta con fotografías registradas.</i>", estilo_normal))
                elementos.append(Spacer(1, 10))

            try:
                precio_formateado = f"${float(entries['Precio'].get()):,.2f}"
            except:
                precio_formateado = entries['Precio'].get()

            datos_tabla = [
                [Paragraph("<b>Título Comercial:</b>", estilo_negrita), Paragraph(str(entries["Título"].get()), estilo_normal)],
                [Paragraph("<b>Tipo de Propiedad:</b>", estilo_negrita), Paragraph(f"{registro[8]} en {registro[7]}", estilo_normal)],
                [Paragraph("<b>Precio de Lista:</b>", estilo_negrita), Paragraph(precio_formateado, estilo_normal)],
                [Paragraph("<b>Ubicación (Colonia):</b>", estilo_negrita), Paragraph(str(entries["Colonia"].get()), estilo_normal)],
                [Paragraph("<b>Municipio / Estado:</b>", estilo_negrita), Paragraph(f"{entries['Municipio'].get()}, {registro[9]}", estilo_normal)],
                [Paragraph("<b>Superficie Terreno:</b>", estilo_negrita), Paragraph(f"{entries['M2 Terreno'].get()} m²", estilo_normal)],
                [Paragraph("<b>Superficie Construcción:</b>", estilo_negrita), Paragraph(f"{entries['M2 Construcción'].get()} m²", estilo_normal)],
                [Paragraph("<b>Detalles y Descripción:</b>", estilo_negrita), Paragraph(str(entries["Características"].get()), estilo_normal)]
            ]
            
            t = Table(datos_tabla, colWidths=[140, 390])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F5F5F5')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D9FF')),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 8)
            ]))
            elementos.append(t)
            
            try:
                doc.build(elementos)
                messagebox.showinfo("Reporte", f"Ficha exportada con éxito en:\n{archivo_pdf}")
            except Exception as e:
                messagebox.showerror("Error al generar PDF", f"No se pudo estructurar el documento: {e}")

        def actualizar_inmueble():
            try:
                v_precio = float(entries["Precio"].get())
                v_terreno = float(entries["M2 Terreno"].get()) if entries["M2 Terreno"].get() else 0.0
                v_construccion = float(entries["M2 Construcción"].get()) if entries["M2 Construcción"].get() else 0.0
            except ValueError:
                messagebox.showerror("Error", "Asegúrate de que Precio y Metros Cuadrados sean numéricos.")
                return

            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE inmuebles SET titulo=?, precio=?, colonia=?, municipio=?, descripcion=?, m2_terreno=?, m2_construccion=? WHERE id_inmueble=?
                """, (entries["Título"].get(), v_precio, entries["Colonia"].get(), entries["Municipio"].get(), entries["Características"].get(), v_terreno, v_construccion, id_inmueble))
                conn.commit()
            ventana_edit.destroy()
            cargar_datos()

        ctk.CTkButton(ventana_edit, text="🖼️ Ver / Gestionar Fotos", command=ver_fotos).pack(pady=4)
        ctk.CTkButton(ventana_edit, text="📷 Agregar Nuevas Fotos", fg_color="#0288D1", command=lambda: agregar_fotos(id_inmueble)).pack(pady=4)
        ctk.CTkButton(ventana_edit, text="📄 Ficha Premium PDF", fg_color="#673AB7", command=generar_pdf_premium).pack(pady=4)
        ctk.CTkButton(ventana_edit, text="Guardar Cambios", fg_color="#2E7D32", command=actualizar_inmueble).pack(pady=15)

    tree.bind("<Double-1>", editar_inmueble)

    def cargar_datos():
        for item in tree.get_children(): tree.delete(item)
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_inmueble, tipo_operacion, tipo_inmueble, titulo, precio, colonia FROM inmuebles WHERE eliminado = 0")
            for fila in cursor.fetchall():
                l = list(fila); l[4] = f"${l[4]:,.2f}"
                tree.insert("", "end", values=l)
                
    ctk.CTkButton(frame_filtros, text="🔍 Actualizar Tabla", command=cargar_datos).pack(side="left", padx=10)
    cargar_datos()

# --------------------------------------------------------
# VISTA: CARTERA DE CLIENTES
# --------------------------------------------------------
def mostrar_clientes():
    global ventana_cartera
    if ventana_cartera is not None and ventana_cartera.winfo_exists():
        ventana_cartera.focus()
        return

    ventana_cartera = ctk.CTkToplevel(app)
    ventana_cartera.title("Cartera de Clientes Prospectos")
    ventana_cartera.geometry("1000x550")

    frame_tabla = ctk.CTkFrame(ventana_cartera)
    frame_tabla.pack(fill="both", expand=True, padx=15, pady=15)

    columnas = ("ID", "NOMBRE", "TELEFONO", "CORREO", "PRESUPUESTO MAX", "ZONA")
    tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
    for col in columnas: tree.heading(col, text=col)
    tree.pack(side="left", fill="both", expand=True)

    def ejecutar_matching(event):
        seleccion = tree.selection()
        if not seleccion: return
        datos = tree.item(seleccion[0], "values")
        id_cliente = datos[0]
        
        with sqlite3.connect(DB) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clientes WHERE id_cliente = ?", (id_cliente,))
            cli = cursor.fetchone()

        ventana_match = ctk.CTkToplevel(ventana_cartera)
        ventana_match.title(f"Matches para {cli['nombre']}")
        ventana_match.geometry("900x500")

        frame_t_match = ctk.CTkFrame(ventana_match)
        frame_t_match.pack(fill="both", expand=True, padx=15, pady=15)

        cols_m = ("ID", "OPERACIÓN", "TIPO", "TÍTULO", "PRECIO", "COLONIA")
        tree_m = ttk.Treeview(frame_t_match, columns=cols_m, show="headings")
        for col in cols_m: tree_m.heading(col, text=col)
        tree_m.pack(fill="both", expand=True)

        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_inmueble, tipo_operacion, tipo_inmueble, titulo, precio, colonia 
                FROM inmuebles 
                WHERE eliminado = 0 AND tipo_inmueble = ? AND precio <= ?
            """, (cli['tipo_buscado'], cli['presupuesto_max']))
            for prop in cursor.fetchall():
                l_p = list(prop); l_p[4] = f"${l_p[4]:,.2f}"
                tree_m.insert("", "end", values=l_p)

    tree.bind("<Double-1>", ejecutar_matching)

    def cargar_clientes():
        for item in tree.get_children(): tree.delete(item)
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_cliente, nombre, telefono, correo, presupuesto_max, zona_interes FROM clientes")
            for fila in cursor.fetchall():
                l = list(fila); l[4] = f"${l[4]:,.2f}"
                tree.insert("", "end", values=l)

    cargar_clientes()


# =========================================================================
# 📅 INTERFAZ DEL MÓDULO ACTUALIZADO: AGENDA DE CITAS (CON CALENDARIO VISUAL)
# =========================================================================
ctk.CTkLabel(frame_agenda, text="Calendario Avanzado de Recorridos y Citas", font=("Arial", 26, "bold"), text_color="#1A237E").pack(pady=(20, 10), padx=30, anchor="w")

# Contenedor Principal Dividido en Dos Columnas (Izquierda: Calendario y Formulario | Derecha: Tabla de eventos de ese día)
split_container = ctk.CTkFrame(frame_agenda, fg_color="transparent")
split_container.pack(fill="both", expand=True, padx=20, pady=10)

columna_izquierda = ctk.CTkFrame(split_container, fg_color="white", corner_radius=10, width=450)
columna_izquierda.pack(side="left", fill="both", padx=10, pady=5)

columna_derecha = ctk.CTkFrame(split_container, fg_color="white", corner_radius=10)
columna_derecha.pack(side="right", fill="both", expand=True, padx=10, pady=5)

# --- COLONNA IZQUIERDA: COMPONENTE CALENDARIO ---
# Nota: Forzamos estilos básicos compatibles con tkinter tradicional
cal_visual = Calendar(columna_izquierda, selectmode='day', date_pattern='yyyy-mm-dd',
                      background='#1A237E', foreground='white', headersbackground='#283593',
                      headersforeground='white', selectbackground='#1E88E5', selectforeground='white')
cal_visual.pack(fill="x", padx=15, pady=15)

# Formulario rápido para agendar cita justo abajo del calendario
ctk.CTkLabel(columna_izquierda, text="➕ Programar Nueva Cita", font=("Arial", 14, "bold"), text_color="#1A237E").pack(pady=5)

combo_cita_cliente = ctk.CTkComboBox(columna_izquierda, values=[], width=380)
combo_cita_cliente.pack(pady=3)
combo_cita_inmueble = ctk.CTkComboBox(columna_izquierda, values=[], width=380)
combo_cita_inmueble.pack(pady=3)

frame_tiempo = ctk.CTkFrame(columna_izquierda, fg_color="transparent")
frame_tiempo.pack(pady=3)
txt_cita_hora = ctk.CTkEntry(frame_tiempo, width=120, placeholder_text="Hora (Ej: 16:30)")
txt_cita_hora.pack(side="left", padx=5)

txt_cita_notas = ctk.CTkEntry(columna_izquierda, width=380, placeholder_text="Notas o comentarios del recorrido")
txt_cita_notas.pack(pady=5)

def guardar_cita_agenda():
    fecha_sel = cal_visual.get_date() # Captura el día seleccionado en el calendario
    raw_cliente = combo_cita_cliente.get()
    raw_inmueble = combo_cita_inmueble.get()
    hora = txt_cita_hora.get().strip()
    notas = txt_cita_notas.get().strip()
    
    if "Seleccionar" in raw_cliente or not raw_cliente or "Seleccionar" in raw_inmueble or not raw_inmueble or not hora:
        messagebox.showwarning("Campos vacíos", "Por favor asigne un Cliente, Inmueble y Hora para la cita.")
        return
        
    id_cli = raw_cliente.split(" - ")[0]
    id_inm = raw_inmueble.split(" - ")[0]
    
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO citas (id_cliente, id_inmueble, fecha, hora, notas) VALUES (?,?,?,?,?)",
                       (id_cli, id_inm, fecha_sel, hora, notas))
        conn.commit()
        
    messagebox.showinfo("Agenda", f"Cita programada con éxito para el día {fecha_sel} a las {hora}.")
    txt_cita_hora.delete(0, 'end');
    txt_cita_notas.delete(0, 'end')
    cargar_citas_del_dia()

btn_agendar = ctk.CTkButton(columna_izquierda, text="📅 Confirmar Cita", command=guardar_cita_agenda, fg_color="#1A237E")
btn_agendar.pack(pady=10)


# --- COLONNA DERECHA: MONITOREO DE CITAS DEL DÍA SELECCIONADO ---
lbl_titulo_citas_dia = ctk.CTkLabel(columna_derecha, text="Citas Agendadas", font=("Arial", 16, "bold"), text_color="#1A237E")
lbl_titulo_citas_dia.pack(pady=(15, 5), padx=15, anchor="w")

frame_t_citas = ctk.CTkFrame(columna_derecha)
frame_t_citas.pack(fill="both", expand=True, padx=15, pady=10)

columnas_citas = ("ID", "HORA", "CLIENTE", "PROPIEDAD / TITULO", "NOTAS")
tree_citas = ttk.Treeview(frame_t_citas, columns=columnas_citas, show="headings")
for col in columnas_citas: tree_citas.heading(col, text=col)
tree_citas.column("ID", width=40, anchor="center")
tree_citas.column("HORA", width=70, anchor="center")
tree_citas.pack(fill="both", expand=True)

def cargar_citas_del_dia():
    fecha_sel = cal_visual.get_date()
    lbl_titulo_citas_dia.configure(text=f"🗓️ Citas y Recorridos para el día: {fecha_sel}")
    
    for item in tree_citas.get_children(): tree_citas.delete(item)
    
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id_cita, c.hora, cl.nombre, i.titulo, c.notas
            FROM citas c
            JOIN clientes cl ON c.id_cliente = cl.id_cliente
            JOIN inmuebles i ON c.id_inmueble = i.id_inmueble
            WHERE c.fecha = ?
            ORDER BY c.hora ASC
        """, (fecha_sel,))
        for fila in cursor.fetchall():
            tree_citas.insert("", "end", values=fila)

# Evento para refrescar la tabla del lado derecho automáticamente al cambiar de día en el calendario
cal_visual.bind("<<CalendarSelected>>", lambda e: cargar_citas_del_dia())

def borrar_cita_seleccionada():
    sel = tree_citas.selection()
    if not sel:
        messagebox.showwarning("Atención", "Seleccione una cita de la lista de la derecha para cancelarla.")
        return
    id_cita = tree_citas.item(sel[0], "values")[0]
    if messagebox.askyesno("Confirmar", "¿Desea cancelar y eliminar esta cita de la agenda?"):
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM citas WHERE id_cita = ?", (id_cita,))
            conn.commit()
        cargar_citas_del_dia()

ctk.CTkButton(columna_derecha, text="❌ Cancelar Cita Seleccionada", fg_color="#C62828", command=borrar_cita_seleccionada).pack(pady=10, padx=15, anchor="e")

def actualizar_componentes_agenda():
    """Carga los comboboxes de la agenda con clientes e inmuebles reales al abrir la vista."""
    clientes = obtener_lista_clientes_combo()
    inmuebles = obtener_lista_inmuebles_combo()
    
    combo_cita_cliente.configure(values=clientes)
    combo_cita_cliente.set(clientes[0] if clientes else "Seleccionar Cliente...")
    
    combo_cita_inmueble.configure(values=inmuebles)
    combo_cita_inmueble.set(inmuebles[0] if inmuebles else "Seleccionar Inmueble...")
    
    cargar_citas_del_dia()


# =========================================================================
# 💼 INTERFAZ DEL MÓDULO: ADMINISTRAR ASESORES
# =========================================================================
ctk.CTkLabel(frame_asesores, text="Administración de Asesores de Venta", font=("Arial", 26, "bold"), text_color="#1A237E").pack(pady=(25,15), padx=30, anchor="w")

frame_captura_ase = ctk.CTkFrame(frame_asesores, fg_color="white", corner_radius=10)
frame_captura_ase.pack(fill="x", padx=30, pady=10)

txt_nombre_ase = ctk.CTkEntry(frame_captura_ase, width=250, placeholder_text="Nombre del Asesor")
txt_nombre_ase.grid(row=0, column=0, padx=10, pady=15)
txt_tel_ase = ctk.CTkEntry(frame_captura_ase, width=180, placeholder_text="Teléfono")
txt_tel_ase.grid(row=0, column=1, padx=10, pady=15)
txt_correo_ase = ctk.CTkEntry(frame_captura_ase, width=220, placeholder_text="Correo Electrónico")
txt_correo_ase.grid(row=0, column=2, padx=10, pady=15)

def registrar_asesor():
    nombre = txt_nombre_ase.get().strip()
    tel = txt_tel_ase.get().strip()
    correo = txt_correo_ase.get().strip()
    
    if not nombre or not tel:
        messagebox.showwarning("Campos vacíos", "El nombre y teléfono son obligatorios.")
        return
        
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO asesores (nombre, telefono, correo, activo) VALUES (?,?,?,1)", (nombre, tel, correo))
        conn.commit()
    
    txt_nombre_ase.delete(0, 'end'); txt_tel_ase.delete(0, 'end'); txt_correo_ase.delete(0, 'end')
    messagebox.showinfo("Éxito", "Asesor comercial registrado.")
    actualizar_tabla_asesores()

btn_alta_ase = ctk.CTkButton(frame_captura_ase, text="➕ Agregar Asesor", command=registrar_asesor, fg_color="#2E7D32")
btn_alta_ase.grid(row=0, column=3, padx=15, pady=15)

frame_t_ase = ctk.CTkFrame(frame_asesores)
frame_t_ase.pack(fill="both", expand=True, padx=30, pady=15)

columnas_ase = ("ID", "NOMBRE", "TELEFONO", "CORREO", "ESTADO")
tree_asesores = ttk.Treeview(frame_t_ase, columns=columnas_ase, show="headings")
for col in columnas_ase: tree_asesores.heading(col, text=col)
tree_asesores.pack(fill="both", expand=True)

def actualizar_tabla_asesores():
    for item in tree_asesores.get_children(): tree_asesores.delete(item)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_asesor, nombre, telefono, correo, activo FROM asesores")
        for f in cursor.fetchall():
            lf = list(f)
            lf[4] = "Activo" if lf[4] == 1 else "Inactivo"
            tree_asesores.insert("", "end", values=lf)

# =========================================================================
# 🗑️ INTERFAZ DEL MÓDULO: PAPELERA DE RECICLAJE (CORREGIDO)
# =========================================================================

# 1. Primero definimos las funciones que usarán los botones
def restaurar_propiedad():
    sel = tree_papelera.selection()
    if not sel:
        messagebox.showwarning("Atención", "Selecciona una propiedad para restaurar.")
        return
    id_inm = tree_papelera.item(sel[0], "values")[0]
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE inmuebles SET eliminado = 0 WHERE id_inmueble = ?", (id_inm,))
        conn.commit()
    messagebox.showinfo("Restaurado", f"Inmueble #{id_inm} devuelto al inventario activo.")
    actualizar_tabla_papelera()

def eliminar_definitivo():
    sel = tree_papelera.selection()
    if not sel:
        messagebox.showwarning("Atención", "Selecciona una propiedad.")
        return
    id_inm = tree_papelera.item(sel[0], "values")[0]
    if messagebox.askyesno("🚨 Alerta Crítica", f"¿Eliminar DEFINITIVAMENTE el inmueble #{id_inm}?\nEsta acción borrará fotos permanentemente de la base de datos y del disco."):
        
        carpeta = f"fotos/inmueble_{id_inm}"
        if os.path.exists(carpeta):
            try:
                shutil.rmtree(carpeta)
            except Exception as e:
                print(f"Advertencia: No se pudo eliminar la carpeta física: {e}")

        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fotos_inmueble WHERE id_inmueble = ?", (id_inm,))
            cursor.execute("DELETE FROM inmuebles WHERE id_inmueble = ?", (id_inm,))
            conn.commit()
        messagebox.showinfo("Borrado", "Eliminado por completo del sistema.")
        actualizar_tabla_papelera()

def actualizar_tabla_papelera():
    for item in tree_papelera.get_children(): tree_papelera.delete(item)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_inmueble, tipo_operacion, tipo_inmueble, titulo, precio, colonia FROM inmuebles WHERE eliminado = 1")
        for fila in cursor.fetchall():
            l = list(fila); l[4] = f"${l[4]:,.2f}"
            tree_papelera.insert("", "end", values=l)


# 2. Ahora que las funciones ya existen en memoria, creamos la interfaz visual
ctk.CTkLabel(frame_papelera, text="Papelera de Reciclaje (Propiedades)", font=("Arial", 26, "bold"), text_color="#1A237E").pack(pady=(25,15), padx=30, anchor="w")

frame_acciones_pap = ctk.CTkFrame(frame_papelera, fg_color="transparent")
frame_acciones_pap.pack(fill="x", padx=30, pady=5)

frame_t_pap = ctk.CTkFrame(frame_papelera)
frame_t_pap.pack(fill="both", expand=True, padx=30, pady=15)

columnas_pap = ("ID", "OPERACION", "TIPO", "TITULO", "PRECIO", "COLONIA")
tree_papelera = ttk.Treeview(frame_t_pap, columns=columnas_pap, show="headings")
for col in columnas_pap: tree_papelera.heading(col, text=col)
tree_papelera.pack(fill="both", expand=True)

# Los botones ahora pueden llamar a las funciones sin romper el programa:
ctk.CTkButton(frame_acciones_pap, text="🔄 Restaurar al Inventario", fg_color="#2E7D32", command=restaurar_propiedad).pack(side="left", padx=5)
ctk.CTkButton(frame_acciones_pap, text="💥 Borrar Definitivamente", fg_color="#C62828", hover_color="#B71C1C", command=eliminar_definitivo).pack(side="left", padx=5)

def actualizar_tabla_papelera():
    for item in tree_papelera.get_children(): tree_papelera.delete(item)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_inmueble, tipo_operacion, tipo_inmueble, titulo, precio, colonia FROM inmuebles WHERE eliminado = 1")
        for fila in cursor.fetchall():
            l = list(fila); l[4] = f"${l[4]:,.2f}"
            tree_papelera.insert("", "end", values=l)

# Inicialización por defecto en el Dashboard
cambiar_vista(frame_dashboard)

app.mainloop()
