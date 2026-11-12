from flask import Flask, render_template, request, session
import math
import sympy as sp
import re

app = Flask(__name__)
app.secret_key = 'nexo_numerico_clave_secreta'

# ==========================================
# 0. FUNCIONES DE PREPROCESAMIENTO Y FORMATO UNIFICADAS
# ==========================================
def limpiar_expresion(expr_str):
    """Limpia y estandariza la entrada matemática para todos los módulos."""
    expr = expr_str.strip()
    expr = re.sub(r'^[a-zA-Z]\s*=\s*', '', expr)
    expr = expr.replace('²', '**2').replace('³', '**3').replace('^', '**')
    expr = re.sub(r'(?<!\*)\b([a-zA-Z])(\d+)\b', r'\2*\1', expr)
    expr = re.sub(r'(\d+)\s*([a-zA-Z])', r'\1*\2', expr)
    expr = re.sub(r'([a-zA-Z0-9\)])\s*(\()', r'\1*\2', expr)
    return expr

def formatear_resultado_visual(texto_resultado):
    """Reemplaza expresiones técnicas como sqrt(X) por el símbolo matemático √."""
    resultado_bonito = re.sub(r'sqrt\((.*?)\)', r'√(\1)', texto_resultado)
    return resultado_bonito


# ==========================================
# 1. LAS 4 SKILLS DEL BACKEND (Paradigma POO)
# ==========================================

class EcuacionSimbolica:
    def __init__(self, ecuacion_str):
        self.ecuacion_str = ecuacion_str

    def resolver(self):
        try:
            x, y, z = sp.symbols('x y z')
            eq_limpia = limpiar_expresion(self.ecuacion_str)
            
            if '=' in eq_limpia:
                partes = eq_limpia.split('=')
                lado_izq = sp.sympify(partes[0])
                lado_der = sp.sympify(partes[-1])
                eq = sp.Eq(lado_izq, lado_der)
            else:
                eq = sp.Eq(sp.sympify(eq_limpia), 0)
            
            simbolos_presentes = eq.free_symbols
            
            if z in simbolos_presentes:
                soluciones = sp.solve(eq, z)
                if not soluciones:
                    return "Error: No se pudo despejar la variable z."
                res_bruto = f"z = {soluciones[0]}"
                
            elif y in simbolos_presentes and x in simbolos_presentes:
                soluciones = sp.solve(eq, y)
                if not soluciones:
                    return "Error: No se pudo despejar la ecuación con dos variables."
                
                if len(soluciones) == 1 and y**2 in eq.atoms(sp.Pow):
                    sol_base = soluciones[0]
                    res_bruto = f"y₁ = {sol_base}  ó  y₂ = -({sol_base})"
                elif len(soluciones) > 1:
                    res_sols = [str(s) for s in soluciones]
                    res_bruto = f"Soluciones (y): {', '.join(res_sols)}"
                else:
                    res_bruto = f"y = {soluciones[0]}"
                
            elif y in simbolos_presentes and x not in simbolos_presentes:
                soluciones = sp.solve(eq, y)
                if not soluciones:
                    return "Error: La ecuación no tiene soluciones reales."
                sol_formateadas = [str(s.evalf(4)) if s.is_number else str(s) for s in soluciones]
                res_bruto = f"Soluciones (y): {', '.join(sol_formateadas)}"
                
            else:
                soluciones = sp.solve(eq, x)
                if not soluciones:
                    return "Error: La ecuación no tiene soluciones reales."
                sol_formateadas = [str(s.evalf(4)) if s.is_number else str(s) for s in soluciones]
                res_bruto = f"Soluciones (x): {', '.join(sol_formateadas)}"
            
            return formatear_resultado_visual(res_bruto)
                
        except Exception:
            return "Error: Expresión matemática no válida. Verifica los signos y la sintaxis."

class Conversor:
    def a_binario(self, num):
        try:
            return bin(int(num))[2:]
        except:
            return "Error: Ingrese un número entero válido para convertir a binario."
            
    def a_hexadecimal(self, num):
        try:
            return hex(int(num))[2:].upper()
        except:
            return "Error: Ingrese un número entero válido para convertir a hexadecimal."

class MetodoNewton:
    def __init__(self, funcion_str, x0, tolerancia):
        self.funcion_str = limpiar_expresion(funcion_str)
        self.x0 = x0
        self.tolerancia = tolerancia

    def calcular(self):
        try:
            x = sp.Symbol('x')
            f = sp.sympify(self.funcion_str)
            df = sp.diff(f, x)
            
            f_num = sp.lambdify(x, f, 'math')
            df_num = sp.lambdify(x, df, 'math')
            
            x_actual = self.x0
            for i in range(50):
                f_val = f_num(x_actual)
                df_val = df_num(x_actual)
                
                if df_val == 0:
                    return "Error: La derivada es cero en este punto, el método no puede continuar."
                
                x_siguiente = x_actual - (f_val / df_val)
                
                if abs(x_siguiente - x_actual) < self.tolerancia:
                    return f"Raíz aproximada: {x_siguiente:.4f} (en {i+1} iteraciones)"
                
                x_actual = x_siguiente
            return "Error: El método no convergió en 50 iteraciones."
        except Exception:
            return "Error: No se pudo procesar la función ingresada. Revisa la sintaxis."

