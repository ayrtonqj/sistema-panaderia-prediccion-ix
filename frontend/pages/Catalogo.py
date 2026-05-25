import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Catálogo | Panadería Victoria", page_icon="📦", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.main{background:#0f1117;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a1f2e,#0d1117);border-right:1px solid #2d3748;}
.badge-ok{background:rgba(52,211,153,0.15);border:1px solid #34d399;border-radius:6px;
          padding:2px 10px;color:#6ee7b7;font-size:0.82rem;display:inline-block;}
.badge-warn{background:rgba(251,191,36,0.15);border:1px solid #fbbf24;border-radius:6px;
            padding:2px 10px;color:#fcd34d;font-size:0.82rem;display:inline-block;}
</style>""", unsafe_allow_html=True)

API = "http://localhost:8000"

CATEGORIAS = ["Pan de mesa", "Pan especial", "Bollería", "Salados", "Pasteles", "Dulces"]
UNIDADES   = ["Kg", "Litros", "Unidades", "Gramos"]

st.markdown("# 📦 Catálogo de Productos e Insumos")
st.markdown("Agrega, edita o elimina productos e insumos del sistema.")

tab_prod, tab_insumos = st.tabs(["🍞 Productos", "🧂 Insumos"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PRODUCTOS
# ══════════════════════════════════════════════════════════════════════════════
with tab_prod:
    sub_ver, sub_agregar = st.tabs(["📋 Ver / Editar", "➕ Agregar Producto"])

    # ── Ver y Editar ──────────────────────────────────────────────────────────
    with sub_ver:
        try:
            productos = requests.get(f"{API}/productos/", timeout=5).json()
        except Exception:
            st.error("⚠️ No se puede conectar con el backend.")
            productos = []

        if not productos:
            st.info("No hay productos registrados. Usa la pestaña **Agregar Producto** para comenzar.")
        else:
            # Tabla resumen
            df_p = pd.DataFrame(productos)
            df_p["margen_%"] = ((df_p["precio"] - df_p["costo"]) / df_p["costo"] * 100).round(1)
            st.dataframe(
                df_p[["nombre", "categoria", "precio", "costo", "margen_%"]],
                column_config={
                    "nombre":    "Producto",
                    "categoria": "Categoría",
                    "precio":    st.column_config.NumberColumn("Precio", format="S/ %.2f"),
                    "costo":     st.column_config.NumberColumn("Costo",  format="S/ %.2f"),
                    "margen_%":  st.column_config.NumberColumn("Margen", format="%.1f%%"),
                },
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("---")
            st.markdown("### Acciones por producto")

            for prod in productos:
                pid = prod["id"]
                with st.expander(f"🍞 **{prod['nombre']}** — {prod['categoria']} | S/ {prod['precio']:.2f}"):
                    col_info, col_edit, col_del = st.columns([4, 1, 1])
                    col_info.markdown(
                        f"Costo: **S/ {prod['costo']:.2f}** | "
                        f"Margen: **{((prod['precio']-prod['costo'])/prod['costo']*100):.1f}%** | "
                        f"ID: `{pid}`"
                    )

                    if col_edit.button("✏️ Editar", key=f"edit_btn_p_{pid}"):
                        st.session_state[f"edit_prod_{pid}"] = not st.session_state.get(f"edit_prod_{pid}", False)
                        st.session_state.pop(f"del_prod_{pid}", None)

                    if col_del.button("🗑️ Eliminar", key=f"del_btn_p_{pid}"):
                        st.session_state[f"del_prod_{pid}"] = not st.session_state.get(f"del_prod_{pid}", False)
                        st.session_state.pop(f"edit_prod_{pid}", None)

                    # ── Formulario de edición inline ─────────────────────────
                    if st.session_state.get(f"edit_prod_{pid}"):
                        st.markdown("##### ✏️ Editar producto")
                        with st.form(key=f"form_edit_p_{pid}"):
                            c1, c2 = st.columns(2)
                            nuevo_nombre = c1.text_input("Nombre", value=prod["nombre"])
                            nueva_cat    = c2.selectbox("Categoría", CATEGORIAS,
                                                        index=CATEGORIAS.index(prod["categoria"])
                                                        if prod["categoria"] in CATEGORIAS else 0)
                            nuevo_precio = c1.number_input("Precio (S/)", value=float(prod["precio"]),
                                                           min_value=0.01, step=0.10, format="%.2f")
                            nuevo_costo  = c2.number_input("Costo (S/)",  value=float(prod["costo"]),
                                                           min_value=0.01, step=0.10, format="%.2f")
                            guardar = st.form_submit_button("💾 Guardar cambios", use_container_width=True)

                        if guardar:
                            payload = {
                                "nombre":    nuevo_nombre,
                                "categoria": nueva_cat,
                                "precio":    nuevo_precio,
                                "costo":     nuevo_costo,
                            }
                            r = requests.put(f"{API}/productos/{pid}", json=payload, timeout=5)
                            if r.status_code == 200:
                                st.success(f"✅ Producto **{nuevo_nombre}** actualizado.")
                                st.session_state.pop(f"edit_prod_{pid}", None)
                                st.rerun()
                            else:
                                st.error(f"Error al actualizar: {r.text}")

                    # ── Confirmación de eliminación ──────────────────────────
                    if st.session_state.get(f"del_prod_{pid}"):
                        st.warning(
                            f"⚠️ ¿Eliminar **{prod['nombre']}**? "
                            "Esta acción no se puede deshacer. Las ventas históricas quedarán sin producto."
                        )
                        confirmar = st.checkbox(
                            "Sí, confirmo la eliminación", key=f"chk_del_p_{pid}"
                        )
                        if confirmar:
                            r = requests.delete(f"{API}/productos/{pid}", timeout=5)
                            if r.status_code == 200:
                                st.success(f"✅ Producto eliminado.")
                                st.session_state.pop(f"del_prod_{pid}", None)
                                st.rerun()
                            else:
                                try:
                                    detail = r.json().get("detail", r.text)
                                except Exception:
                                    detail = r.text
                                st.error(f"No se pudo eliminar: {detail}")

    # ── Agregar Producto ───────────────────────────────────────────────────────
    with sub_agregar:
        st.markdown("### Nuevo Producto")
        st.caption("Completa los campos para registrar un nuevo producto en el catálogo.")

        with st.form("form_nuevo_producto", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nuevo_nombre = c1.text_input("Nombre del producto *", placeholder="Ej: Pan de Yema")
            nueva_cat    = c2.selectbox("Categoría *", CATEGORIAS)
            nuevo_precio = c1.number_input("Precio de venta (S/) *", min_value=0.01,
                                           step=0.10, format="%.2f", value=1.00)
            nuevo_costo  = c2.number_input("Costo de producción (S/) *", min_value=0.01,
                                           step=0.10, format="%.2f", value=0.50)
            crear = st.form_submit_button("➕ Crear Producto", use_container_width=True)

        # Vista previa del margen (fuera del form para que sea reactiva)
        if nuevo_costo > 0:
            margen = ((nuevo_precio - nuevo_costo) / nuevo_costo) * 100
            if margen >= 50:
                st.markdown(f'<span class="badge-ok">Margen estimado: {margen:.1f}% ✅</span>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="badge-warn">Margen estimado: {margen:.1f}% ⚠️ (bajo)</span>',
                            unsafe_allow_html=True)

        if crear:
            if not nuevo_nombre.strip():
                st.error("El nombre del producto es obligatorio.")
            elif nuevo_precio <= nuevo_costo:
                st.error("El precio de venta debe ser mayor al costo de producción.")
            else:
                payload = {
                    "nombre":    nuevo_nombre.strip(),
                    "categoria": nueva_cat,
                    "precio":    nuevo_precio,
                    "costo":     nuevo_costo,
                }
                r = requests.post(f"{API}/productos/", json=payload, timeout=5)
                if r.status_code in [200, 201]:
                    prod_creado = r.json()
                    st.success(
                        f"✅ Producto **{prod_creado['nombre']}** creado con ID `{prod_creado['id']}`."
                    )
                    st.rerun()
                else:
                    try:
                        detail = r.json().get("detail", r.text)
                    except Exception:
                        detail = r.text
                    st.error(f"Error al crear producto: {detail}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — INSUMOS
# ══════════════════════════════════════════════════════════════════════════════
with tab_insumos:
    sub_ver_i, sub_agregar_i = st.tabs(["📋 Ver / Editar", "➕ Agregar Insumo"])

    # Cargar proveedores una vez para ambos sub-tabs
    try:
        proveedores_raw = requests.get(f"{API}/proveedores/", timeout=5).json()
        prov_opciones   = {p["nombre"]: p["id"] for p in proveedores_raw}
        prov_map        = {p["id"]: p["nombre"] for p in proveedores_raw}
    except Exception:
        proveedores_raw = []
        prov_opciones   = {}
        prov_map        = {}

    # ── Ver y Editar ──────────────────────────────────────────────────────────
    with sub_ver_i:
        try:
            insumos = requests.get(f"{API}/insumos/", timeout=5).json()
        except Exception:
            st.error("⚠️ No se puede conectar con el backend.")
            insumos = []

        if not insumos:
            st.info("No hay insumos registrados. Usa la pestaña **Agregar Insumo** para comenzar.")
        else:
            # Tabla resumen
            df_i = pd.DataFrame(insumos)
            df_i["proveedor"]  = df_i["proveedor_id"].map(prov_map).fillna("—")
            df_i["estado"]     = df_i.apply(
                lambda row: "⚠️ Bajo mínimo" if row["stock_actual"] < row["stock_minimo"] else "✅ OK",
                axis=1
            )
            st.dataframe(
                df_i[["nombre", "stock_actual", "stock_minimo", "unidad_medida", "proveedor", "estado"]],
                column_config={
                    "nombre":        "Insumo",
                    "stock_actual":  st.column_config.NumberColumn("Stock Actual", format="%.2f"),
                    "stock_minimo":  st.column_config.NumberColumn("Stock Mínimo", format="%.2f"),
                    "unidad_medida": "Unidad",
                    "proveedor":     "Proveedor Principal",
                    "estado":        "Estado",
                },
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("---")
            st.markdown("### Acciones por insumo")

            for insumo in insumos:
                iid   = insumo["id"]
                alerta = insumo["stock_actual"] < insumo["stock_minimo"]
                icono  = "🔴" if alerta else "🟢"
                prov_nombre = prov_map.get(insumo.get("proveedor_id"), "Sin proveedor")

                with st.expander(
                    f"{icono} **{insumo['nombre']}** — "
                    f"{insumo['stock_actual']} / {insumo['stock_minimo']} {insumo['unidad_medida']}"
                ):
                    col_info, col_edit, col_del = st.columns([4, 1, 1])
                    col_info.markdown(
                        f"Proveedor: **{prov_nombre}** | ID: `{iid}`"
                        + (f" | 🚨 Déficit: {insumo['stock_minimo'] - insumo['stock_actual']:.2f}" if alerta else "")
                    )

                    if col_edit.button("✏️ Editar", key=f"edit_btn_i_{iid}"):
                        st.session_state[f"edit_insumo_{iid}"] = not st.session_state.get(f"edit_insumo_{iid}", False)
                        st.session_state.pop(f"del_insumo_{iid}", None)

                    if col_del.button("🗑️ Eliminar", key=f"del_btn_i_{iid}"):
                        st.session_state[f"del_insumo_{iid}"] = not st.session_state.get(f"del_insumo_{iid}", False)
                        st.session_state.pop(f"edit_insumo_{iid}", None)

                    # ── Formulario de edición inline ─────────────────────────
                    if st.session_state.get(f"edit_insumo_{iid}"):
                        st.markdown("##### ✏️ Editar insumo")
                        # Índice del proveedor actual en el selectbox
                        prov_nombres_list = ["(Sin proveedor)"] + list(prov_opciones.keys())
                        prov_actual_nombre = prov_map.get(insumo.get("proveedor_id"), "(Sin proveedor)")
                        prov_idx = prov_nombres_list.index(prov_actual_nombre) \
                            if prov_actual_nombre in prov_nombres_list else 0

                        with st.form(key=f"form_edit_i_{iid}"):
                            c1, c2 = st.columns(2)
                            nuevo_stock_act = c1.number_input(
                                "Stock actual", value=float(insumo["stock_actual"]),
                                min_value=0.0, step=1.0
                            )
                            nuevo_stock_min = c2.number_input(
                                "Stock mínimo", value=float(insumo["stock_minimo"]),
                                min_value=0.0, step=1.0
                            )
                            prov_sel = c1.selectbox("Proveedor principal", prov_nombres_list,
                                                    index=prov_idx)
                            guardar = st.form_submit_button("💾 Guardar cambios", use_container_width=True)

                        if guardar:
                            nuevo_prov_id = prov_opciones.get(prov_sel) if prov_sel != "(Sin proveedor)" else None
                            payload = {
                                "stock_actual": nuevo_stock_act,
                                "stock_minimo": nuevo_stock_min,
                                "proveedor_id": nuevo_prov_id,
                            }
                            r = requests.put(f"{API}/insumos/{iid}", json=payload, timeout=5)
                            if r.status_code == 200:
                                st.success(f"✅ Insumo **{insumo['nombre']}** actualizado.")
                                st.session_state.pop(f"edit_insumo_{iid}", None)
                                st.rerun()
                            else:
                                st.error(f"Error al actualizar: {r.text}")

                    # ── Confirmación de eliminación ──────────────────────────
                    if st.session_state.get(f"del_insumo_{iid}"):
                        st.warning(
                            f"⚠️ ¿Eliminar **{insumo['nombre']}**? "
                            "No se podrá eliminar si está en fichas técnicas o tiene órdenes pendientes."
                        )
                        confirmar = st.checkbox(
                            "Sí, confirmo la eliminación", key=f"chk_del_i_{iid}"
                        )
                        if confirmar:
                            r = requests.delete(f"{API}/insumos/{iid}", timeout=5)
                            if r.status_code == 200:
                                st.success("✅ Insumo eliminado.")
                                st.session_state.pop(f"del_insumo_{iid}", None)
                                st.rerun()
                            else:
                                try:
                                    detail = r.json().get("detail", r.text)
                                except Exception:
                                    detail = r.text
                                st.error(f"🚫 {detail}")

    # ── Agregar Insumo ─────────────────────────────────────────────────────────
    with sub_agregar_i:
        st.markdown("### Nuevo Insumo")
        st.caption("Registra un nuevo insumo crítico. Podrás asignarle recetas desde el sistema ML.")

        prov_nombres_list_add = ["(Sin proveedor)"] + list(prov_opciones.keys())

        with st.form("form_nuevo_insumo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nuevo_nombre_i   = c1.text_input("Nombre del insumo *", placeholder="Ej: Manteca Vegetal")
            nueva_unidad     = c2.selectbox("Unidad de medida *", UNIDADES)
            nuevo_stock_act  = c1.number_input("Stock actual *",  min_value=0.0, step=1.0, value=0.0)
            nuevo_stock_min  = c2.number_input("Stock mínimo *",  min_value=0.0, step=1.0, value=0.0)
            prov_sel_add     = c1.selectbox("Proveedor principal", prov_nombres_list_add)
            crear_i = st.form_submit_button("➕ Crear Insumo", use_container_width=True)

        if crear_i:
            if not nuevo_nombre_i.strip():
                st.error("El nombre del insumo es obligatorio.")
            elif nuevo_stock_min <= 0:
                st.error("El stock mínimo debe ser mayor a 0 para que las alertas funcionen correctamente.")
            else:
                nuevo_prov_id = prov_opciones.get(prov_sel_add) if prov_sel_add != "(Sin proveedor)" else None
                payload = {
                    "nombre":        nuevo_nombre_i.strip(),
                    "stock_actual":  nuevo_stock_act,
                    "stock_minimo":  nuevo_stock_min,
                    "unidad_medida": nueva_unidad,
                    "proveedor_id":  nuevo_prov_id,
                }
                r = requests.post(f"{API}/insumos/", json=payload, timeout=5)
                if r.status_code in [200, 201]:
                    ins_creado = r.json()
                    st.success(
                        f"✅ Insumo **{ins_creado['nombre']}** creado con ID `{ins_creado['id']}`."
                    )
                    st.rerun()
                else:
                    try:
                        detail = r.json().get("detail", r.text)
                    except Exception:
                        detail = r.text
                    st.error(f"Error al crear insumo: {detail}")
