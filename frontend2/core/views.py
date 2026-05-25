import re
import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import json
import time
from concurrent.futures import ThreadPoolExecutor

API = "http://127.0.0.1:8000"
TIMEOUT = 3

_cache = {}
_cache_lock = __import__('threading').Lock()


def login_view(request):
    if request.user.is_authenticated:
        return redirect('resumen')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            error = 'Ingrese usuario y contraseña'
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('resumen')
                else:
                    error = 'Usuario desactivado'
            else:
                error = 'Credenciales incorrectas'

    return render(request, 'core/login.html', {'error': error})


def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('login')


def rol_requerido(*roles_permitidos):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.rol in roles_permitidos:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'No tienes permiso para acceder a esta página')
            return redirect('resumen')
        return wrapper
    return decorator


def admin_requerido(view_func):
    return rol_requerido('administrador')(view_func)


def gerente_requerido(view_func):
    return rol_requerido('administrador', 'gerente')(view_func)


def _get_cache(key, timeout=30):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.time() - entry['ts']) < timeout:
            return entry['data']
    return None


def _set_cache(key, data):
    with _cache_lock:
        _cache[key] = {'data': data, 'ts': time.time()}


def get_api(endpoint, cache_seconds=30):
    cached = _get_cache(endpoint, cache_seconds)
    if cached is not None:
        return cached
    try:
        r = requests.get(f"{API}{endpoint}", timeout=TIMEOUT)
        data = r.json()
        _set_cache(endpoint, data)
        return data
    except:
        return None


def post_api(endpoint, data):
    try:
        r = requests.post(f"{API}{endpoint}", json=data, timeout=TIMEOUT)
        return r.json()
    except:
        return None


def invalidate_cache():
    with _cache_lock:
        _cache.clear()


@login_required
def resumen(request):
    with ThreadPoolExecutor() as ex:
        f_data     = ex.submit(get_api, "/dashboard/resumen", 15)
        f_productos = ex.submit(get_api, "/productos/")
    data = f_data.result()
    productos = f_productos.result()
    n_productos = len(productos) if productos else 0
    return render(request, 'core/resumen.html', {'resumen': data, 'n_productos': n_productos})


@login_required
def registro_diario(request):
    with ThreadPoolExecutor() as ex:
        f_productos = ex.submit(get_api, "/productos/")
        f_ventas    = ex.submit(get_api, "/ventas/")
    productos = f_productos.result()
    ventas    = f_ventas.result()
    return render(request, 'core/registro_diario.html', {'productos': productos, 'ventas': ventas})


@login_required
@gerente_requerido
def predicciones(request):
    with ThreadPoolExecutor() as ex:
        f_predicciones = ex.submit(get_api, "/predicciones/")
        f_productos    = ex.submit(get_api, "/productos/")
    predicciones = f_predicciones.result()
    productos    = f_productos.result()
    productos_dict = {p['id']: p['nombre'] for p in productos} if productos else {}
    return render(request, 'core/predicciones.html', {'predicciones': predicciones, 'productos_dict': productos_dict})


@login_required
@gerente_requerido
def analisis_mermas(request):
    with ThreadPoolExecutor() as ex:
        f_mermas  = ex.submit(get_api, "/mermas/")
        f_analisis = ex.submit(get_api, "/mermas/analisis")
    mermas   = f_mermas.result()
    analisis = f_analisis.result()
    return render(request, 'core/analisis_mermas.html', {'mermas': mermas, 'analisis': analisis})


@login_required
def inventario(request):
    with ThreadPoolExecutor() as ex:
        f_insumos = ex.submit(get_api, "/insumos/")
        f_alertas = ex.submit(get_api, "/insumos/alertas/")
    insumos = f_insumos.result()
    alertas = f_alertas.result()
    return render(request, 'core/inventario.html', {'insumos': insumos, 'alertas': alertas})


@login_required
def catalogo(request):
    productos = get_api("/productos/")
    if productos:
        for p in productos:
            precio = float(p.get('precio', 0))
            costo = float(p.get('costo', 0))
            if precio > 0:
                p['margen_pct'] = round(((precio - costo) / precio) * 100, 1)
            else:
                p['margen_pct'] = 0
    return render(request, 'core/catalogo.html', {'productos': productos})


@login_required
@gerente_requerido
def ordenes_compra(request):
    with ThreadPoolExecutor() as ex:
        f_ordenes     = ex.submit(get_api, "/ordenes-compra/")
        f_proveedores = ex.submit(get_api, "/proveedores/")
        f_insumos     = ex.submit(get_api, "/insumos/")
    ordenes     = f_ordenes.result()
    proveedores = f_proveedores.result()
    insumos     = f_insumos.result()
    return render(request, 'core/ordenes_compra.html', {'ordenes': ordenes, 'proveedores': proveedores, 'insumos': insumos})


@login_required
@gerente_requerido
def reportes_financieros(request):
    return render(request, 'core/reportes_financieros.html', {})


@login_required
@admin_requerido
def modelo_estadistico(request):
    with ThreadPoolExecutor() as ex:
        f_metricas = ex.submit(get_api, "/ml/metricas")
        f_estado   = ex.submit(get_api, "/sistema/estado")
    metricas = f_metricas.result()
    estado   = f_estado.result()
    return render(request, 'core/modelo_estadistico.html', {'metricas': metricas, 'estado': estado})


