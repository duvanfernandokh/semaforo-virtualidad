# El semáforo de la virtualidad

Código y datos del policy paper *Inserción laboral de egresados de pregrado virtual en Colombia: heterogeneidad por campo de conocimiento y brechas en la cobertura de la acreditación de alta calidad, 2018–2023*.

Duvan Fernando Caleño Henao · Maestría en Economía y Política de la Educación ·
Universidad Externado de Colombia

---

## Qué hay en cada carpeta

```
semaforo-virtualidad/
├── datos/                    los cuatro archivos del panel
│   ├── panel_celda.csv       campo CINE × modalidad × cohorte (99 filas)
│   ├── panel_programa.csv    programa × cohorte (27.939 filas)
│   ├── semaforo.csv          clasificación por campo
│   └── control_calidad.csv   verificación del cruce
├── salidas/                  lo que generan los guiones (figuras, log, QR)
├── tablero.py                tablero interactivo — el semáforo
├── .streamlit/config.toml    tema visual del tablero
├── pipeline.py               reconstruye el panel desde los archivos del SNIES y el OLE
├── analisis.py               las seis especificaciones
├── robustez.py               las siete verificaciones de robustez
├── figura_cobertura.py       genera la Figura 2 del documento
├── generar_qr.py             genera el código QR del tablero publicado
├── analisis.do               las mismas estimaciones en Stata
└── requirements.txt          dependencias
```

---

## Puesta en marcha en Visual Studio Code

### 1. Instalar lo necesario

Necesitas **Python 3.10 o superior** y **Visual Studio Code**. Si no tienes Python,
descárgalo de python.org y, durante la instalación en Windows, marca la casilla
*Add Python to PATH*; sin eso VS Code no lo encuentra.

En VS Code instala la extensión **Python** de Microsoft. Al abrir esta carpeta, el
editor te la sugerirá solo, porque está declarada en `.vscode/extensions.json`.

### 2. Abrir el proyecto

`Archivo > Abrir carpeta…` y selecciona `semaforo-virtualidad`. Abre la carpeta
completa, no un archivo suelto: las rutas del proyecto se resuelven a partir de ella.

### 3. Crear el entorno virtual

Abre la terminal integrada con `Ctrl + Ñ` (o `Ver > Terminal`) y ejecuta:

**Windows**
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS o Linux**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Después pulsa `Ctrl + Shift + P`, escribe *Python: Select Interpreter* y elige el que
diga `.venv`. Es el paso que más se olvida: si no lo haces, VS Code ejecuta con el
Python del sistema y no encuentra las librerías.

### 4. Levantar el tablero

Dos formas, ambas equivalentes.

Desde la terminal:
```
streamlit run tablero.py
```

O con el depurador: ve al panel *Ejecutar y depurar* (`Ctrl + Shift + D`), elige
**Tablero (Streamlit)** en el desplegable y pulsa `F5`. Esta segunda forma permite
poner puntos de interrupción dentro del código del tablero.

El navegador abre en `http://localhost:8501`. Para detenerlo, `Ctrl + C` en la
terminal.

### 5. Los demás guiones

El archivo `launch.json` trae una configuración por guion, de modo que puedes
ejecutarlos con `F5` sin escribir comandos. También funcionan desde la terminal:

```
python analisis.py            # las seis especificaciones
python robustez.py            # las siete verificaciones (tarda unos minutos)
python figura_cobertura.py    # regenera la Figura 2 en salidas/
python generar_qr.py https://direccion-del-tablero
python pipeline.py            # reconstruye el panel desde las fuentes originales
```

`pipeline.py` es el único que necesita los archivos originales del SNIES y del
Observatorio Laboral. Antes de ejecutarlo, ajusta las rutas del bloque `RUTAS` al
comienzo del archivo. Los demás trabajan sobre los CSV de `datos/`, que ya están
construidos.

---

## El tablero

El tablero se lee de arriba abajo, como un informe de una sola página. La barra
lateral lleva el índice —píldoras de color que llevan a cada sección— y debajo los
filtros de cohorte, modalidad y campo, que actúan sobre las vistas descriptivas.

1. **Las cifras clave.** Brecha media, conteo del semáforo, cobertura de la
   acreditación y egresados bajo el filtro.
2. **El semáforo.** Los diez campos en una lista numerada, de mayor a menor ventaja
   de la modalidad virtual, cada uno con su brecha, su intervalo de confianza y su
   etiqueta de estado; al lado, la regla de clasificación. Debajo, el gráfico de
   intervalos.
3. **Evolución.** La tasa de cotización por modalidad y la brecha observada en cada
   cohorte.
4. **La acreditación.** Brecha frente a la proporción de programas virtuales
   acreditados en cada campo.
5. **Lo que no se sabe.** La incertidumbre del coeficiente de interacción. No es un
   simulador.
6. **Qué se propone.** La estrategia dual y su ejecución con la normativa vigente.
7. **Fuentes.** Origen de los datos y control de calidad del panel.

Cada vista trae su versión en tabla en un desplegable «Ver como tabla».

Los coeficientes están precalculados en el diccionario `COEFICIENTES` de `tablero.py`
y **no se reestiman al ejecutar**. Es deliberado: garantiza que lo que el tablero
muestre coincida con lo que reportan los anexos 1 y 4 del documento. Si los datos
cambian, hay que actualizar ese diccionario a mano y dejar constancia del cambio.

### Sobre el estilo

Papel cálido, tarjetas claras y tres tipografías de Google Fonts: Bricolage
Grotesque para títulos y cifras, Instrument Serif para las bajadas y JetBrains Mono
para rótulos y ejes. Se cargan desde internet; sin conexión, el tablero usa las
tipografías del sistema y funciona igual. Los colores del índice solo identifican
secciones. Los colores del semáforo son una paleta reservada de estado y **nunca
comunican solos**: cada punto lleva una forma propia —círculo, rombo, cuadrado— y
cada campo, una etiqueta con la palabra. El azul y el naranja de las modalidades son
las dos primeras ranuras de una paleta categórica validada para daltonismo.

El tema está en `.streamlit/config.toml`, que además oculta el botón *Deploy* y el
menú de Streamlit. Requiere Streamlit 1.45 o superior.

---

## Publicar el tablero

Para que el lector no tenga que instalar nada:

1. Sube esta carpeta a un repositorio público.
2. Despliégala en un servicio que ejecute aplicaciones Streamlit. Necesita ver
   `requirements.txt` en la raíz y apuntar a `tablero.py` como archivo principal.
3. Con la dirección en mano, ejecuta `python generar_qr.py <dirección>` y consigna la
   dirección y el QR en la tabla de acceso del Anexo 7.

---

## Stata

`analisis.do` replica las estimaciones. Abre el archivo, ajusta la línea

```
global proyecto "C:/Tesis/semaforo-virtualidad"
```

a la ruta de esta carpeta y ejecútalo completo. Lee los CSV de `datos/` y escribe el
registro y el gráfico en `salidas/`.