class MetodoEuler:
    def __init__(self, x0, y0, h, iteraciones):
        self.x0 = x0
        self.y0 = y0
        self.h = h
        self.iteraciones = iteraciones

    def iterar(self):
        try:
            x, y = self.x0, self.y0
            lineas = ["<b>Resultados del Método de Euler:</b><br><br>"]
            for i in range(int(self.iteraciones)):
                y_nuevo = y + self.h * (x + y)
                x_siguiente = x + self.h
                
                iteracion_str = (
                    f"<b>Iteración {i+1}:</b><br>"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;X = {x_siguiente:.2f}<br>"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;Y = {y_nuevo:.4f}<br>"
                    f"<hr style='border: 0.5px solid rgba(255,255,255,0.3); margin: 8px 0;'>"
                )
                lineas.append(iteracion_str)
                
                x = x_siguiente
                y = y_nuevo
                
            return "".join(lineas)
        except Exception:
            return "Error: Verifique los valores ingresados para el método de Euler."


# ==========================================
# 2. RUTAS DE FLASK (Frontend y Backend)
# ==========================================

@app.route('/', methods=['GET', 'POST'])
def inicio():
    resultado = ""
    seccion_activa = "menu"

    if 'historial' not in session:
        session['historial'] = []

    if request.method == 'POST':
        accion = request.form.get('accion')

        # NAVEGACIÓN DESDE EL MENÚ PRINCIPAL
        if accion == 'ir_ecuacion':
            seccion_activa = 'ecuacion'
        elif accion == 'ir_conversor':
            seccion_activa = 'conversor'
        elif accion == 'ir_newton':
            seccion_activa = 'newton'
        elif accion == 'ir_euler':
            seccion_activa = 'euler'
        elif accion == 'ir_historial':
            seccion_activa = 'historial'
        elif accion == 'limpiar_historial':
            session['historial'] = []
            session.modified = True
            seccion_activa = 'historial'
        elif accion == 'salir':
            seccion_activa = 'salir'

        # EJECUCIÓN DE CÁLCULOS POR SKILL
        elif accion == 'ecuacion':
            seccion_activa = 'ecuacion'
            try:
                eq_str = request.form['ecuacion_completa']
                solver = EcuacionSimbolica(eq_str)
                resultado = solver.resolver()
                
                if not resultado.startswith("Error"):
                    session['historial'].insert(0, {
                        'modulo': 'Resolución de Ecuación',
                        'detalle': f'Ecuación: {eq_str}',
                        'resultado': resultado
                    })
                    session.modified = True
            except:
                resultado = "Error: Ocurrió un problema al procesar la ecuación."

        elif accion == 'conversor':
            seccion_activa = 'conversor'
            try:
                num = request.form['num_dec']
                tipo = request.form['tipo_conv']
                conv = Conversor()
                if tipo == 'bin':
                    res_val = conv.a_binario(num)
                    resultado = f"Binario: {res_val}"
                    detalle = f"Decimal {num} ➔ Binario"
                else:
                    res_val = conv.a_hexadecimal(num)
                    resultado = f"Hexadecimal: {res_val}"
                    detalle = f"Decimal {num} ➔ Hexadecimal"
                
                if not resultado.startswith("Error"):
                    session['historial'].insert(0, {
                        'modulo': 'Conversion Numérica',
                        'detalle': detalle,
                        'resultado': resultado
                    })
                    session.modified = True
            except:
                resultado = "Error: Ocurrió un fallo durante la conversión."

        elif accion == 'newton':
            seccion_activa = 'newton'
            try:
                func = request.form['funcion']
                x0 = float(request.form['x0'])
                tol = float(request.form['tolerancia'])
                newton = MetodoNewton(func, x0, tol)
                resultado = newton.calcular()
                
                if not resultado.startswith("Error"):
                    session['historial'].insert(0, {
                        'modulo': 'Newton-Raphson',
                        'detalle': f'f(x)={func}, x0={x0}, Tol={tol}',
                        'resultado': resultado
                    })
                    session.modified = True
            except:
                resultado = "Error: Por favor revise los datos numéricos ingresados."

        elif accion == 'euler':
            seccion_activa = 'euler'
            try:
                x0 = float(request.form['x0_euler'])
                y0 = float(request.form['y0_euler'])
                h = float(request.form['h_euler'])
                iters = int(request.form['iters'])
                euler = MetodoEuler(x0, y0, h, iters)
                resultado = euler.iterar()
                
                if not resultado.startswith("Error"):
                    session['historial'].insert(0, {
                        'modulo': 'Método de Euler',
                        'detalle': f'x0={x0}, y0={y0}, h={h}, iters={iters}',
                        'resultado': resultado
                    })
                    session.modified = True
            except:
                resultado = "Error: Por favor revise los datos numéricos ingresados."

    return render_template('index.html', resultado=resultado, seccion=seccion_activa, historial=session.get('historial', []))


# ==========================================
# 3. ARRANQUE LIMPIO LOCAL
# ==========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)