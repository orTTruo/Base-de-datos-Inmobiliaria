import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from PIL import Image as PILImage, ImageTk
from tkcalendar import Calendar

import database_manager as db
import pdf_generator

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class SistemaInmobiliarioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GRUPO GARANZIA INMOBILIARIA")
        self.geometry("1250x780")
        
        self.ventana_inventario = None
        self.rutas_fotos_temporales = []
        
        # UI Base Layout Novedoso Anteriores
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#1A237E")
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="GRUPO GARANZIA", font=("Arial", 18, "bold"), text_color="white").pack(pady=30)
        
        ctk.CTkButton(self.sidebar, text="🏠 Alta de Inmueble", fg_color="transparent", text_color="white", anchor="w", command=lambda: self.conmutar_panel(self.frame_alta_inm)).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(self.sidebar, text="🔍 Inventario Inmuebles", fg_color="transparent", text_color="white", anchor="w", command=self.mostrar_inventario).pack(fill="x", padx=15, pady=5) 
        ctk.CTkButton(self.sidebar, text="👥 Registro Prospectos", fg_color="transparent", text_color="white", anchor="w", command=lambda: self.conmutar_panel(self.frame_alta_clientes)).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(self.sidebar, text="📈 Prospectos activos", fg_color="transparent", text_color="white", anchor="w", command=self.mostrar_buscador_prospectos).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(self.sidebar, text="💼 Control de Asesores", fg_color="transparent", text_color="white", anchor="w", command=lambda: [self.conmutar_panel(self.frame_asesores), self.actualizar_tabla_asesores()]).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(self.sidebar, text="📅 Agenda de Visitas", fg_color="transparent", text_color="white", anchor="w", command=lambda: [self.conmutar_panel(self.frame_agenda), self.actualizar_agenda_datos()]).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(self.sidebar, text="🗑️ Papelera", fg_color="transparent", text_color="white", anchor="w", command=lambda: [self.conmutar_panel(self.frame_papelera), self.actualizar_tabla_papelera()]).pack(fill="x", padx=15, pady=5)

        self.contenedor_principal = ctk.CTkFrame(self, fg_color="#F5F5F5", corner_radius=0)
        self.contenedor_principal.pack(side="right", fill="both", expand=True)
        
        self.crear_paneles_arquitectura()
        self.conmutar_panel(self.frame_alta_inm)

    def conmutar_panel(self, panel):
        for p in [self.frame_alta_inm, self.frame_alta_clientes, self.frame_asesores, self.frame_agenda, self.frame_papelera]:
            p.pack_forget()
        panel.pack(fill="both", expand=True, padx=25, pady=25)

    def crear_paneles_arquitectura(self):
        # ---------------------------------------------------------------------
        # CORRECCIÓN SOLUCIÓN 4: SCROLLBAR COMPLETAMENTE FUNCIONAL
        # ---------------------------------------------------------------------
        self.frame_alta_inm = ctk.CTkScrollableFrame(self.contenedor_principal, fg_color="transparent")
        
        frame_interior = ctk.CTkFrame(self.frame_alta_inm, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        frame_interior.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame_interior, text="Registro de Nuevo Inmueble", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=15, padx=20, anchor="w")
        
        def crear_bloque_campo(parent, texto):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=4)
            lbl = ctk.CTkLabel(f, text=texto, font=("Arial", 12, "bold"), width=150, anchor="w")
            lbl.pack(side="left")
            return f

        # Formulario Estilo Original Asegurado
        self.cmb_op = ctk.CTkComboBox(crear_bloque_campo(frame_interior, "Tipo Operación:"), values=["VENTA", "RENTA"], width=280)
        self.cmb_op.pack(side="left")
        
        self.cmb_tipo = ctk.CTkComboBox(crear_bloque_campo(frame_interior, "Tipo Inmueble:"), values=["Casa", "Departamento", "Terreno", "Local", "Oficina"], width=280)
        self.cmb_tipo.pack(side="left")

        self.txt_tit = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Título Comercial:"), width=450)
        self.txt_tit.pack(side="left")
        
        self.txt_prc = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Precio ($ MXN):"), width=280)
        self.txt_prc.pack(side="left")
        
        self.txt_col = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Colonia:"), width=350)
        self.txt_col.pack(side="left")
        
        self.txt_mun = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Municipio / Alc:"), width=350)
        self.txt_mun.pack(side="left")
        
        self.txt_est = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Estado:"), width=350)
        self.txt_est.pack(side="left")

        self.txt_m2t = ctk.CTkEntry(crear_bloque_campo(frame_interior, "M² Terreno:"), width=180)
        self.txt_m2t.pack(side="left")

        self.txt_m2c = ctk.CTkEntry(crear_bloque_campo(frame_interior, "M² Construcción:"), width=180)
        self.txt_m2c.pack(side="left")

        self.txt_desc = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Descripción:"), width=450)
        self.txt_desc.pack(side="left")
        
        self.cmb_ase_inm = ctk.CTkComboBox(crear_bloque_campo(frame_interior, "Asesor Asignado:"), values=["Seleciona Asesor"], width=280)
        self.cmb_ase_inm.pack(side="left")

        f_media = ctk.CTkFrame(frame_interior, fg_color="transparent")
        f_media.pack(fill="x", padx=20, pady=15)
        self.lbl_fotos_info = ctk.CTkLabel(f_media, text="Fotos Cargadas: 0", font=("Arial", 12, "italic"))
        self.lbl_fotos_info.pack(side="left", padx=10)
        ctk.CTkButton(f_media, text="📷 Seleccionar Imágenes", fg_color="#455A64", command=self.cargar_fotos_dialogo_alta).pack(side="left", padx=10)
        
        ctk.CTkButton(frame_interior, text="💾 Registrar Inmueble", fg_color="#2E7D32", height=40, font=("Arial", 13, "bold"), command=self.procesar_guardar_inmueble).pack(pady=20, padx=20, fill="x")

        # ---------------------------------------------------------------------
        # PANEL: REGISTRO DE PROSPECTOS (ASPECTO ORIGINAL RESTAURADO)
        # ---------------------------------------------------------------------
        self.frame_alta_clientes = ctk.CTkFrame(self.contenedor_principal, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        ctk.CTkLabel(self.frame_alta_clientes, text="Registro y Alta de Prospectos (Leads)", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=20, padx=25, anchor="w")
        
        def crear_fila_cliente(texto):
            f = ctk.CTkFrame(self.frame_alta_clientes, fg_color="transparent")
            f.pack(fill="x", padx=25, pady=6)
            ctk.CTkLabel(f, text=texto, font=("Arial", 12, "bold"), width=180, anchor="w").pack(side="left")
            return f

        self.txt_nom_cli = ctk.CTkEntry(crear_fila_cliente("Nombre del Cliente:"), width=400)
        self.txt_nom_cli.pack(side="left")
        self.txt_tel_cli = ctk.CTkEntry(crear_fila_cliente("Teléfono Celular (10 dgt):"), width=400)
        self.txt_tel_cli.pack(side="left")
        self.txt_cor_cli = ctk.CTkEntry(crear_fila_cliente("Correo Electrónico:"), width=400)
        self.txt_cor_cli.pack(side="left")
        self.txt_pres_cli = ctk.CTkEntry(crear_fila_cliente("Presupuesto Máximo:"), width=400)
        self.txt_pres_cli.pack(side="left")
        self.txt_col_cli = ctk.CTkEntry(crear_fila_cliente("Colonia de Interés:"), width=400)
        self.txt_col_cli.pack(side="left")
        
        self.cmb_tipo_cli = ctk.CTkComboBox(crear_fila_cliente("Inmueble Solicitado:"), values=["Casa", "Departamento", "Terreno", "Local", "Oficina"], width=400)
        self.cmb_tipo_cli.pack(side="left")
        self.cmb_ase_cli = ctk.CTkComboBox(crear_fila_cliente("Asesor de Seguimiento:"), width=400)
        self.cmb_ase_cli.pack(side="left")

        f_acts_cli = ctk.CTkFrame(self.frame_alta_clientes, fg_color="transparent")
        f_acts_cli.pack(fill="x", padx=25, pady=25)
        ctk.CTkButton(f_acts_cli, text="💾 Registrar Cliente", fg_color="#2E7D32", height=38, command=self.procesar_guardar_cliente).pack(side="left", padx=5)
        ctk.CTkButton(f_acts_cli, text="🧼 Eliminar Clientes Duplicados", fg_color="#78909C", height=38, command=self.eliminar_clientes_duplicados).pack(side="left", padx=5)

        # ---------------------------------------------------------------------
        # PANEL: ADMINISTRAR ASESORES
        # ---------------------------------------------------------------------
        self.frame_asesores = ctk.CTkFrame(self.contenedor_principal, fg_color="transparent")
        f_bloque_as = ctk.CTkFrame(self.frame_asesores, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        f_bloque_as.pack(fill="both", expand=True)
        
        ctk.CTkLabel(f_bloque_as, text="Administración y Control de Asesores", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=15, padx=20, anchor="w")
        
        f_alta_as = ctk.CTkFrame(f_bloque_as, fg_color="transparent")
        f_alta_as.pack(fill="x", padx=20, pady=10)
        
        self.txt_n_as = ctk.CTkEntry(f_alta_as, placeholder_text="Nombre Completo", width=180); self.txt_n_as.pack(side="left", padx=4)
        self.txt_emp_as = ctk.CTkEntry(f_alta_as, placeholder_text="Empresa", width=140); self.txt_emp_as.pack(side="left", padx=4)
        self.txt_t_as = ctk.CTkEntry(f_alta_as, placeholder_text="Teléfono (10 dgt)", width=140); self.txt_t_as.pack(side="left", padx=4)
        self.txt_c_as = ctk.CTkEntry(f_alta_as, placeholder_text="Correo Válido", width=180); self.txt_c_as.pack(side="left", padx=4)
        
        ctk.CTkButton(f_alta_as, text="➕ Dar de Alta", command=self.agregar_asesor, fg_color="#1A237E").pack(side="left", padx=4)

        self.tree_as = ttk.Treeview(f_bloque_as, columns=("ID", "NOMBRE", "TELEFONO", "CORREO"), show="headings")
        for c in ("ID", "NOMBRE", "TELEFONO", "CORREO"): self.tree_as.heading(c, text=c); self.tree_as.column(c, anchor="center")
        self.tree_as.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkButton(f_bloque_as, text="🗑️ Eliminar Asesor Seleccionado de Forma Segura", fg_color="#C62828", command=self.eliminar_asesor_seguro).pack(pady=15, padx=20, anchor="w")

        # ---------------------------------------------------------------------
        # PANEL: AGENDA DE CITAS
        # ---------------------------------------------------------------------
        self.frame_agenda = ctk.CTkFrame(self.contenedor_principal, fg_color="transparent")
        f_bloque_ag = ctk.CTkFrame(self.frame_agenda, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        f_bloque_ag.pack(fill="both", expand=True)
        
        ctk.CTkLabel(f_bloque_ag, text="Agenda de Citas Inteligente", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=15, padx=20, anchor="w")
        
        frame_top_ag = ctk.CTkFrame(f_bloque_ag, fg_color="transparent")
        frame_top_ag.pack(fill="x", padx=20)

        f_cal = ctk.CTkFrame(frame_top_ag, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0")
        f_cal.pack(side="left", padx=(0, 15))
        
        self.cal = Calendar(f_cal, selectmode='day', date_pattern='yyyy-mm-dd',
                            background='#1A237E', foreground='white', 
                            headersbackground='#ECEFF1', headersforeground='black',
                            selectbackground='#1E88E5', selectforeground='white',
                            normalbackground='white', normalforeground='black',
                            weekendbackground='#F5F5F5', weekendforeground='black')
        self.cal.pack(padx=10, pady=10)

        f_form_ag = ctk.CTkFrame(frame_top_ag, fg_color="transparent")
        f_form_ag.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(f_form_ag, text="Seleccionar Cliente Prospecto:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(2,0))
        self.cmb_age_cli = ctk.CTkComboBox(f_form_ag, width=380); self.cmb_age_cli.pack(pady=2, anchor="w")
        
        ctk.CTkLabel(f_form_ag, text="Seleccionar Propiedad del Inventario:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(2,0))
        self.cmb_age_inm = ctk.CTkComboBox(f_form_ag, width=380); self.cmb_age_inm.pack(pady=2, anchor="w")
        
        ctk.CTkLabel(f_form_ag, text="Hora de Cita (HH:MM):", font=("Arial", 11, "bold")).pack(anchor="w", pady=(2,0))
        f_hm = ctk.CTkFrame(f_form_ag, fg_color="transparent")
        f_hm.pack(pady=2, anchor="w")
        self.cmb_h = ctk.CTkComboBox(f_hm, width=80, values=[f"{i:02d}" for i in range(8, 21)]); self.cmb_h.pack(side="left", padx=2)
        self.cmb_m = ctk.CTkComboBox(f_hm, width=80, values=["00", "15", "30", "45"]); self.cmb_m.pack(side="left", padx=2)

        self.txt_nota_cita = ctk.CTkEntry(f_form_ag, width=380, placeholder_text="Notas especiales..."); self.txt_nota_cita.pack(pady=8, anchor="w")
        ctk.CTkButton(f_form_ag, text="📅 Agendar Nueva Cita", command=self.registrar_cita_agenda, fg_color="#1A237E").pack(pady=4, anchor="w")

        self.tree_age = ttk.Treeview(f_bloque_ag, columns=("ID", "CLIENTE", "INMUEBLE", "FECHA_HORA", "NOTAS"), show="headings")
        for c in ("ID", "CLIENTE", "INMUEBLE", "FECHA_HORA", "NOTAS"): self.tree_age.heading(c, text=c); self.tree_age.column(c, anchor="center")
        self.tree_age.pack(fill="both", expand=True, padx=20, pady=10)

        f_ops_citas = ctk.CTkFrame(f_bloque_ag, fg_color="transparent")
        f_ops_citas.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(f_ops_citas, text="⏳ Cambiar Fecha/Hora Cita", fg_color="#F57C00", command=self.modificar_fecha_cita).pack(side="left", padx=5)
        ctk.CTkButton(f_ops_citas, text="❌ Cancelar/Eliminar Cita", fg_color="#D32F2F", command=self.eliminar_cita).pack(side="left", padx=5)

        # ---------------------------------------------------------------------
        # PANEL: PAPELERA DE RECICLAJE
        # ---------------------------------------------------------------------
        self.frame_papelera = ctk.CTkFrame(self.contenedor_principal, fg_color="transparent")
        f_bloque_pap = ctk.CTkFrame(self.frame_papelera, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        f_bloque_pap.pack(fill="both", expand=True)
        
        ctk.CTkLabel(f_bloque_pap, text="Papelera de Reciclaje de Inmuebles", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=15, padx=20, anchor="w")
        
        f_btns_pap = ctk.CTkFrame(f_bloque_pap, fg_color="transparent")
        f_btns_pap.pack(fill="x", padx=20)
        ctk.CTkButton(f_btns_pap, text="🔄 Restaurar Propiedad", fg_color="#2E7D32", command=self.restaurar_propiedad_papelera).pack(side="left", padx=5)
        ctk.CTkButton(f_btns_pap, text="🚨 Eliminar Definitivamente", fg_color="#D32F2F", command=self.eliminar_definitivamente_inmueble).pack(side="left", padx=5)
        
        self.tree_pap = ttk.Treeview(f_bloque_pap, columns=("ID", "TITULO", "PRECIO"), show="headings")
        for c in ("ID", "TITULO", "PRECIO"): self.tree_pap.heading(c, text=c); self.tree_pap.column(c, anchor="center")
        self.tree_pap.pack(fill="both", expand=True, padx=20, pady=15)

    # ---------------------------------------------------------------------
    # LOGICA LOGÍSTICA COMPLETA Y VALIDACIONES ARREGLADAS
    # ---------------------------------------------------------------------
    def cargar_fotos_dialogo_alta(self):
        archivos = filedialog.askopenfilenames(title="Seleccionar Imágenes", filetypes=[("Imágenes", "*.jpg *.jpeg *.png")])
        if archivos:
            self.rutas_fotos_temporales = list(archivos)
            self.lbl_fotos_info.configure(text=f"Fotos Cargadas: {len(self.rutas_fotos_temporales)}")

    def procesar_guardar_inmueble(self):
        try:
            precio = float(self.txt_prc.get().strip())
            m2_t = float(self.txt_m2t.get().strip())
            m2_c = float(self.txt_m2c.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Precio, M2 Terreno y M2 Construcción requieren números reales.")
            return

        if not self.txt_tit.get().strip() or not self.txt_col.get().strip():
            messagebox.showwarning("Atención", "Título comercial y Colonia son obligatorios.")
            return

        id_ub = db.obtener_o_crear_ubicacion(self.txt_col.get().strip(), self.txt_mun.get().strip(), self.txt_est.get().strip())
        id_ase = self.obtener_id_asesor_por_nombre(self.cmb_ase_inm.get())

        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inmuebles (tipo_operacion, tipo_inmueble, titulo, precio, id_ubicacion, descripcion, m2_terreno, m2_construccion, id_asesor, eliminado)
                VALUES (?,?,?,?,?,?,?,?,?,0)
            """, (self.cmb_op.get(), self.cmb_tipo.get(), self.txt_tit.get().strip(), precio, id_ub, self.txt_desc.get().strip(), m2_t, m2_c, id_ase))
            id_nuevo_inm = cursor.lastrowid

            carpeta_propiedad = f"fotos/propiedad_{id_nuevo_inm}"
            os.makedirs(carpeta_propiedad, exist_ok=True)

            for idx, ruta_orig in enumerate(self.rutas_fotos_temporales):
                ext = os.path.splitext(ruta_orig)[1]
                nombre_destino = f"{carpeta_propiedad}/inm_{id_nuevo_inm}_{idx}{ext}"
                try:
                    shutil.copy(ruta_orig, nombre_destino)
                    es_principal = 1 if idx == 0 else 0
                    cursor.execute("INSERT INTO fotos_inmueble (id_inmueble, ruta_archivo, principal) VALUES (?,?,?)", (id_nuevo_inm, nombre_destino, es_principal))
                except: pass
            conn.commit()

        messagebox.showinfo("Éxito", f"Inmueble ID #{id_nuevo_inm} guardado e indexado por carpeta.")
        for x in [self.txt_tit, self.txt_prc, self.txt_col, self.txt_mun, self.txt_est, self.txt_m2t, self.txt_m2c, self.txt_desc]: x.delete(0, 'end')
        self.rutas_fotos_temporales = []
        self.lbl_fotos_info.configure(text="Fotos Cargadas: 0")

    def procesar_guardar_cliente(self):
        nombre = self.txt_nom_cli.get().strip()
        telefono = self.txt_tel_cli.get().strip()
        correo = self.txt_cor_cli.get().strip()
        colonia = self.txt_col_cli.get().strip()

        if not telefono.isdigit() or len(telefono) != 10:
            messagebox.showerror("Error de Formato", "El campo de teléfono debe ser obligatoriamente un número de 10 dígitos.")
            return
        if "@" not in correo or "." not in correo:
            messagebox.showerror("Error de Formato", "Ingrese una dirección de correo electrónico válida.")
            return
        if not nombre or not colonia:
            messagebox.showwarning("Atención", "Los campos Nombre y Colonia son requeridos.")
            return

        try: pres = float(self.txt_pres_cli.get().strip())
        except: pres = 0.0

        id_ub = db.obtener_o_crear_ubicacion(colonia, "Por definir", "Por definir")
        id_ase = self.obtener_id_asesor_por_nombre(self.cmb_ase_cli.get())

        with db.conectar_bd() as conn:
            conn.cursor().execute("""
                INSERT INTO clientes (nombre, telephone, correo, presupuesto_max, id_ubicacion_interes, tipo_buscado, id_asesor)
                VALUES (?,?,?,?,?,?,?)
            """, (nombre, telefono, correo, pres, id_ub, self.cmb_tipo_cli.get(), id_ase))
            conn.commit()

        messagebox.showinfo("Éxito", f"Cliente '{nombre}' dado de alta exitosamente.")
        for x in [self.txt_nom_cli, self.txt_tel_cli, self.txt_cor_cli, self.txt_pres_cli, self.txt_col_cli]: x.delete(0, 'end')

    def eliminar_clientes_duplicados(self):
        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clientes WHERE id_cliente NOT IN (SELECT MIN(id_cliente) FROM clientes GROUP BY nombre, telephone, correo)")
            afectados = conn.total_changes
            conn.commit()
        messagebox.showinfo("Limpieza Exitosa", f"Se eliminaron {afectados} registros duplicados idénticos.")

    def agregar_asesor(self):
        nombre = self.txt_n_as.get().strip()
        empresa = self.txt_emp_as.get().strip()
        tel = self.txt_t_as.get().strip()
        correo = self.txt_c_as.get().strip()

        if not nombre or not empresa:
            messagebox.showerror("Campos Vacíos", "Los campos Nombre Completo y Empresa no deben ir vacíos.")
            return
        if not tel.isdigit() or len(tel) != 10:
            messagebox.showerror("Error de Formato", "El campo Teléfono debe ser estrictamente de 10 dígitos numéricos.")
            return
        if "@" not in correo or "." not in correo:
            messagebox.showerror("Error de Formato", "Formato de Correo Electrónico inválido.")
            return

        with db.conectar_bd() as conn:
            conn.cursor().execute("INSERT INTO asesores (nombre, telephone, correo, activo) VALUES (?,?,?,1)", (f"{nombre} ({empresa})", tel, correo))
            conn.commit()

        messagebox.showinfo("Éxito", "Asesor guardado correctamente.")
        for x in [self.txt_n_as, self.txt_emp_as, self.txt_t_as, self.txt_c_as]: x.delete(0, 'end')
        self.actualizar_tabla_asesores()

    def eliminar_asesor_seguro(self):
        sel = self.tree_as.selection()
        if not sel: return
        id_as = self.tree_as.item(sel[0], "values")[0]
        if int(id_as) == 1:
            messagebox.showerror("Denegado", "El asesor número 1 primario del sistema no puede ser removido.")
            return

        if messagebox.askyesno("Confirmar", "Se reasignarán propiedades y clientes activos al Asesor Raíz para evitar huérfanos. ¿Proceder?"):
            with db.conectar_bd() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE inmuebles SET id_asesor = 1 WHERE id_asesor = ?", (id_as,))
                cursor.execute("UPDATE clientes SET id_asesor = 1 WHERE id_asesor = ?", (id_as,))
                cursor.execute("DELETE FROM asesores WHERE id_asesor = ?", (id_as,))
                conn.commit()
            self.actualizar_tabla_asesores()

    def actualizar_tabla_asesores(self):
        for item in self.tree_as.get_children(): self.tree_as.delete(item)
        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_asesor, nombre, telephone, correo FROM asesores WHERE activo = 1")
            for row in cursor.fetchall(): self.tree_as.insert("", "end", values=row)
        
        lista = []
        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM asesores")
            lista = [r[0] for r in cursor.fetchall()]
        if lista:
            self.cmb_ase_inm.configure(values=lista)
            self.cmb_ase_cli.configure(values=lista)

    def actualizar_agenda_datos(self):
        for item in self.tree_age.get_children(): self.tree_age.delete(item)
        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_cliente, nombre FROM clientes")
            clis = [f"{r[0]}- {r[1]}" for r in cursor.fetchall()]
            cursor.execute("SELECT id_inmueble, titulo FROM inmuebles WHERE eliminado=0")
            inms = [f"{r[0]}- {r[1]}" for r in cursor.fetchall()]
            
        if clis: self.cmb_age_cli.configure(values=clis)
        if inms: self.cmb_age_inm.configure(values=inms)

        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id_cita, cl.nombre, i.titulo, c.fecha_hora, c.nota 
                FROM citas c JOIN clientes cl ON c.id_cliente = cl.id_cliente JOIN inmuebles i ON c.id_inmueble = i.id_inmueble
            """)
            for row in cursor.fetchall(): self.tree_age.insert("", "end", values=row)

    def registrar_cita_agenda(self):
        if not self.cmb_age_cli.get() or not self.cmb_age_inm.get(): return
        id_c = self.cmb_age_cli.get().split("-")[0].strip()
        id_i = self.cmb_age_inm.get().split("-")[0].strip()
        fecha_completa = f"{self.cal.get_date()} {self.cmb_h.get()}:{self.cmb_m.get()}"
        
        with db.conectar_bd() as conn:
            conn.cursor().execute("INSERT INTO citas (id_cliente, id_inmueble, fecha_hora, nota, id_asesor) VALUES (?,?,?,?,1)",
                           (id_c, id_i, fecha_completa, self.txt_nota_cita.get().strip()))
            conn.commit()
        self.actualizar_agenda_datos()

    def modificar_fecha_cita(self):
        sel = self.tree_age.selection()
        if not sel: return
        id_cita = self.tree_age.item(sel[0], "values")[0]
        nueva_fecha_hora = f"{self.cal.get_date()} {self.cmb_h.get()}:{self.cmb_m.get()}"
        with db.conectar_bd() as conn:
            conn.cursor().execute("UPDATE citas SET fecha_hora = ? WHERE id_cita = ?", (nueva_fecha_hora, id_cita))
            conn.commit()
        self.actualizar_agenda_datos()
        messagebox.showinfo("Éxito", "La cita cambió su horario de visita.")

    def eliminar_cita(self):
        sel = self.tree_age.selection()
        if not sel: return
        id_cita = self.tree_age.item(sel[0], "values")[0]
        if messagebox.askyesno("Confirmar", "¿Eliminar cita de la agenda?"):
            with db.conectar_bd() as conn:
                conn.cursor().execute("DELETE FROM citas WHERE id_cita = ?", (id_cita,))
                conn.commit()
            self.actualizar_agenda_datos()

    def actualizar_tabla_papelera(self):
        for item in self.tree_pap.get_children(): self.tree_pap.delete(item)
        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_inmueble, titulo, precio FROM inmuebles WHERE eliminado = 1")
            for row in cursor.fetchall(): self.tree_pap.insert("", "end", values=row)

    def restaurar_propiedad_papelera(self):
        sel = self.tree_pap.selection()
        if not sel: return
        id_inm = self.tree_pap.item(sel[0], "values")[0]
        with db.conectar_bd() as conn:
            conn.cursor().execute("UPDATE inmuebles SET eliminado = 0 WHERE id_inmueble = ?", (id_inm,))
            conn.commit()
        self.actualizar_tabla_papelera()

    def eliminar_definitivamente_inmueble(self):
        sel = self.tree_pap.selection()
        if not sel: return
        id_inm = self.tree_pap.item(sel[0], "values")[0]

        if messagebox.askyesno("PELIGRO", "Esta acción purgará el inmueble y borrará físicamente sus imágenes. ¿Continuar?"):
            carpeta_prop = f"fotos/propiedad_{id_inm}"
            if os.path.exists(carpeta_prop):
                try: shutil.rmtree(carpeta_prop)
                except: pass

            with db.conectar_bd() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM fotos_inmueble WHERE id_inmueble = ?", (id_inm,))
                cursor.execute("DELETE FROM citas WHERE id_inmueble = ?", (id_inm,))
                cursor.execute("DELETE FROM inmuebles WHERE id_inmueble = ?", (id_inm,))
                conn.commit()
            self.actualizar_tabla_papelera()

    def obtener_id_asesor_por_nombre(self, nombre_completo):
        try:
            with db.conectar_bd() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id_asesor FROM asesores WHERE nombre = ?", (nombre_completo,))
                res = cursor.fetchone()
                return res[0] if res else 1
        except: return 1

    # ---------------------------------------------------------------------
    # VENTANA: BUSCADOR DE INVENTARIO OPERATIVO (FILTRO MANUAL + INMEDIATO)
    # ---------------------------------------------------------------------
    def mostrar_inventario(self):
        if self.ventana_inventario and self.ventana_inventario.winfo_exists():
            self.ventana_inventario.focus()
            return

        self.ventana_inventario = ctk.CTkToplevel(self)
        self.ventana_inventario.title("Buscador Operativo Avanzado")
        self.ventana_inventario.geometry("1280x680")

        frame_filtros = ctk.CTkFrame(self.ventana_inventario, fg_color="white", border_width=1, border_color="#E0E0E0")
        frame_filtros.pack(fill="x", padx=15, pady=10)

        # PUNTO 4: Campos de filtrado en el orden exacto solicitado
        cmb_f_tipo = ctk.CTkComboBox(frame_filtros, values=["Todos", "Casa", "Departamento", "Terreno", "Local", "Oficina"], width=130)
        cmb_f_tipo.pack(side="left", padx=5, pady=8)

        cmb_f_op = ctk.CTkComboBox(frame_filtros, values=["Todos", "VENTA", "RENTA"], width=110)
        cmb_f_op.pack(side="left", padx=5, pady=8)

        txt_f_precio = ctk.CTkEntry(frame_filtros, placeholder_text="Precio Max...", width=110)
        txt_f_precio.pack(side="left", padx=5, pady=8)

        txt_f_m2t = ctk.CTkEntry(frame_filtros, placeholder_text="M2 Terreno Min...", width=120)
        txt_f_m2t.pack(side="left", padx=5, pady=8)

        txt_f_m2c = ctk.CTkEntry(frame_filtros, placeholder_text="M2 Const Min...", width=120)
        txt_f_m2c.pack(side="left", padx=5, pady=8)

        txt_buscar_col = ctk.CTkEntry(frame_filtros, placeholder_text="Filtrar Colonia...", width=140)
        txt_buscar_col.pack(side="left", padx=5, pady=8)

        frame_tabla = ctk.CTkFrame(self.ventana_inventario)
        frame_tabla.pack(fill="both", expand=True, padx=15, pady=5)

        cols = ("ID", "OPERACION", "TIPO", "TITULO", "PRECIO", "M2 TERRENO", "M2 CONST", "COLONIA", "ESTATUS")
        tree = ttk.Treeview(frame_tabla, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c); tree.column(c, anchor="center", width=110)
        tree.pack(fill="both", expand=True)

        def ejecutar_busqueda_automatica(*args):
            for item in tree.get_children(): tree.delete(item)
            query = """
                SELECT i.id_inmueble, i.tipo_operacion, i.tipo_inmueble, i.titulo, i.precio, i.m2_terreno, i.m2_construccion, u.colonia,
                CASE WHEN i.eliminado = 2 THEN 'Vendido/Rentado' ELSE 'Disponible' END
                FROM inmuebles i JOIN ubicaciones u ON i.id_ubicacion = u.id_ubicacion WHERE i.eliminado != 1 AND u.colonia LIKE ?
            """
            params = [f"%{txt_buscar_col.get().strip()}%"]

            if cmb_f_tipo.get() != "Todos":
                query += " AND i.tipo_inmueble = ?"; params.append(cmb_f_tipo.get())
            if cmb_f_op.get() != "Todos":
                query += " AND i.tipo_operacion = ?"; params.append(cmb_f_op.get())
            if txt_f_precio.get().strip():
                try: query += " AND i.precio <= ?"; params.append(float(txt_f_precio.get().strip()))
                except: pass
            if txt_f_m2t.get().strip():
                try: query += " AND i.m2_terreno >= ?"; params.append(float(txt_f_m2t.get().strip()))
                except: pass
            if txt_f_m2c.get().strip():
                try: query += " AND i.m2_construccion >= ?"; params.append(float(txt_f_m2c.get().strip()))
                except: pass

            with db.conectar_bd() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                for row in cursor.fetchall(): tree.insert("", "end", values=row)

        # PUNTO 5 RESTAURADO: Reincorporación del primer botón de filtrado manual en el layout
        btn_filtrar = ctk.CTkButton(frame_filtros, text="🔍 Filtrar", command=ejecutar_busqueda_automatica, fg_color="#1A237E", width=90)
        btn_filtrar.pack(side="left", padx=10)

        # PUNTO 16: Refresco inmediato automatizado al teclear o cambiar selecciones
        txt_buscar_col.bind("<KeyRelease>", ejecutar_busqueda_automatica)
        txt_f_precio.bind("<KeyRelease>", ejecutar_busqueda_automatica)
        txt_f_m2t.bind("<KeyRelease>", ejecutar_busqueda_automatica)
        txt_f_m2c.bind("<KeyRelease>", ejecutar_busqueda_automatica)
        cmb_f_tipo.configure(command=ejecutar_busqueda_automatica)
        cmb_f_op.configure(command=ejecutar_busqueda_automatica)

        ejecutar_busqueda_automatica()

        f_ops = ctk.CTkFrame(self.ventana_inventario, fg_color="transparent")
        f_ops.pack(fill="x", padx=15, pady=10)

        def abrir_ficha_edicion():
            sel = tree.selection()
            if not sel: return
            self.lanzar_ventana_detalle_edicion(tree.item(sel[0], "values")[0], ejecutar_busqueda_automatica)

        def marcar_como_vendido_ya():
            sel = tree.selection()
            if not sel: return
            id_inm = tree.item(sel[0], "values")[0]
            with db.conectar_bd() as conn:
                conn.cursor().execute("UPDATE inmuebles SET eliminado = 2 WHERE id_inmueble = ?", (id_inm,))
                conn.commit()
            ejecutar_busqueda_automatica()

        def mover_a_papelera_temporal():
            sel = tree.selection()
            if not sel: return
            id_inm = tree.item(sel[0], "values")[0]
            if messagebox.askyesno("Confirmar", "¿Mover inmueble a la papelera?"):
                with db.conectar_bd() as conn:
                    conn.cursor().execute("UPDATE inmuebles SET eliminado = 1 WHERE id_inmueble = ?", (id_inm,))
                    conn.commit()
                ejecutar_busqueda_automatica()

        ctk.CTkButton(f_ops, text="👁️ Ver Detalles / Editar Todo", fg_color="#1976D2", command=abrir_ficha_edicion).pack(side="left", padx=5)
        ctk.CTkButton(f_ops, text="🤝 Marcar Vendido / Rentado", fg_color="#2E7D32", command=marcar_como_vendido_ya).pack(side="left", padx=5)
        ctk.CTkButton(f_ops, text="🗑️ Mover a Papelera", fg_color="#C62828", command=mover_a_papelera_temporal).pack(side="left", padx=5)

    # ---------------------------------------------------------------------
    # WINDOW: DETALLE / CONTROL INTERNO COMPLETO
    # ---------------------------------------------------------------------
    def lanzar_ventana_detalle_edicion(self, id_inmueble, callback_recarga):
        v_det = ctk.CTkToplevel(self)
        v_det.title(f"Ficha de Control Interno - ID #{id_inmueble}")
        v_det.geometry("900x740")
        v_det.grab_set()

        self.fotos_db_local = []
        self.indice_foto_actual = 0

        def cargar_fotos_desde_bd():
            with db.conectar_bd() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id_foto, ruta_archivo, principal FROM fotos_inmueble WHERE id_inmueble=? ORDER BY principal DESC, id_foto ASC", (id_inmueble,))
                self.fotos_db_local = cursor.fetchall()

        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.titulo, i.precio, u.colonia, u.municipio, i.descripcion, i.m2_terreno, i.m2_construccion, i.tipo_operacion, i.tipo_inmueble, u.estado 
                FROM inmuebles i JOIN ubicaciones u ON i.id_ubicacion = u.id_ubicacion WHERE i.id_inmueble=?
            """, (id_inmueble,))
            r = cursor.fetchone()
        
        cargar_fotos_desde_bd()

        scroll_izq = ctk.CTkScrollableFrame(v_det, fg_color="transparent")
        scroll_izq.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        f_der = ctk.CTkFrame(v_det, width=360, fg_color="#ECEFF1")
        f_der.pack(side="right", fill="y", padx=15, pady=15)

# Campos Homologados a Pantalla de Alta de Inmuebles
        def agregar_campo_scroll(texto):
            f = ctk.CTkFrame(scroll_izq, fg_color="transparent")
            f.pack(fill="x", pady=4)
            # SE CORRIGE EL ANCHOR DE "w btn" A "w"
            ctk.CTkLabel(f, text=texto, font=("Arial", 12, "bold"), width=150, anchor="w").pack(side="left")
            return f

        e_op = ctk.CTkComboBox(agregar_campo_scroll("Tipo Operación:"), values=["VENTA", "RENTA"], width=280); e_op.pack(side="left"); e_op.set(r[7])
        e_tipo = ctk.CTkComboBox(agregar_campo_scroll("Tipo Inmueble:"), values=["Casa", "Departamento", "Terreno", "Local", "Oficina"], width=280); e_tipo.pack(side="left"); e_tipo.set(r[8])
        e_tit = ctk.CTkEntry(agregar_campo_scroll("Título Comercial:"), width=400); e_tit.pack(side="left"); e_tit.insert(0, str(r[0]))
        e_prc = ctk.CTkEntry(agregar_campo_scroll("Precio:"), width=280); e_prc.pack(side="left"); e_prc.insert(0, str(r[1]))
        e_col = ctk.CTkEntry(agregar_campo_scroll("Colonia:"), width=350); e_col.pack(side="left"); e_col.insert(0, str(r[2]))
        e_mun = ctk.CTkEntry(agregar_campo_scroll("Municipio / Alc:"), width=350); e_mun.pack(side="left"); e_mun.insert(0, str(r[3]))
        e_est = ctk.CTkEntry(agregar_campo_scroll("Estado:"), width=350); e_est.pack(side="left"); e_est.insert(0, str(r[9]))
        e_m2t = ctk.CTkEntry(agregar_campo_scroll("M² Terreno:"), width=180); e_m2t.pack(side="left"); e_m2t.insert(0, str(r[5]))
        e_m2c = ctk.CTkEntry(agregar_campo_scroll("M² Construcción:"), width=180); e_m2c.pack(side="left"); e_m2c.insert(0, str(r[6]))
        e_des = ctk.CTkEntry(agregar_campo_scroll("Descripción / Notas:"), width=400); e_des.pack(side="left"); e_des.insert(0, str(r[4]))

        lbl_canvas_foto = ctk.CTkLabel(f_der, text="[ Sin Fotografía ]")
        lbl_canvas_foto.pack(pady=(20, 5), padx=10)
        lbl_status_foto = ctk.CTkLabel(f_der, text="", font=("Arial", 11, "italic"), text_color="gray")
        lbl_status_foto.pack()

        def renderizar_foto_indice():
            if not self.fotos_db_local:
                lbl_canvas_foto.configure(image=None, text="[ Sin Fotografía ]")
                lbl_status_foto.configure(text="")
                return
            if self.indice_foto_actual >= len(self.fotos_db_local): self.indice_foto_actual = 0
            id_f, ruta, es_principal = self.fotos_db_local[self.indice_foto_actual]
            if os.path.exists(ruta):
                try:
                    img_pil = PILImage.open(ruta)
                    img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(280, 200))
                    lbl_canvas_foto.configure(image=img_ctk, text="")
                    lbl_canvas_foto.image = img_ctk
                    texto = f"Foto {self.indice_foto_actual + 1} de {len(self.fotos_db_local)}"
                    if es_principal: texto += " ⭐ [PORTADA]"
                    lbl_status_foto.configure(text=texto)
                except Exception as e:
                    print(f"Error al renderizar imagen: {e}")

        renderizar_foto_indice()

        f_nav = ctk.CTkFrame(f_der, fg_color="transparent")
        f_nav.pack(pady=5)
        ctk.CTkButton(f_nav, text="◀", width=40, command=lambda: [setattr(self, 'indice_foto_actual', (self.indice_foto_actual - 1) % len(self.fotos_db_local)) if self.fotos_db_local else None, renderizar_foto_indice()]).pack(side="left", padx=5)
        ctk.CTkButton(f_nav, text="▶", width=40, command=lambda: [setattr(self, 'indice_foto_actual', (self.indice_foto_actual + 1) % len(self.fotos_db_local)) if self.fotos_db_local else None, renderizar_foto_indice()]).pack(side="left", padx=5)

        # -------------------------------------------------------------
        # PRIMERO SE DECLARA EL CONTENEDOR (Arregla el NameError)
        # -------------------------------------------------------------
        f_gestion_fotos = ctk.CTkFrame(f_der, fg_color="transparent")
        f_gestion_fotos.pack(pady=10, fill="x", padx=20)

        # -------------------------------------------------------------
        # SEGUNDO: LA FUNCIÓN QUE USA EL CONTENEDOR O LOS ELEMENTOS
        # -------------------------------------------------------------
        def agregar_nuevas_fotos_a_propiedad():
            archivos = filedialog.askopenfilenames(title="Añadir Imágenes", filetypes=[("Imágenes", "*.jpg *.jpeg *.png")])
            if archivos:
                carpeta_prop = f"fotos/propiedad_{id_inmueble}"
                os.makedirs(carpeta_prop, exist_ok=True)
                with db.conectar_bd() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM fotos_inmueble WHERE id_inmueble=?", (id_inmueble,))
                    conteo = cursor.fetchone()[0]
                    for idx, ruta_orig in enumerate(archivos):
                        ext = os.path.splitext(ruta_orig)[1]
                        nombre_destino = f"{carpeta_prop}/inm_{id_inmueble}_add_{conteo + idx}{ext}"
                        try:
                            shutil.copy(ruta_orig, nombre_destino)
                            cursor.execute("INSERT INTO fotos_inmueble (id_inmueble, ruta_archivo, principal) VALUES (?,?,0)", (id_inmueble, nombre_destino))
                        except: print("Error de guardado")
                    conn.commit()
                cargar_fotos_desde_bd()
                renderizar_foto_indice()

        # -------------------------------------------------------------
        # TERCERO: AHORA SÍ SE CREA EL BOTÓN DENTRO DE f_gestion_fotos
        # -------------------------------------------------------------
        ctk.CTkButton(f_gestion_fotos, text="📷 Añadir Fotos", fg_color="#5C6BC0", command=agregar_nuevas_fotos_a_propiedad).pack(fill="x", pady=3)

        # -------------------------------------------------------------
        # NUEVA FUNCIÓN: ASIGNAR PORTADA PRINCIPAL (⭐)
        # -------------------------------------------------------------
        def asignar_foto_portada_actual():
            if not self.fotos_db_local:
                messagebox.showwarning("Atención", "No hay fotografías en este inmueble para asignar como portada.")
                return
            
            # Obtenemos los datos de la foto que está actualmente en pantalla
            id_f, ruta, es_principal = self.fotos_db_local[self.indice_foto_actual]
            
            with db.conectar_bd() as conn:
                cursor = conn.cursor()
                # 1. Ponemos en 0 todas las fotos de este inmueble
                cursor.execute("UPDATE fotos_inmueble SET principal = 0 WHERE id_inmueble = ?", (id_inmueble,))
                # 2. Ponemos en 1 únicamente la foto seleccionada actual
                cursor.execute("UPDATE fotos_inmueble SET principal = 1 WHERE id_foto = ?", (id_f,))
                conn.commit()
            
            messagebox.showinfo("Éxito", "Esta imagen ha sido establecida como la portada oficial.")
            
            # Recargamos la lista local de fotos para que refleje el cambio de la estrella ⭐ inmediatamente
            cargar_fotos_desde_bd()
            renderizar_foto_indice()

        # -------------------------------------------------------------
        # NUEVO BOTÓN: ESTABLECER COMO PORTADA
        # -------------------------------------------------------------
        ctk.CTkButton(f_gestion_fotos, text="⭐ Seleccionar como Portada", fg_color="#F57C00", command=asignar_foto_portada_actual).pack(fill="x", pady=3)

        def guardar_cambios_update():
            id_ub = db.obtener_o_crear_ubicacion(e_col.get().strip(), e_mun.get().strip(), e_est.get().strip())
            with db.conectar_bd() as conn:
                conn.cursor().execute("""
                    UPDATE inmuebles SET tipo_operacion=?, tipo_inmueble=?, titulo=?, precio=?, id_ubicacion=?, descripcion=?, m2_terreno=?, m2_construccion=? WHERE id_inmueble=?
                """, (e_op.get(), e_tipo.get(), e_tit.get().strip(), float(e_prc.get()), id_ub, e_des.get().strip(), float(e_m2t.get()), float(e_m2c.get()), id_inmueble))
                conn.commit()
            callback_recarga()
            v_det.destroy()
            messagebox.showinfo("Éxito", "Todos los campos de la propiedad modificados correctamente.")

        def disparar_pdf_hilo():
            datos_pdf = {
                'titulo': e_tit.get(), 'operacion': e_op.get(), 'tipo': e_tipo.get(),
                'precio': float(e_prc.get()), 'colonia': e_col.get(),
                'municipio': e_mun.get(), 'estado': e_est.get(), 'm2t': float(e_m2t.get()), 'm2c': float(e_m2c.get()), 'descripcion': e_des.get()
            }
            ruta_foto = self.fotos_db_local[0][1] if self.fotos_db_local else None
            archivo_res = pdf_generator.construir_pdf_propiedad(id_inmueble, datos_pdf, ruta_foto)
            messagebox.showinfo("Éxito", f"Ficha Premium generada en /pdfs:\n{archivo_res}")

        ctk.CTkButton(scroll_izq, text="💾 Guardar Cambios Integrales", fg_color="#2E7D32", height=40, command=guardar_cambios_update).pack(pady=15, fill="x")
        ctk.CTkButton(scroll_izq, text="📄 Exportar a Ficha PDF Premium", fg_color="#1A237E", command=disparar_pdf_hilo).pack(fill="x", pady=5)

# =====================================================================
    # VENTANA: BUSCADOR DE PROSPECTOS OPERATIVO
    # =====================================================================
    def mostrar_buscador_prospectos(self):
        self.ventana_prospectos = ctk.CTkToplevel(self)
        self.ventana_prospectos.title("Buscador Operativo de Prospectos")
        self.ventana_prospectos.geometry("1100x600")

        frame_filtros = ctk.CTkFrame(self.ventana_prospectos, fg_color="white", border_width=1, border_color="#E0E0E0")
        frame_filtros.pack(fill="x", padx=15, pady=10)

        txt_buscar_nom = ctk.CTkEntry(frame_filtros, placeholder_text="Buscar por nombre...", width=250)
        txt_buscar_nom.pack(side="left", padx=5, pady=8)

        cmb_f_tipo = ctk.CTkComboBox(frame_filtros, values=["Todos", "Casa", "Departamento", "Terreno", "Local", "Oficina"], width=150)
        cmb_f_tipo.pack(side="left", padx=5, pady=8)

        frame_tabla = ctk.CTkFrame(self.ventana_prospectos)
        frame_tabla.pack(fill="both", expand=True, padx=15, pady=5)

        cols = ("ID", "NOMBRE", "TELEFONO", "CORREO", "PRESUPUESTO", "INTERES", "ASESOR")
        tree = ttk.Treeview(frame_tabla, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c); tree.column(c, anchor="center", width=130)
        tree.pack(fill="both", expand=True)

        def ejecutar_busqueda_prospectos(*args):
            for item in tree.get_children(): tree.delete(item)
            query = """
                SELECT c.id_cliente, c.nombre, c.telephone, c.correo, c.presupuesto_max, u.colonia, a.nombre
                FROM clientes c 
                JOIN ubicaciones u ON c.id_ubicacion_interes = u.id_ubicacion
                JOIN asesores a ON c.id_asesor = a.id_asesor
                WHERE c.nombre LIKE ?
            """
            params = [f"%{txt_buscar_nom.get().strip()}%"]

            if cmb_f_tipo.get() != "Todos":
                query += " AND c.tipo_buscado = ?"
                params.append(cmb_f_tipo.get())

            with db.conectar_bd() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                for row in cursor.fetchall(): tree.insert("", "end", values=row)

        btn_filtrar = ctk.CTkButton(frame_filtros, text="🔍 Filtrar", command=ejecutar_busqueda_prospectos, fg_color="#1A237E", width=90)
        btn_filtrar.pack(side="left", padx=10)

        txt_buscar_nom.bind("<KeyRelease>", ejecutar_busqueda_prospectos)
        cmb_f_tipo.configure(command=ejecutar_busqueda_prospectos)

        ejecutar_busqueda_prospectos()

        f_ops = ctk.CTkFrame(self.ventana_prospectos, fg_color="transparent")
        f_ops.pack(fill="x", padx=15, pady=10)

        def abrir_edicion_prospecto():
            sel = tree.selection()
            if not sel: return
            self.lanzar_ventana_editar_prospecto(tree.item(sel[0], "values")[0], ejecutar_busqueda_prospectos)

        def eliminar_prospecto_seguro():
            sel = tree.selection()
            if not sel: return
            id_cli = tree.item(sel[0], "values")[0]
            nom_cli = tree.item(sel[0], "values")[1]

            if messagebox.askyesno("Confirmar Borrado", f"¿Está seguro de eliminar de forma permanente al cliente {nom_cli}?\nEsta acción purgará también sus citas agendadas."):
                with db.conectar_bd() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM citas WHERE id_cliente = ?", (id_cli,))
                    cursor.execute("DELETE FROM clientes WHERE id_cliente = ?", (id_cli,))
                    conn.commit()
                ejecutar_busqueda_prospectos()
                messagebox.showinfo("Purgado", "Prospecto eliminado de manera limpia de la base de datos.")

        ctk.CTkButton(f_ops, text="👁️ Editar Prospecto", fg_color="#1976D2", command=abrir_edicion_prospecto).pack(side="left", padx=5)
        ctk.CTkButton(f_ops, text="🗑️ Eliminar de Forma Segura", fg_color="#C62828", command=eliminar_prospecto_seguro).pack(side="left", padx=5)


    # =====================================================================
    # VENTANA MODAL: DETALLE Y EDICIÓN INDIVIDUAL DE PROSPECTO
    # =====================================================================
    def lanzar_ventana_editar_prospecto(self, id_cliente, callback_recarga):
        v_edt = ctk.CTkToplevel(self)
        v_edt.title(f"Modificar Datos del Prospecto - ID #{id_cliente}")
        v_edt.geometry("600x550")
        v_edt.grab_set()

        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.nombre, c.telephone, c.correo, c.presupuesto_max, u.colonia, c.tipo_buscado, a.nombre
                FROM clientes c 
                JOIN ubicaciones u ON c.id_ubicacion_interes = u.id_ubicacion
                JOIN asesores a ON c.id_asesor = a.id_asesor
                WHERE c.id_cliente = ?
            """, (id_cliente,))
            r = cursor.fetchone()

        scroll = ctk.CTkScrollableFrame(v_edt, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(scroll, text="Editar Información del Prospecto", font=("Arial", 16, "bold"), text_color="#1A237E").pack(pady=10, anchor="w", padx=10)

        def agregar_campo(texto):
            f = ctk.CTkFrame(scroll, fg_color="transparent")
            f.pack(fill="x", pady=6, padx=10)
            ctk.CTkLabel(f, text=texto, font=("Arial", 11, "bold"), width=150, anchor="w").pack(side="left")
            return f

        e_nom = ctk.CTkEntry(agregar_campo("Nombre Completo:"), width=300); e_nom.pack(side="left"); e_nom.insert(0, str(r[0]))
        e_tel = ctk.CTkEntry(agregar_campo("Teléfono (10 dgt):"), width=300); e_tel.pack(side="left"); e_tel.insert(0, str(r[1]))
        e_cor = ctk.CTkEntry(agregar_campo("Correo Electrónico:"), width=300); e_cor.pack(side="left"); e_cor.insert(0, str(r[2]))
        e_pre = ctk.CTkEntry(agregar_campo("Presupuesto Máximo:"), width=300); e_pre.pack(side="left"); e_pre.insert(0, str(r[3]))
        e_col = ctk.CTkEntry(agregar_campo("Colonia de Interés:"), width=300); e_col.pack(side="left"); e_col.insert(0, str(r[4]))
        
        e_tipo = ctk.CTkComboBox(agregar_campo("Inmueble Solicitado:"), values=["Casa", "Departamento", "Terreno", "Local", "Oficina"], width=300)
        e_tipo.pack(side="left"); e_tipo.set(r[5])

        # Obtener lista actualizada de asesores para el ComboBox
        lista_asesores = []
        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM asesores")
            lista_asesores = [row[0] for row in cursor.fetchall()]

        e_ase = ctk.CTkComboBox(agregar_campo("Asesor Asignado:"), values=lista_asesores, width=300)
        e_ase.pack(side="left"); e_ase.set(r[6])

        def guardar_cambios_prospecto():
            tel_val = e_tel.get().strip()
            cor_val = e_cor.get().strip()
            
            if not tel_val.isdigit() or len(tel_val) != 10:
                messagebox.showerror("Error de Formato", "El teléfono debe tener exactamente 10 dígitos.")
                return
            if "@" not in cor_val or "." not in cor_val:
                messagebox.showerror("Error de Formato", "Ingrese un correo electrónico válido.")
                return

            id_ub = db.obtener_o_crear_ubicacion(e_col.get().strip(), "Por definir", "Por definir")
            id_ase = self.obtener_id_asesor_por_nombre(e_ase.get())

            with db.conectar_bd() as conn:
                conn.cursor().execute("""
                    UPDATE clientes 
                    SET nombre=?, telephone=?, correo=?, presupuesto_max=?, id_ubicacion_interes=?, tipo_buscado=?, id_asesor=?
                    WHERE id_cliente=?
                """, (e_nom.get().strip(), tel_val, cor_val, float(e_pre.get()), id_ub, e_tipo.get(), id_ase, id_cliente))
                conn.commit()

            callback_recarga()
            v_edt.destroy()
            messagebox.showinfo("Éxito", "Los datos del prospecto han sido actualizados de forma segura.")

        ctk.CTkButton(scroll, text="💾 Guardar Cambios del Prospecto", fg_color="#2E7D32", height=38, command=guardar_cambios_prospecto).pack(pady=20, fill="x", padx=10)

if __name__ == "__main__":
    app = SistemaInmobiliarioApp()
    app.mainloop()
