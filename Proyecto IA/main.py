import re
from visualizador import mostrar_arbol_async

# ============================================================
#                    NORMALIZACIÓN DE TEXTO
# ============================================================

# esta funcion la vamos a utlizar como clave del BST (suma_ascii, palabra_normalizada) para desempatar
# entre palabras con la misma suma ASCII
def _norm(palabra: str) -> str:
   
    return palabra.strip().lower()

# ============================================================
#                         ESTRUCTURAS
# ============================================================

class NodoBST:
    
    #inicializa el nodo con su clave y punteros a hijos nulos.
    def __init__(self, suma_ascii: int, palabra: str, significado: str | None = None):
        self.suma_ascii = suma_ascii          # métrica de comparación primaria
        self.palabra = palabra                # palabra original (para mostrar)
        self.significado = significado
        self.clave = (suma_ascii, _norm(palabra))  # empaqueta criterio de orden
        self.izquierda = None                       # hijo izquierdo
        self.derecha = None                       # hijo derecho


#encapsula operaciones sobre el BST
class ArbolBST:
   
    def __init__(self):
        self.raiz = None

    
#Inserta un nodo respetando el orden BST por clave compuesta.
    def insertar(self, suma_ascii: int, palabra: str, significado: str | None = None ) -> None:
        nuevo = NodoBST(suma_ascii, palabra, significado)
        if self.raiz is None:
            self.raiz = nuevo
        else:
            self._insertar_rec(self.raiz, nuevo)

    def _insertar_rec(self, actual: NodoBST, nuevo: NodoBST) -> None:
       
        #la clave compuesta evita que dos palabras con igual suma ASCII se mezclen desordenadas.
        if nuevo.clave < actual.clave:
            if actual.izquierda is None:
                actual.izquierda = nuevo
            else:
                self._insertar_rec(actual.izquierda, nuevo)
        elif nuevo.clave > actual.clave:
            if actual.derecha is None:
                actual.derecha = nuevo
            else:
                self._insertar_rec(actual.derecha, nuevo)
        else:
            # Duplicado exacto: misma suma y misma palabra normalizada.
            # Se omite para mantener unicidad.
            pass

    
# Devuelve la altura del árbol de forma recursiva.
    def _altura_rec(self, nodo: NodoBST) -> int:
        
        if nodo is None:
            return -1
        return 1 + max(self._altura_rec(nodo.izquierda), self._altura_rec(nodo.derecha))
 #Altura de la raíz. Útil para acotar la IDDFS y evitar iteraciones inútiles.
    def altura(self) -> int:
        return self._altura_rec(self.raiz)

# Búsqueda en Profundidad Limitada (DLS) 
    def dls(self, suma_objetivo: int, limite: int, palabra_objetivo: str | None = None):
       
        if self.raiz is None:
            return None, [], []

        clave_obj = None
        if palabra_objetivo is not None:
            clave_obj = (suma_objetivo, _norm(palabra_objetivo))

        # La pila guarda tuplas (nodo, nivel, padre)
        pila = [(self.raiz, 0, None)]
        padres = {}          # para reconstruir el camino
        visitados = set()    # evita reprocesar el mismo nodo
        recorrido = []       # traza del orden de visita

        while pila:
            nodo, nivel, padre = pila.pop()

            if nodo is None or nodo in visitados:
                continue

            visitados.add(nodo)
            padres[nodo] = padre
            recorrido.append((nodo.palabra, nodo.suma_ascii, nivel))

            # Si superamos el límite, no expandimos hijos.
            if nivel > limite:
                continue

            # Comprobación de meta por clave exacta 
            if clave_obj is not None and nodo.clave == clave_obj:
                # Reconstruir camino desde nodo hasta la raíz usando 'padres'
                camino_nodos = []
                cur = nodo
                while cur is not None:
                    camino_nodos.append(cur)
                    cur = padres[cur]
                camino_nodos.reverse()
                camino = [(n.palabra, n.suma_ascii) for n in camino_nodos]
                return nodo, recorrido, camino

            # LIFo para apilar primero derecha y luego izquierda
            # para visitar antes la izquierda en el pop siguiente
            if nivel < limite:
                if nodo.derecha:
                    pila.append((nodo.derecha, nivel + 1, nodo))
                if nodo.izquierda:
                    pila.append((nodo.izquierda, nivel + 1, nodo))

        return None, recorrido, []

    # Búsqueda en Profundidad Iterativa (

    def iddfs(self,suma_objetivo: int,limite_inicial: int,
            paso: int,
            limite_max: int | None,
            palabra_objetivo: str | None = None,
            acumular_recorridos: bool = False):
  
        if paso is None or paso <= 0:
            paso = 1
        if limite_inicial is None or limite_inicial < 0:
            limite_inicial = 0
        if limite_max is None:
            limite_max = self.altura()
        else:
            limite_max = max(0, limite_max)

        if self.raiz is None:
            return None, [], []

        recorrido_total = []
        nodo_encontrado = None
        camino_encontrado = []

        if limite_inicial > limite_max:
            return None, [], []

        for limite in range(limite_inicial, limite_max + 1, paso):
            nodo, recorrido, camino = self.dls(
                suma_objetivo, limite, palabra_objetivo
            )
            if acumular_recorridos:
                recorrido_total.extend([(p, v, lvl, limite) for (p, v, lvl) in recorrido])

            if nodo:
                nodo_encontrado = nodo
                camino_encontrado = camino
                break

        return nodo_encontrado, recorrido_total, camino_encontrado