@csrf_exempt
def api_productos(request):
    invalidate_cache()
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except:
            data = {
                'nombre': request.POST.get('nombre'),
                'categoria': request.POST.get('categoria'),
                'precio': float(request.POST.get('precio', 0)),
                'costo': float(request.POST.get('costo', 0))
            }
        result = post_api("/productos/", data)
        return JsonResponse(result or {'error': 'Error'})
    productos = get_api("/productos/")
    return JsonResponse(productos, safe=False)


@csrf_exempt
def api_ventas(request):
    invalidate_cache()
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except:
            data = {
                'producto_id': int(request.POST.get('producto_id')),
                'fecha': request.POST.get('fecha'),
                'cantidad_vendida': float(request.POST.get('cantidad_vendida')),
                'cantidad_producida': float(request.POST.get('cantidad_producida', 0)) or None,
                'motivo_merma': request.POST.get('motivo_merma', 'Sobreproduccion')
            }
        result = post_api("/ventas/", data)
        return JsonResponse(result or {'error': 'Error'})
    ventas = get_api("/ventas/")
    return JsonResponse(ventas, safe=False)


@csrf_exempt
def api_insumos(request):
    invalidate_cache()
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except:
            data = {
                'nombre': request.POST.get('nombre'),
                'stock_actual': float(request.POST.get('stock_actual') or 0),
                'stock_minimo': float(request.POST.get('stock_minimo') or 0),
                'unidad_medida': request.POST.get('unidad_medida'),
                'proveedor_id': int(request.POST.get('proveedor_id')) if request.POST.get('proveedor_id') else None
            }
        result = post_api("/insumos/", data)
        return JsonResponse(result or {'error': 'Error'})
    insumos = get_api("/insumos/")
    return JsonResponse(insumos, safe=False)


@csrf_exempt
def api_ordenes(request):
    invalidate_cache()
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except:
            data = {
                'proveedor_id': int(request.POST.get('proveedor_id')),
                'insumo_id': int(request.POST.get('insumo_id')),
                'fecha_orden': request.POST.get('fecha_orden'),
                'cantidad': float(request.POST.get('cantidad')),
                'precio_unitario': float(request.POST.get('precio_unitario', 0)) or None,
                'estado': 'pendiente'
            }
        result = post_api("/ordenes-compra/", data)
        return JsonResponse(result or {'error': 'Error'})
    ordenes = get_api("/ordenes-compra/")
    return JsonResponse(ordenes, safe=False)


@csrf_exempt
def api_recibir_orden(request, orden_id):
    invalidate_cache()
    if request.method == 'POST':
        try:
            result = requests.post(f"{API}/ordenes-compra/{orden_id}/recibir", timeout=TIMEOUT).json()
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'error': str(e)})
    return JsonResponse({'error': 'Metodo no permitido'})


@csrf_exempt
def ml_cargar_seed(request):
    invalidate_cache()
    try:
        result = requests.post(f"{API}/datos/semilla", timeout=60).json()
        return JsonResponse(result or {'error': 'Sin respuesta'})
    except Exception as e:
        return JsonResponse({'error': str(e)})


@csrf_exempt
def ml_entrenar(request):
    invalidate_cache()
    try:
        result = requests.post(f"{API}/ml/entrenar", timeout=120).json()
        return JsonResponse(result or {'error': 'Sin respuesta'})
    except Exception as e:
        return JsonResponse({'error': str(e)})


@csrf_exempt
def ml_sincronizar_clima(request):
    invalidate_cache()
    try:
        result = requests.post(f"{API}/clima/sincronizar?dias=7", timeout=30).json()
        return JsonResponse(result or {'error': 'Sin respuesta'})
    except Exception as e:
        return JsonResponse({'error': str(e)})


@csrf_exempt
def ml_generar_predicciones(request):
    invalidate_cache()
    try:
        result = requests.post(f"{API}/predicciones/generar?n_dias=7", timeout=60).json()
        return JsonResponse(result or {'error': 'Sin respuesta'})
    except Exception as e:
        return JsonResponse({'error': str(e)})


@csrf_exempt
def api_chatbot(request):
    try:
        data = json.loads(request.body)
        pregunta = data.get('pregunta', '')
        result = requests.post(f"{API}/chatbot/pregunta", json={"pregunta": pregunta}, timeout=TIMEOUT).json()
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'mensaje': 'Error de conexion: ' + str(e)})


@csrf_exempt
def reportes_estado_resultados(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            result = requests.post(
                f"{API}/reportes/estado-resultados",
                json={"fecha_inicio": data.get('fecha_inicio'), "fecha_fin": data.get('fecha_fin')},
                timeout=TIMEOUT
            ).json()
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'error': str(e)})
    return JsonResponse({'error': 'Metodo no permitido'})


@csrf_exempt
def reportes_ventas_diarias(request):
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    try:
        result = requests.get(
            f"{API}/reportes/ventas-diarias?fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}",
            timeout=TIMEOUT
        ).json()
        return JsonResponse(result)
    except:
        return JsonResponse({'error': 'Error'})


@csrf_exempt
def reportes_rentabilidad(request):
    try:
        result = requests.get(f"{API}/reportes/productos-rentabilidad", timeout=TIMEOUT).json()
        return JsonResponse(result, safe=False)
    except:
        return JsonResponse([])


@csrf_exempt
def reportes_porcentaje(request):
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    try:
        result = requests.get(
            f"{API}/reportes/productos-porcentaje?fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}",
            timeout=TIMEOUT
        ).json()
        return JsonResponse(result, safe=False)
    except:
        return JsonResponse([])