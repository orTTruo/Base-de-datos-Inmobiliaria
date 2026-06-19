import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from PIL import Image as PILImage, ImageTk
from tkcalendar import Calendar

# IMPORTACIÓN DE NUESTROS NUEVOS MÓDULOS
import database_manager as db
import pdf_generator
import crm_manager

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class SistemaInmobiliarioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GRUPO GARANZIA INMOBILIARIA")
        self.geometry("1250x780")
        
        self.ventana_inventario = None
        self.ventana_prospectos = None
        self.rutas_fotos_temporales = []
        self.fotos_db_local = []
        self.indice_foto_actual = 0
        
        # UI Base Layout Novedoso Anteriores
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#1A237E")
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="GARANZIA", font=("Arial", 22, "bold"), text_color="white").pack(pady=30)
        
        ctk.CTkButton(self.sidebar, text="📊 CRM Estadísticas", fg_color="transparent", text_color="white", anchor="w", command=lambda: [self.conmutar_panel(self.frame_crm_dashboard), self.actualizar_metricas_crm()]).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(self.sidebar, text="🏠 Alta Inmueble", fg_color="transparent", text_color="white", anchor="w", command=lambda: self.conmutar_panel(self.frame_alta_inm)).pack(fill="x", padx=15, pady=5) 
        ctk.CTkButton(self.sidebar, text="📈 Consultar Inventario", fg_color="transparent", text_color="white", anchor="w", command=self.mostrar_inventario).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(self.sidebar, text="👥 Registro Prospectos", fg_color="transparent", text_color="white", anchor="w", command=lambda: self.conmutar_panel(self.frame_alta_clientes)).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(self.sidebar, text="🔍 Buscador Prospectos", fg_color="transparent", text_color="white", anchor="w", command=self.mostrar_buscador_prospectos).pack(fill="x", padx=15, pady=5) 
        ctk.CTkButton(self.sidebar, text="💼 Control Asesores", fg_color="transparent", text_color="white", anchor="w", command=lambda: [self.conmutar_panel(self.frame_asesores), self.actualizar_tabla_asesores()]).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(self.sidebar, text="📅 Agenda de Visitas", fg_color="transparent", text_color="white", anchor="w", command=lambda: [self.conmutar_panel(self.frame_agenda), self.actualizar_agenda_datos()]).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(self.sidebar, text="🗑️ Papelera", fg_color="transparent", text_color="white", anchor="w", command=lambda: [self.conmutar_panel(self.frame_papelera), self.actualizar_tabla_papelera()]).pack(fill="x", padx=15, pady=5)

        self.contenedor_principal = ctk.CTkFrame(self, fg_color="#F5F5F5", corner_radius=0)
        self.contenedor_principal.pack(side="right", fill="both", expand=True)
        
        self.crear_paneles_arquitectura()
        self.conmutar_panel(self.frame_alta_inm)

    def conmutar_panel(self, panel):
        for p in [self.frame_alta_inm, self.frame_alta_clientes, self.frame_asesores, self.frame_agenda, self.frame_papelera, self.frame_crm_dashboard]:
            p.pack_forget()
        panel.pack(fill="both", expand=True, padx=25, pady=25)

    def crear_paneles_arquitectura(self):
        # PANEL ALTA INMUEBLE
        self.frame_alta_inm = ctk.CTkScrollableFrame(self.contenedor_principal, fg_color="transparent")
        frame_interior = ctk.CTkFrame(self.frame_alta_inm, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        frame_interior.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame_interior, text="Alta y Registro de Nuevo Inmueble", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=15, padx=20, anchor="w")
        
        def crear_bloque_campo(parent, texto):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(f, text=texto, font=("Arial", 12, "bold"), width=150, anchor="w").pack(side="left")
            return f

        self.cmb_op = ctk.CTkComboBox(crear_bloque_campo(frame_interior, "Tipo Operación:"), values=["VENTA", "RENTA"], width=280); self.cmb_op.pack(side="left")
        self.cmb_tipo = ctk.CTkComboBox(crear_bloque_campo(frame_interior, "Tipo Inmueble:"), values=["Casa", "Departamento", "Terreno", "Local", "Oficina"], width=280); self.cmb_tipo.pack(side="left")
        self.txt_tit = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Título Comercial:"), width=450); self.txt_tit.pack(side="left")
        self.txt_prc = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Precio ($ MXN):"), width=280); self.txt_prc.pack(side="left")
        self.txt_col = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Colonia:"), width=350); self.txt_col.pack(side="left")
        self.txt_mun = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Municipio / Alc:"), width=350); self.txt_mun.pack(side="left")
        self.txt_est = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Estado:"), width=350); self.txt_est.pack(side="left")
        self.txt_m2t = ctk.CTkEntry(crear_bloque_campo(frame_interior, "M² Terreno:"), width=180); self.txt_m2t.pack(side="left")
        self.txt_m2c = ctk.CTkEntry(crear_bloque_campo(frame_interior, "M² Construcción:"), width=180); self.txt_m2c.pack(side="left")
        self.txt_desc = ctk.CTkEntry(crear_bloque_campo(frame_interior, "Descripción:"), width=450); self.txt_desc.pack(side="left")
        self.cmb_ase_inm = ctk.CTkComboBox(crear_bloque_campo(frame_interior, "Asesor Asignado:"), width=350); self.cmb_ase_inm.pack(side="left")

        f_media = ctk.CTkFrame(frame_interior, fg_color="transparent")
        f_media.pack(fill="x", padx=20, pady=15)
        self.lbl_fotos_info = ctk.CTkLabel(f_media, text="Fotos Cargadas: 0", font=("Arial", 12, "italic")); self.lbl_fotos_info.pack(side="left", padx=10)
        ctk.CTkButton(f_media, text="📷 Seleccionar Imágenes", fg_color="#455A64", command=self.cargar_fotos_dialogo_alta).pack(side="left", padx=10)
        ctk.CTkButton(frame_interior, text="💾 Registrar Inmueble", fg_color="#2E7D32", height=40, font=("Arial", 13, "bold"), command=self.procesar_guardar_inmueble).pack(pady=20, padx=20, fill="x")

        # PANEL CRM ESTADÍSTICAS
        self.frame_crm_dashboard = ctk.CTkFrame(self.contenedor_principal, fg_color="transparent")
        f_bloque_crm = ctk.CTkFrame(self.frame_crm_dashboard, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        f_bloque_crm.pack(fill="both", expand=True)
        ctk.CTkLabel(f_bloque_crm, text="Resumen Ejecutivo y Métricas CRM", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=20, padx=25, anchor="w")
        self.f_tarjetas = ctk.CTkFrame(f_bloque_crm, fg_color="transparent"); self.f_tarjetas.pack(fill="both", expand=True, padx=25, pady=10)
        self.lbl_crm_inmuebles = ctk.CTkLabel(self.f_tarjetas, text="", font=("Arial", 14), anchor="w"); self.lbl_crm_inmuebles.pack(fill="x", pady=8, padx=10)
        self.lbl_crm_venta = ctk.CTkLabel(self.f_tarjetas, text="", font=("Arial", 14), anchor="w"); self.lbl_crm_venta.pack(fill="x", pady=8, padx=10)
        self.lbl_crm_renta = ctk.CTkLabel(self.f_tarjetas, text="", font=("Arial", 14), anchor="w"); self.lbl_crm_renta.pack(fill="x", pady=8, padx=10)
        self.lbl_crm_clientes = ctk.CTkLabel(self.f_tarjetas, text="", font=("Arial", 14), anchor="w"); self.lbl_crm_clientes.pack(fill="x", pady=8, padx=10)
        self.lbl_crm_asesores = ctk.CTkLabel(self.f_tarjetas, text="", font=("Arial", 14), anchor="w"); self.lbl_crm_asesores.pack(fill="x", pady=8, padx=10)

        # PANEL REGISTRO DE PROSPECTOS
        self.frame_alta_clientes = ctk.CTkFrame(self.contenedor_principal, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0")
        ctk.CTkLabel(self.frame_alta_clientes, text="Registro de Prospectos", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=20, padx=25, anchor="w")
        def crear_fila_cliente(texto):
            f = ctk.CTkFrame(self.frame_alta_clientes, fg_color="transparent"); f.pack(fill="x", padx=25, pady=6)
            ctk.CTkLabel(f, text=texto, font=("Arial", 12, "bold"), width=180, anchor="w").pack(side="left")
            return f
        self.txt_nom_cli = ctk.CTkEntry(crear_fila_cliente("Nombre del Cliente:"), width=400); self.txt_nom_cli.pack(side="left")
        self.txt_tel_cli = ctk.CTkEntry(crear_fila_cliente("Teléfono Celular (10 dgt):"), width=400); self.txt_tel_cli.pack(side="left")
        self.txt_cor_cli = ctk.CTkEntry(crear_fila_cliente("Correo Electrónico:"), width=400); self.txt_cor_cli.pack(side="left")
        self.txt_pres_cli = ctk.CTkEntry(crear_fila_cliente("Presupuesto Máximo:"), width=400); self.txt_pres_cli.pack(side="left")
        self.txt_col_cli = ctk.CTkEntry(crear_fila_cliente("Colonia de Interés:"), width=400); self.txt_col_cli.pack(side="left")
        self.cmb_tipo_cli = ctk.CTkComboBox(crear_fila_cliente("Inmueble Solicitado:"), values=["Casa", "Departamento", "Terreno", "Local", "Oficina"], width=400); self.cmb_tipo_cli.pack(side="left")
        self.cmb_ase_cli = ctk.CTkComboBox(crear_fila_cliente("Asesor de Seguimiento:"), width=400); self.cmb_ase_cli.pack(side="left")
        f_acts_cli = ctk.CTkFrame(self.frame_alta_clientes, fg_color="transparent"); f_acts_cli.pack(fill="x", padx=25, pady=25)
        ctk.CTkButton(f_acts_cli, text="💾 Registrar Cliente", fg_color="#2E7D32", height=38, command=self.procesar_guardar_cliente).pack(side="left", padx=5)
        ctk.CTkButton(f_acts_cli, text="🧼 Eliminar Clientes Duplicados", fg_color="#78909C", height=38, command=self.eliminar_clientes_duplicados).pack(side="left", padx=5)

        # PANEL ASESORES
        self.frame_asesores = ctk.CTkFrame(self.contenedor_principal, fg_color="transparent")
        f_bloque_as = ctk.CTkFrame(self.frame_asesores, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0"); f_bloque_as.pack(fill="both", expand=True)
        ctk.CTkLabel(f_bloque_as, text="Administración y Control de Asesores", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=15, padx=20, anchor="w")
        f_alta_as = ctk.CTkFrame(f_bloque_as, fg_color="transparent"); f_alta_as.pack(fill="x", padx=20, pady=10)
        self.txt_n_as = ctk.CTkEntry(f_alta_as, placeholder_text="Nombre Completo", width=180); self.txt_n_as.pack(side="left", padx=4)
        self.txt_emp_as = ctk.CTkEntry(f_alta_as, placeholder_text="Empresa", width=140); self.txt_emp_as.pack(side="left", padx=4)
        self.txt_t_as = ctk.CTkEntry(f_alta_as, placeholder_text="Teléfono (10 dgt)", width=140); self.txt_t_as.pack(side="left", padx=4)
        self.txt_c_as = ctk.CTkEntry(f_alta_as, placeholder_text="Correo Válido", width=180); self.txt_c_as.pack(side="left", padx=4)
        ctk.CTkButton(f_alta_as, text="➕ Dar de Alta", command=self.agregar_asesor, fg_color="#1A237E").pack(side="left", padx=4)
        self.tree_as = ttk.Treeview(f_bloque_as, columns=("ID", "NOMBRE", "TELEFONO", "CORREO"), show="headings")
        for c in ("ID", "NOMBRE", "TELEFONO", "CORREO"): self.tree_as.heading(c, text=c); self.tree_as.column(c, anchor="center")
        self.tree_as.pack(fill="both", expand=True, padx=20, pady=15)
        ctk.CTkButton(f_bloque_as, text="🗑️ Eliminar Asesor Seleccionado de Forma Segura", fg_color="#C62828", command=self.eliminar_asesor_seguro).pack(pady=15, padx=20, anchor="w")

        # PANEL AGENDA
        self.frame_agenda = ctk.CTkFrame(self.contenedor_principal, fg_color="transparent")
        f_bloque_ag = ctk.CTkFrame(self.frame_agenda, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0"); f_bloque_ag.pack(fill="both", expand=True)
        ctk.CTkLabel(f_bloque_ag, text="Agenda de Citas Inteligente", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=15, padx=20, anchor="w")
        frame_top_ag = ctk.CTkFrame(f_bloque_ag, fg_color="transparent"); frame_top_ag.pack(fill="x", padx=20)
        f_cal = ctk.CTkFrame(frame_top_ag, fg_color="white", corner_radius=10, border_width=1, border_color="#E0E0E0"); f_cal.pack(side="left", padx=(0, 15))
        self.cal = Calendar(f_cal, selectmode='day', date_pattern='yyyy-mm-dd', background='#1A237E', foreground='white', headersbackground='#ECEFF1', headersforeground='black', selectbackground='#1E88E5', selectforeground='white', normalbackground='white', normalforeground='black', weekendbackground='#F5F5F5', weekendforeground='black')
        self.cal.pack(padx=10, pady=10)
        f_form_ag = ctk.CTkFrame(frame_top_ag, fg_color="transparent"); f_form_ag.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(f_form_ag, text="Seleccionar Cliente Prospecto:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(2,0))
        self.cmb_age_cli = ctk.CTkComboBox(f_form_ag, width=380); self.cmb_age_cli.pack(pady=2, anchor="w")
        ctk.CTkLabel(f_form_ag, text="Seleccionar Propiedad del Inventario:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(2,0))
        self.cmb_age_inm = ctk.CTkComboBox(f_form_ag, width=380); self.cmb_age_inm.pack(pady=2, anchor="w")
        ctk.CTkLabel(f_form_ag, text="Hora de Cita (HH:MM):", font=("Arial", 11, "bold")).pack(anchor="w", pady=(2,0))
        f_hm = ctk.CTkFrame(f_form_ag, fg_color="transparent"); f_hm.pack(pady=2, anchor="w")
        self.cmb_h = ctk.CTkComboBox(f_hm, width=80, values=[f"{i:02d}" for i in range(8, 21)]); self.cmb_h.pack(side="left", padx=2)
        self.cmb_m = ctk.CTkComboBox(f_hm, width=80, values=["00", "15", "30", "45"]); self.cmb_m.pack(side="left", padx=2)
        self.txt_nota_cita = ctk.CTkEntry(f_form_ag, width=380, placeholder_text="Notas especiales..."); self.txt_nota_cita.pack(pady=8, anchor="w")
        ctk.CTkButton(f_form_ag, text="📅 Agendar Nueva Cita", command=self.registrar_cita_agenda, fg_color="#1A237E").pack(pady=4, anchor="w")
        self.tree_age = ttk.Treeview(f_bloque_ag, columns=("ID", "CLIENTE", "INMUEBLE", "FECHA_HORA", "NOTAS"), show="headings")
        for c in ("ID", "CLIENTE", "INMUEBLE", "FECHA_HORA", "NOTAS"): self.tree_age.heading(c, text=c); self.tree_age.column(c, anchor="center")
        self.tree_age.pack(fill="both", expand=True, padx=20, pady=10)
        f_ops_citas = ctk.CTkFrame(f_bloque_ag, fg_color="transparent"); f_ops_citas.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(f_ops_citas, text="⏳ Cambiar Fecha/Hora Cita", fg_color="#F57C00", command=self.modificar_fecha_cita).pack(side="left", padx=5)
        ctk.CTkButton(f_ops_citas, text="❌ Cancelar/Eliminar Cita", fg_color="#D32F2F", command=self.eliminar_cita).pack(side="left", padx=5)

        # PANEL PAPELERA
        self.frame_papelera = ctk.CTkFrame(self.contenedor_principal, fg_color="transparent")
        f_bloque_pap = ctk.CTkFrame(self.frame_papelera, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0"); f_bloque_pap.pack(fill="both", expand=True)
        ctk.CTkLabel(f_bloque_pap, text="Papelera de Reciclaje de Inmuebles", font=("Arial", 20, "bold"), text_color="#1A237E").pack(pady=15, padx=20, anchor="w")
        f_btns_pap = ctk.CTkFrame(f_bloque_pap, fg_color="transparent"); f_btns_pap.pack(fill="x", padx=20)
        ctk.CTkButton(f_btns_pap, text="🔄 Restaurar Propiedad", fg_color="#2E7D32", command=self.restaurar_propiedad_papelera).pack(side="left", padx=5)
        ctk.CTkButton(f_btns_pap, text="🚨 Eliminar Definitivamente", fg_color="#D32F2F", command=self.eliminar_definitivamente_inmueble).pack(side="left", padx=5)
        self.tree_pap = ttk.Treeview(f_bloque_pap, columns=("ID", "TITULO", "PRECIO"), show="headings")
        for c in ("ID", "TITULO", "PRECIO"): self.tree_pap.heading(c, text=c); self.tree_pap.column(c, anchor="center")
        self.tree_pap.pack(fill="both", expand=True, padx=20, pady=15)

    def actualizar_metricas_crm(self):
        # En lugar de asignar textos fijos, le pasamos el contenedor al crm_manager
        crm_manager.construir_tarjetas_crm(self.f_tarjetas)

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

        messagebox.showinfo("Éxito", f"Inmueble ID #{id_nuevo_inm} guardado e indexado.")
        for x in [self.txt_tit, self.txt_prc, self.txt_col, self.txt_mun, self.txt_est, self.txt_m2t, self.txt_m2c, self.txt_desc]: x.delete(0, 'end')
        self.rutas_fotos_temporales = []
        self.lbl_fotos_info.configure(text="Fotos Cargadas: 0")

    def procesar_guardar_cliente(self):
        nombre = self.txt_nom_cli.get().strip()
        telefono = self.txt_tel_cli.get().strip()
        correo = self.txt_cor_cli.get().strip()
        colonia = self.txt_col_cli.get().strip()

        if not telefono.isdigit() or len(telefono) != 10:
            messagebox.showerror("Error de Formato", "El campo de teléfono debe ser un número de 10 dígitos.")
            return
        if "@" not in correo or "." not in correo:
            messagebox.showerror("Error de Formato", "Ingrese un correo electrónico válido.")
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
        messagebox.showinfo("Limpieza", f"Se eliminaron {afectados} duplicados.")

    def agregar_asesor(self):
        nombre = self.txt_n_as.get().strip()
        empresa = self.txt_emp_as.get().strip()
        tel = self.txt_t_as.get().strip()
        correo = self.txt_c_as.get().strip()

        if not tel.isdigit() or len(tel) != 10:
            messagebox.showerror("Error", "Teléfono debe ser de 10 dígitos.")
            return

        with db.conectar_bd() as conn:
            conn.cursor().execute("INSERT INTO asesores (nombre, telephone, correo, activo) VALUES (?,?,?,1)", (f"{nombre} ({empresa})", tel, correo))
            conn.commit()
        self.actualizar_tabla_asesores()

    def eliminar_asesor_seguro(self):
        sel = self.tree_as.selection()
        if not sel: return
        id_as = self.tree_as.item(sel[0], "values")[0]
        if int(id_as) == 1: return

        if messagebox.askyesno("Confirmar", "Se reasignarán elementos al Asesor Raíz. ¿Proceder?"):
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

    def eliminar_cita(self):
        sel = self.tree_age.selection()
        if not sel: return
        id_cita = self.tree_age.item(sel[0], "values")[0]
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

    def mostrar_inventario(self):
        if self.ventana_inventario and self.ventana_inventario.winfo_exists():
            self.ventana_inventario.focus(); return
        self.ventana_inventario = ctk.CTkToplevel(self)
        self.ventana_inventario.title("Buscador Operativo Avanzado")
        self.ventana_inventario.geometry("1280x680")

        frame_filtros = ctk.CTkFrame(self.ventana_inventario, fg_color="white", border_width=1, border_color="#E0E0E0")
        frame_filtros.pack(fill="x", padx=15, pady=10)

        cmb_f_tipo = ctk.CTkComboBox(frame_filtros, values=["Todos", "Casa", "Departamento", "Terreno", "Local", "Oficina"], width=130); cmb_f_tipo.pack(side="left", padx=5, pady=8)
        cmb_f_op = ctk.CTkComboBox(frame_filtros, values=["Todos", "VENTA", "RENTA"], width=110); cmb_f_op.pack(side="left", padx=5, pady=8)
        txt_f_precio = ctk.CTkEntry(frame_filtros, placeholder_text="Precio Max...", width=110); txt_f_precio.pack(side="left", padx=5, pady=8)
        txt_f_m2t = ctk.CTkEntry(frame_filtros, placeholder_text="M2 Terreno Min...", width=120); txt_f_m2t.pack(side="left", padx=5, pady=8)
        txt_f_m2c = ctk.CTkEntry(frame_filtros, placeholder_text="M2 Const Min...", width=120); txt_f_m2c.pack(side="left", padx=5, pady=8)
        txt_buscar_col = ctk.CTkEntry(frame_filtros, placeholder_text="Filtrar Colonia...", width=140); txt_buscar_col.pack(side="left", padx=5, pady=8)

        frame_tabla = ctk.CTkFrame(self.ventana_inventario); frame_tabla.pack(fill="both", expand=True, padx=15, pady=5)
        cols = ("ID", "OPERACION", "TIPO", "TITULO", "PRECIO", "M2 TERRENO", "M2 CONST", "COLONIA", "ESTATUS")
        tree = ttk.Treeview(frame_tabla, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c); tree.column(c, anchor="center", width=110)
        tree.pack(fill="both", expand=True)

        def ejecutar_busqueda_automatica(*args):
            for item in tree.get_children(): tree.delete(item)
            query = "SELECT i.id_inmueble, i.tipo_operacion, i.tipo_inmueble, i.titulo, i.precio, i.m2_terreno, i.m2_construccion, u.colonia, CASE WHEN i.eliminado = 2 THEN 'Vendido/Rentado' ELSE 'Disponible' END FROM inmuebles i JOIN ubicaciones u ON i.id_ubicacion = u.id_ubicacion WHERE i.eliminado != 1 AND u.colonia LIKE ?"
            params = [f"%{txt_buscar_col.get().strip()}%"]
            if cmb_f_tipo.get() != "Todos": query += " AND i.tipo_inmueble = ?"; params.append(cmb_f_tipo.get())
            if cmb_f_op.get() != "Todos": query += " AND i.tipo_operacion = ?"; params.append(cmb_f_op.get())
            
            with db.conectar_bd() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                for row in cursor.fetchall(): tree.insert("", "end", values=row)

        btn_filtrar = ctk.CTkButton(frame_filtros, text="🔍 Filtrar", command=ejecutar_busqueda_automatica, fg_color="#1A237E", width=90); btn_filtrar.pack(side="left", padx=10)
        txt_buscar_col.bind("<KeyRelease>", ejecutar_busqueda_automatica)
        ejecutar_busqueda_automatica()

        f_ops = ctk.CTkFrame(self.ventana_inventario, fg_color="transparent"); f_ops.pack(fill="x", padx=15, pady=10)
        ctk.CTkButton(f_ops, text="👁️ Ver Detalles / Editar Todo", fg_color="#1976D2", command=lambda: self.lanzar_ventana_detalle_edicion(tree.item(tree.selection()[0], "values")[0], ejecutar_busqueda_automatica) if tree.selection() else None).pack(side="left", padx=5)

    def mostrar_buscador_prospectos(self):
        if self.ventana_prospectos and self.ventana_prospectos.winfo_exists():
            self.ventana_prospectos.focus(); return
        self.ventana_prospectos = ctk.CTkToplevel(self)
        self.ventana_prospectos.title("Buscador Operativo de Prospectos")
        self.ventana_prospectos.geometry("1100x600")

        frame_filtros = ctk.CTkFrame(self.ventana_prospectos, fg_color="white", border_width=1, border_color="#E0E0E0")
        frame_filtros.pack(fill="x", padx=15, pady=10)
        txt_buscar_nom = ctk.CTkEntry(frame_filtros, placeholder_text="Buscar por nombre...", width=250); txt_buscar_nom.pack(side="left", padx=5, pady=8)
        cmb_f_tipo = ctk.CTkComboBox(frame_filtros, values=["Todos", "Casa", "Departamento", "Terreno", "Local", "Oficina"], width=150); cmb_f_tipo.pack(side="left", padx=5, pady=8)

        frame_tabla = ctk.CTkFrame(self.ventana_prospectos); frame_tabla.pack(fill="both", expand=True, padx=15, pady=5)
        cols = ("ID", "NOMBRE", "TELEFONO", "CORREO", "PRESUPUESTO", "INTERES", "ASESOR")
        tree = ttk.Treeview(frame_tabla, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c); tree.column(c, anchor="center", width=130)
        tree.pack(fill="both", expand=True)

        def ejecutar_busqueda_prospectos(*args):
            for item in tree.get_children(): tree.delete(item)
            query = "SELECT c.id_cliente, c.nombre, c.telephone, c.correo, c.presupuesto_max, u.colonia, a.nombre FROM clientes c JOIN ubicaciones u ON c.id_ubicacion_interes = u.id_ubicacion JOIN asesores a ON c.id_asesor = a.id_asesor WHERE c.nombre LIKE ?"
            params = [f"%{txt_buscar_nom.get().strip()}%"]
            with db.conectar_bd() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                for row in cursor.fetchall(): tree.insert("", "end", values=row)

        txt_buscar_nom.bind("<KeyRelease>", ejecutar_busqueda_prospectos)
        ejecutar_busqueda_prospectos()
        f_ops = ctk.CTkFrame(self.ventana_prospectos, fg_color="transparent"); f_ops.pack(fill="x", padx=15, pady=10)
        ctk.CTkButton(f_ops, text="👁️ Editar Prospecto", fg_color="#1976D2", command=lambda: self.lanzar_ventana_editar_prospecto(tree.item(tree.selection()[0], "values")[0], ejecutar_busqueda_prospectos) if tree.selection() else None).pack(side="left", padx=5)

    def lanzar_ventana_detalle_edicion(self, id_inmueble, callback_recarga):
        v_det = ctk.CTkToplevel(self); v_det.title(f"Ficha Interna - ID #{id_inmueble}"); v_det.geometry("1100x740"); v_det.grab_set()
        
        def cargar_fotos_desde_bd():
            with db.conectar_bd() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id_foto, ruta_archivo, principal FROM fotos_inmueble WHERE id_inmueble=? ORDER BY principal DESC", (id_inmueble,))
                self.fotos_db_local = cursor.fetchall()

        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT i.titulo, i.precio, u.colonia, u.municipio, i.descripcion, i.m2_terreno, i.m2_construccion, i.tipo_operacion, i.tipo_inmueble, u.estado FROM inmuebles i JOIN ubicaciones u ON i.id_ubicacion = u.id_ubicacion WHERE i.id_inmueble=?", (id_inmueble,))
            r = cursor.fetchone()
        cargar_fotos_desde_bd()

        scroll_izq = ctk.CTkScrollableFrame(v_det, fg_color="transparent"); scroll_izq.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        f_der = ctk.CTkFrame(v_det, width=360, fg_color="#ECEFF1"); f_der.pack(side="right", fill="y", padx=15, pady=15)

        def agregar_campo_scroll(texto):
            f = ctk.CTkFrame(scroll_izq, fg_color="transparent"); f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=texto, font=("Arial", 12, "bold"), width=150, anchor="w").pack(side="left")
            return f

        e_op = ctk.CTkComboBox(agregar_campo_scroll("Tipo Operación:"), values=["VENTA", "RENTA"], width=280); e_op.pack(side="left"); e_op.set(r[7])
        e_tit = ctk.CTkEntry(agregar_campo_scroll("Título Comercial:"), width=400); e_tit.pack(side="left"); e_tit.insert(0, str(r[0]))
        e_prc = ctk.CTkEntry(agregar_campo_scroll("Precio:"), width=280); e_prc.pack(side="left"); e_prc.insert(0, str(r[1]))
        e_col = ctk.CTkEntry(agregar_campo_scroll("Colonia:"), width=350); e_col.pack(side="left"); e_col.insert(0, str(r[2]))
        e_m2t = ctk.CTkEntry(agregar_campo_scroll("M² Terreno:"), width=180); e_m2t.pack(side="left"); e_m2t.insert(0, str(r[5]))
        e_m2c = ctk.CTkEntry(agregar_campo_scroll("M² Construcción:"), width=180); e_m2c.pack(side="left"); e_m2c.insert(0, str(r[6]))
        e_des = ctk.CTkEntry(agregar_campo_scroll("Descripción / Notas:"), width=400); e_des.pack(side="left"); e_des.insert(0, str(r[4]))

        lbl_canvas_foto = ctk.CTkLabel(f_der, text="[ Sin Fotografía ]"); lbl_canvas_foto.pack(pady=(20, 5), padx=10)
        
        def renderizar_foto_indice():
            if not self.fotos_db_local: lbl_canvas_foto.configure(image=None, text="[ Sin Fotografía ]"); return
            id_f, ruta, es_principal = self.fotos_db_local[self.indice_foto_actual]
            if os.path.exists(ruta):
                img_pil = PILImage.open(ruta)
                img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(280, 200))
                lbl_canvas_foto.configure(image=img_ctk, text="")
                lbl_canvas_foto.image = img_ctk

        renderizar_foto_indice()
        f_gestion_fotos = ctk.CTkFrame(f_der, fg_color="transparent"); f_gestion_fotos.pack(pady=10, fill="x", padx=20)
        
        def guardar_cambios_update():
            id_ub = db.obtener_o_crear_ubicacion(e_col.get().strip(), "Por definir", "Por definir")
            with db.conectar_bd() as conn:
                conn.cursor().execute("UPDATE inmuebles SET tipo_operacion=?, titulo=?, precio=?, id_ubicacion=?, descripcion=?, m2_terreno=?, m2_construccion=? WHERE id_inmueble=?", (e_op.get(), e_tit.get().strip(), float(e_prc.get()), id_ub, e_des.get().strip(), float(e_m2t.get()), float(e_m2c.get()), id_inmueble))
                conn.commit()
            callback_recarga(); v_det.destroy()

        def disparar_pdf():
            datos_pdf = {'titulo': e_tit.get(), 'operacion': e_op.get(), 'tipo': "Casa", 'precio': float(e_prc.get()), 'colonia': e_col.get(), 'municipio': "Def", 'estado': "Def", 'm2t': float(e_m2t.get()), 'm2c': float(e_m2c.get()), 'descripcion': e_des.get()}
            ruta_foto = self.fotos_db_local[0][1] if self.fotos_db_local else None
            pdf_generator.construir_pdf_propiedad(id_inmueble, datos_pdf, ruta_foto)

        ctk.CTkButton(scroll_izq, text="💾 Guardar Cambios Integrales", fg_color="#2E7D32", height=40, command=guardar_cambios_update).pack(pady=15, fill="x")
        ctk.CTkButton(scroll_izq, text="📄 Exportar a Ficha PDF Premium", fg_color="#1A237E", command=disparar_pdf).pack(fill="x", pady=5)

    def lanzar_ventana_editar_prospecto(self, id_cliente, callback_recarga):
        v_edt = ctk.CTkToplevel(self); v_edt.title(f"Modificar Datos - ID #{id_cliente}"); v_edt.geometry("600x550"); v_edt.grab_set()
        with db.conectar_bd() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT c.nombre, c.telephone, c.correo, c.presupuesto_max, u.colonia, c.tipo_buscado FROM clientes c JOIN ubicaciones u ON c.id_ubicacion_interes = u.id_ubicacion WHERE c.id_cliente = ?", (id_cliente,))
            r = cursor.fetchone()

        scroll = ctk.CTkScrollableFrame(v_edt, fg_color="white", corner_radius=12, border_width=1, border_color="#E0E0E0"); scroll.pack(fill="both", expand=True, padx=15, pady=15)
        def agregar_campo(texto):
            f = ctk.CTkFrame(scroll, fg_color="transparent"); f.pack(fill="x", pady=6, padx=10)
            ctk.CTkLabel(f, text=texto, font=("Arial", 11, "bold"), width=150, anchor="w").pack(side="left")
            return f
        e_nom = ctk.CTkEntry(agregar_campo("Nombre Completo:"), width=300); e_nom.pack(side="left"); e_nom.insert(0, str(r[0]))
        e_tel = ctk.CTkEntry(agregar_campo("Teléfono:"), width=300); e_tel.pack(side="left"); e_tel.insert(0, str(r[1]))
        e_cor = ctk.CTkEntry(agregar_campo("Correo:"), width=300); e_cor.pack(side="left"); e_cor.insert(0, str(r[2]))
        e_pre = ctk.CTkEntry(agregar_campo("Presupuesto:"), width=300); e_pre.pack(side="left"); e_pre.insert(0, str(r[3]))

        def guardar_cambios_prospecto():
            id_ub = db.obtener_o_crear_ubicacion("General", "Por definir", "Por definir")
            with db.conectar_bd() as conn:
                conn.cursor().execute("UPDATE clientes SET nombre=?, telephone=?, correo=?, presupuesto_max=? WHERE id_cliente=?", (e_nom.get().strip(), e_tel.get().strip(), e_cor.get().strip(), float(e_pre.get()), id_cliente))
                conn.commit()
            callback_recarga(); v_edt.destroy()
        ctk.CTkButton(scroll, text="💾 Guardar Cambios", fg_color="#2E7D32", height=38, command=guardar_cambios_prospecto).pack(pady=20, fill="x", padx=10)

if __name__ == "__main__":
    app = SistemaInmobiliarioApp()
    app.mainloop()