def calcular_suma_ascii(palabra: str) -> int:
   
    return sum(ord(c) for c in palabra)

def _orden_insercion_balanceada(tuplas_ordenadas: list[tuple[int, str, str]]):

   # Dado un arreglo ordenado por (suma_ascii, palabra_norm),
    #devuelve índices en orden "medianas" para insertar y aproximar un BST balanceado.
    #Idea: insertar primero el medio, luego los medios de cada subarreglo, etc.
    
    indices = []

    def rec(lo: int, hi: int):
        if lo > hi:
            return
        mid = (lo + hi) // 2
        indices.append(mid)
        rec(lo, mid - 1)
        rec(mid + 1, hi)

    rec(0, len(tuplas_ordenadas) - 1)
    return [tuplas_ordenadas[i] for i in indices]
# Devuelve la lista balanceada en memoria: [(suma_ascii, palabra_norm, 'palabra : significado')]
def normalizar_y_generar_balanceado(archivo_entrada: str, archivo_salida_balanceado: str) -> list[tuple[int, str, str]]:
    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            lineas_in = f.readlines()
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo {archivo_entrada}")
        return []

    lineas_limpias = []
    vistos = set()  # evita duplicados 

    for linea in lineas_in:
        linea = linea.strip()
        if not linea or ':' not in linea:
            continue

        palabra_original, significado = linea.split(':', 1)
        palabra_original = palabra_original.strip()
        # elimina paréntesis y su contenido del significado (limpieza visual)
        significado = re.sub(r'\([^)]*\)', '', significado.strip())

        # filtra caracteres no alfabéticos en la palabra
        palabra_limpia = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', palabra_original)
        tokens = palabra_limpia.split()
        if not tokens:
            continue

        palabra = tokens[0]           # primera palabra como clave
        clave_norm = _norm(palabra)
        if clave_norm in vistos:
            continue
        vistos.add(clave_norm)
        lineas_limpias.append(f"{palabra} : {significado}")

    # arma tuplas (suma, palabra_norm, linea) y ordena
    tuplas = []
    for linea in lineas_limpias:
        palabra = linea.split(':', 1)[0].strip()
        tuplas.append((calcular_suma_ascii(palabra), _norm(palabra), linea))
    tuplas.sort(key=lambda t: (t[0], t[1]))

    # genera orden de "medianas" para inserción balanceada
    lista_balanceada = _orden_insercion_balanceada(tuplas)

    # escribe archivo balanceado (agrega la suma al final de cada línea)
    try:
        with open(archivo_salida_balanceado, 'w', encoding='utf-8') as f:
            for suma, _, linea in lista_balanceada:
                f.write(f"{linea} (Suma ASCII: {suma})\n")
        print(f"Archivo BALANCEADO guardado como: {archivo_salida_balanceado}")
        print(f"Palabras únicas: {len(lista_balanceada)}")
    except Exception as e:
        print(f"Error al escribir el archivo balanceado: {e}")

    return lista_balanceada


#Lee líneas tipo 'palabra : significado (Suma ASCII: N)' o sin sufijo.
    #Retorna tuplas: (suma_ascii, palabra_norm, 'palabra : significado')
def leer_lista_desde_archivo_balanceado(archivo: str) -> list[tuple[int, str, str]]:

    resultado = []
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            for raw in f:
                linea = raw.strip()
                if not linea:
                    continue
                # si viene con sufijo '(Suma ASCII: N)', lo quitamos
                m = re.search(r'\s*\(Suma ASCII:\s*\d+\)\s*$', linea)
                if m:
                    linea = linea[:m.start()]
                if ':' not in linea:
                    continue
                palabra = linea.split(':', 1)[0].strip()
                suma = calcular_suma_ascii(palabra)
                resultado.append((suma, _norm(palabra), linea))
    except FileNotFoundError:
        print(f"No se encontró el archivo: {archivo}")
    return resultado

# Costruciion del árbol desde la lista balanceada

def construir_arbol_desde_lista(lista_balanceada: list[tuple[int, str, str]]) -> ArbolBST:
  
    arbol = ArbolBST()

    for suma, _, linea in lista_balanceada:
        # linea debe traer "palabra : significado"
        if ':' in linea:
            palabra, significado = linea.split(':', 1)
            palabra = palabra.strip()
            significado = significado.strip()
        else:
            # por si alguna línea viniera mal formada
            palabra = linea.strip()
            significado = ""

        arbol.insertar(suma, palabra, significado)

    print("Árbol construido (inserción en orden balanceado).")
    return arbol


# Construcción del árbol balanceado, ya sea desde memoria o archivo
def construir_arbol_balanceado_auto(lista_balanceada_mem: list[tuple[int, str, str]] | None) -> ArbolBST | None:
    
    # Si hay lista balanceada en memoria, la usa.
    #Si no, pide la ruta del archivo balanceado y lo carga.
    
    if lista_balanceada_mem:
        return construir_arbol_desde_lista(lista_balanceada_mem)

    print("\nNo hay lista balanceada en memoria. Se requiere el archivo balanceado.")
    ruta_arch = input("Ruta del archivo BALANCEADO: ").strip()
    if not ruta_arch:
        print("No se proporcionó un archivo balanceado. Genere primero con la opción 1.")
        return None

    lista = leer_lista_desde_archivo_balanceado(ruta_arch)
    if not lista:
        print("No se pudo leer o parsear el archivo balanceado.")
        return None

    return construir_arbol_desde_lista(lista)



def buscar_interactivo(arbol: ArbolBST) -> None:
  
    if arbol is None or arbol.raiz is None:
        print("Error: el árbol no ha sido construido")
        return

    try:
        pal = input("Ingrese la palabra a buscar: ").strip()
        if not pal:
            print("Error: ingrese una palabra no vacía.")
            return

        suma_obj = calcular_suma_ascii(pal)
        lim = int(input("Ingrese la profundidad máxima de búsqueda: "))

        #  DLS con el límite ingresado por el usuario
        nodo, recorrido, camino = arbol.dls(suma_obj, lim, pal)

        print("\nRecorrido con límite inicial:")
        if not recorrido:
            print("  (sin visitas)")
        else:
            for p, v, nivel in recorrido:
                print(f"  - {p} (ASCII={v}, nivel={nivel})")

        if nodo:
            print("\nCamino raíz → objetivo:")
            print("  " + " -> ".join(f"{p}({v})" for p, v in camino))
            print(f"\nEncontrado: '{nodo.palabra}' | Suma ASCII: {nodo.suma_ascii}")
            if getattr(nodo, 'significado', None):
                print(f"Significado: {nodo.significado}")
            return

        # IDDFS elevando el límite hasta la altura del árbol
        print(f"\nNo se encontró '{pal}' (suma {suma_obj}) en el límite {lim}.")
        print("Aplicando búsqueda en profundidad iterativa (IDDFS)...")

        limite_max = arbol.altura()  
        nodo2, recorrido_total, camino2 = arbol.iddfs(
            suma_objetivo=suma_obj,
            limite_inicial=lim + 1,
            paso=1,
            limite_max=limite_max,
            palabra_objetivo=pal,
            acumular_recorridos=True
        )

        if nodo2:
            print("\nRecorrido acumulado por iteraciones (palabra, ASCII, nivel, límite_usado):")
            for p, v, nivel, lim_usado in recorrido_total:
                print(f"  - {p} (ASCII={v}, nivel={nivel}, límite={lim_usado})")

            print("\nCamino raíz → objetivo (IDDFS):")
            print("  " + " -> ".join(f"{p}({v})" for p, v in camino2))
            print(f"\nEncontrado con IDDFS: '{nodo2.palabra}' | Suma ASCII: {nodo2.suma_ascii}")
            if getattr(nodo2, 'significado', None):
                print(f"Significado: {nodo2.significado}")
        else:
            print(f"\nNo se encontró con IDDFS hasta el límite {limite_max}.")

    except ValueError:
        print("Error: ingrese un número válido para la profundidad.")

def mostrar_menu() -> None:
    print("\n" + "=" * 58)
    print("      MENÚ: DICCIONARIO, MEDIANTE DLS O IDDFS")
    print("=" * 58)
    print("1) Normalizar y generar diccionario BALANCEADO (1 archivo)")
    print("2) Construir árbol y Visualizar")
    print("3) Buscar en el árbol (DLS o IDDFS)")
    print("4) Salir")
    print("=" * 58)

def main() -> None:
    
    arbol = None
    lista_balanceada_mem: list[tuple[int, str, str]] = []

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción (1-4): ").strip()

        if opcion == '1':
            ruta_in = input("Archivo de entrada (texto fuente): ").strip()
            ruta_out = input("Archivo BALANCEADO de salida (p.ej. diccionario_balanceado.txt): ").strip()
            lista_balanceada_mem = normalizar_y_generar_balanceado(ruta_in, ruta_out)

        elif opcion == '2':
            arbol = construir_arbol_balanceado_auto(lista_balanceada_mem)
            if arbol is not None:
                # Reutiliza tu visualizador externo
                mostrar_arbol_async(arbol, titulo="Árbol BST balanceado")

        elif opcion == '3':
            if arbol is None or arbol.raiz is None:
                print("Primero construya el árbol (opción 2).")
            else:
                buscar_interactivo(arbol)

        elif opcion == '4':
            print("Fin del programa.")
            break

        else:
            print("Opción no válida. Seleccione 1-4.")

        input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    main()
