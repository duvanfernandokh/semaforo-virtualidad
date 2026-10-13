# -*- coding: utf-8 -*-
"""
EL SEMÁFORO DE LA VIRTUALIDAD — tablero interactivo
===================================================
Implementa la especificación del Anexo 7 del policy paper.

Arquitectura en tres capas:
  datos          panel_celda.csv y panel_programa.csv, leídos y validados al iniciar
  modelo         coeficientes y clasificación precalculados en COEFICIENTES y
                 SEMAFORO; no se reestima nada en tiempo de ejecución, para que
                 las cifras coincidan necesariamente con las de los anexos 1 y 4
  presentación   una sola página que se lee de arriba abajo, como un informe:
                 portada, diagnóstico, semáforo, evolución, cobertura,
                 incertidumbre y fuentes. La barra lateral lleva el índice de
                 secciones y los filtros.

Ejecución local:
    pip install -r requirements.txt
    streamlit run tablero.py

Publicación: cualquier servicio de aplicaciones analíticas que ejecute
Streamlit. La dirección resultante se consigna en el Anexo 7.
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATOS = Path(__file__).parent / 'datos'

# --------------------------------------------------------------------------
# PALETA
# Papel y tinta: fondo cálido, tarjetas claras, texto casi negro.
# Índice: colores de navegación (solo identifican secciones, no datos).
# Categóricas: ranuras 1 y 2 de la paleta validada (ΔE con visión normal 33,6;
# ΔE con deuteranopía 24,7, ambos por encima del piso exigido).
# Estado: paleta reservada del semáforo. Nunca comunica sola: cada marca lleva
# además una forma propia y un rótulo de texto.
# --------------------------------------------------------------------------
PAPEL = '#efede7'         # fondo de la página
TARJETA = '#faf8f3'       # fondo de tarjetas y gráficos
TINTA = '#141413'
TINTA_2 = '#4d4b46'
TINTA_3 = '#86837b'
REJILLA = '#e3e0d6'
BASE = '#c4c0b3'

INDICE = {'diagnostico': '#7dbcff', 'resultados': '#d8f36a',
          'politica': '#ff6fae', 'incertidumbre': '#ff6fae', 'propuesta': '#ffb867',
          'fuentes': '#b9a6ff'}

AZUL = '#2a78d6'          # presencial
NARANJA = '#eb6834'       # virtual

ESTADO = {'Verde': '#0ca30c', 'Amarillo': '#fab219', 'Rojo': '#d03b3b',
          'Sin datos suficientes': '#898781'}
TEXTO_ESTADO = {'Verde': '#ffffff', 'Amarillo': '#141413', 'Rojo': '#ffffff',
                'Sin datos suficientes': '#ffffff'}
FORMA = {'Verde': 'circle', 'Amarillo': 'diamond', 'Rojo': 'square',
         'Sin datos suficientes': 'circle-open'}
GLIFO = {'Verde': '●', 'Amarillo': '◆', 'Rojo': '■', 'Sin datos suficientes': '○'}

DISPLAY = '"Bricolage Grotesque", "Segoe UI", system-ui, -apple-system, Arial, sans-serif'
SERIF = '"Instrument Serif", "Georgia", "Times New Roman", serif'
MONO = '"JetBrains Mono", "Consolas", "SFMono-Regular", monospace'
VERSION_PANEL = 'Cohortes 2018-2022 · seguimiento laboral 2019-2023'
TITULO_PAPER = ('Inserción laboral de egresados de pregrado virtual en Colombia: heterogeneidad por campo de conocimiento y brechas en la cobertura de la acreditación de alta calidad, 2018–2023')

# --------------------------------------------------------------------------
# CAPA DE MODELO — resultados precalculados (anexos 1 y 4)
# --------------------------------------------------------------------------
COEFICIENTES = {
    'brecha_media': {'coef': 7.13, 'ee': 0.95, 'ic': (5.26, 9.00), 'n': 99},
    'interaccion': {'coef': -3.41, 'ee': 3.49, 'ic': (-10.24, 3.42), 'n': 9194,
                    'programas_identificantes': 30},
    'rango_observado_acreditacion': (0.0, 8.0),
    'cobertura': {'virtual': 4.5, 'presencial': 24.7, 'z': 8.49},
}

SEMAFORO = {
    'Servicios': (26.44, 18.66, 34.23, 'Verde'),
    'Educacion': (11.91, 7.76, 16.05, 'Verde'),
    'Administracion De Empresas Y Derecho': (8.79, 6.98, 10.60, 'Verde'),
    'Ingenieria, Industria Y Construccion': (5.91, 3.89, 7.93, 'Verde'),
    'Salud Y Bienestar': (3.53, 1.10, 5.96, 'Amarillo'),
    'Ciencias Naturales, Matematicas Y Estadistica': (2.30, -2.19, 6.79, 'Amarillo'),
    'Ciencias Sociales, Periodismo E Informacion': (2.22, -5.49, 9.94, 'Amarillo'),
    'Arte Y Humanidades': (-0.67, -7.44, 6.10, 'Amarillo'),
    'Agropecuario, Silvicultura, Pesca Y Veterinaria': (-0.97, -6.85, 4.91, 'Amarillo'),
    'Tecnologias De La Informacion Y La Comunicacion (Tic)': (-5.25, -8.30, -2.19, 'Rojo'),
}

# Rótulos cortos y acentuados para ejes y tarjetas. Las claves del panel vienen
# del SNIES sin tildes y en mayúscula inicial; mostrarlas así resulta ilegible.
CORTO = {
    'Administracion De Empresas Y Derecho': 'Administración y Derecho',
    'Agropecuario, Silvicultura, Pesca Y Veterinaria': 'Agropecuario y Veterinaria',
    'Arte Y Humanidades': 'Arte y Humanidades',
    'Ciencias Naturales, Matematicas Y Estadistica': 'Ciencias Naturales',
    'Ciencias Sociales, Periodismo E Informacion': 'Ciencias Sociales',
    'Educacion': 'Educación',
    'Ingenieria, Industria Y Construccion': 'Ingeniería e Industria',
    'Salud Y Bienestar': 'Salud y Bienestar',
    'Servicios': 'Servicios',
    'Tecnologias De La Informacion Y La Comunicacion (Tic)': 'TIC',
}

SENTIDO = {'Rojo': 'Rezago verificado',
           'Amarillo': 'Sin diferencia distinguible',
           'Verde': 'Ventaja verificada'}


def corto(area):
    return CORTO.get(area, area)


def num(x, dec=1, signo=False):
    """Formato colombiano: coma decimal, punto de miles."""
    if x is None or pd.isna(x):
        return '—'
    s = f'{x:,.{dec}f}'.replace(',', ' ').replace('.', ',').replace(' ', '.')
    if signo and x > 0:
        s = '+' + s
    return s


# --------------------------------------------------------------------------
# CAPA DE DATOS
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def cargar():
    celda = pd.read_csv(DATOS / 'panel_celda.csv')
    programa = pd.read_csv(DATOS / 'panel_programa.csv')
    calidad = {}
    for nombre, df in (('celdas', celda), ('programas', programa)):
        df['tasa'] = pd.to_numeric(df['tasa'], errors='coerce')
        fuera = int((~df['tasa'].dropna().between(0, 1)).sum())
        calidad[nombre] = (fuera, len(df))
    return celda, programa, calidad


def cobertura_virtual(programa, cohorte=2022):
    d = programa[(programa.cohorte == cohorte) & programa.acreditado.notna()]
    d = d[d.modalidad == 'Virtual']
    g = d.groupby('area')['acreditado'].agg(['size', 'sum'])
    g.columns = ['programas', 'acreditados']
    g['cobertura'] = 100 * g.acreditados / g.programas
    return g


# --------------------------------------------------------------------------
# CHROME DE LAS GRÁFICAS — mismo papel que las tarjetas que las contienen
# --------------------------------------------------------------------------
def lienzo(fig, titulo_x='', titulo_y='', alto=460, leyenda=True):
    fig.update_layout(
        plot_bgcolor=TARJETA, paper_bgcolor=TARJETA, height=alto,
        font=dict(family=DISPLAY, size=13, color=TINTA),
        margin=dict(l=8, r=12, t=46 if leyenda else 14, b=8),
        hoverlabel=dict(bgcolor='#ffffff', bordercolor=REJILLA,
                        font=dict(family=DISPLAY, size=13, color=TINTA)),
        showlegend=leyenda,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0,
                    font=dict(family=MONO, size=11.5, color=TINTA_2),
                    bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(title=titulo_x, gridcolor=REJILLA, zeroline=False,
                   linecolor=BASE, ticks='outside', tickcolor=BASE, ticklen=4,
                   tickfont=dict(family=MONO, size=11.5, color=TINTA_3),
                   title_font=dict(family=MONO, size=11.5, color=TINTA_2)),
        yaxis=dict(title=titulo_y, gridcolor=REJILLA, zeroline=False,
                   linecolor=BASE, tickfont=dict(family=MONO, size=11.5, color=TINTA_3),
                   title_font=dict(family=MONO, size=11.5, color=TINTA_2)),
    )
    return fig


PLOTLY_CONF = {'displayModeBar': False, 'displaylogo': False,
               'scrollZoom': False, 'responsive': True}


# --------------------------------------------------------------------------
# PIEZAS DE PRESENTACIÓN
# --------------------------------------------------------------------------
def html(fragmento):
    st.markdown(fragmento, unsafe_allow_html=True)


def seccion(ancla, titulo, bajada):
    """Encabezado de sección: ancla para el índice, título grande y bajada en serif."""
    html(f'<div class="ancla" id="{ancla}"></div>'
         f'<h2 class="titulo-seccion">{titulo}</h2>'
         f'<p class="bajada">{bajada}</p>')


def nota(texto):
    html(f'<div class="nota">{texto}</div>')


def ficha(cat):
    """Etiqueta de estado: color, glifo y palabra. El color nunca va solo."""
    return (f'<span class="ficha" style="background:{ESTADO[cat]};'
            f'color:{TEXTO_ESTADO[cat]}">{GLIFO[cat]} {cat.upper()}</span>')


# --------------------------------------------------------------------------
# CAPA DE PRESENTACIÓN
# --------------------------------------------------------------------------
st.set_page_config(page_title='El semáforo de la virtualidad',
                   page_icon='🚦', layout='wide',
                   initial_sidebar_state='expanded')

html(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,700;12..96,800&family=Instrument+Serif&family=JetBrains+Mono:wght@400;600&display=swap');

  /* ---------- lienzo general ---------- */
  .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background: {PAPEL}; }}
  .block-container {{ padding-top: 2.6rem; padding-bottom: 4rem; max-width: 1180px; }}
  #MainMenu, footer {{ visibility: hidden; }}
  header[data-testid="stHeader"] {{ background: transparent; }}
  [data-testid="stToolbar"], .stAppDeployButton, [data-testid="stAppDeployButton"],
  [data-testid="stDecoration"] {{ display: none !important; }}
  html {{ scroll-behavior: smooth; }}

  /* Tipografía solo sobre texto. No usar [class*="st-"] ni "*": pisa la fuente
     de íconos de Streamlit y aparecen rótulos como "keyboard_double_arrow_left". */
  html, body, .stApp, .stMarkdown, p, label, li, h1, h2, h3, h4,
  [data-testid="stWidgetLabel"], [data-testid="stCaptionContainer"],
  [data-testid="stExpander"] summary p, button p {{ font-family: {DISPLAY}; color: {TINTA}; }}
  [data-testid="stIconMaterial"], span[class*="material-symbols"],
  span[class*="material-icons"] {{
      font-family: "Material Symbols Rounded", "Material Symbols Outlined",
                   "Material Icons" !important;
  }}

  /* ---------- portada ---------- */
  .ceja {{ font-family: {MONO}; font-size: 12.5px; letter-spacing: 2.2px;
           text-transform: uppercase; color: {TINTA_2}; margin: 0 0 18px 0; }}
  .portada h1 {{ font-family: {DISPLAY}; font-weight: 800; font-size: clamp(46px, 7.4vw, 104px);
                 line-height: 0.93; letter-spacing: -0.045em; color: {TINTA}; margin: 0 0 26px 0; }}
  .portada .entrada {{ font-family: {SERIF}; font-size: clamp(23px, 2.5vw, 33px);
                       line-height: 1.2; color: {TINTA}; max-width: 30ch; margin: 0; }}
  .portada .titulo-doc {{ font-family: {MONO}; font-size: 12.5px; line-height: 1.6;
                          color: {TINTA_2}; max-width: 78ch; margin: 22px 0 0 0; }}
  .portada .sello {{ display: inline-block; margin-top: 26px; font-family: {MONO};
                     font-size: 11.5px; letter-spacing: 1.2px; text-transform: uppercase;
                     padding: 5px 12px; border: 1.5px solid {TINTA}; border-radius: 999px; }}

  /* ---------- secciones ---------- */
  .ancla {{ position: relative; top: -24px; }}
  .titulo-seccion {{ font-family: {DISPLAY} !important; font-weight: 800 !important;
                     font-size: clamp(34px, 4.2vw, 54px) !important; line-height: 1.02 !important;
                     letter-spacing: -0.035em !important; color: {TINTA} !important;
                     margin: 96px 0 10px 0 !important; padding: 0 !important; }}
  .bajada {{ font-family: {SERIF} !important; font-size: clamp(20px, 1.9vw, 26px) !important;
             line-height: 1.22 !important; color: {TINTA_2} !important; max-width: 46ch;
             margin: 0 0 26px 0 !important; }}
  .rotulo-mono {{ font-family: {MONO}; font-size: 11.5px; letter-spacing: 1.8px;
                  text-transform: uppercase; color: {TINTA_2}; margin: 0 0 10px 0; }}

  /* ---------- tarjetas ---------- */
  .tarjeta {{ background: {TARJETA}; border-radius: 18px; padding: 20px 22px 18px 22px;
              box-shadow: 0 1px 0 rgba(20,20,19,0.04); height: 100%; }}
  .tarjeta .cifra {{ font-family: {DISPLAY}; font-weight: 800; font-size: clamp(30px, 2.9vw, 44px); line-height: 1;
                     letter-spacing: -0.04em; color: {TINTA}; margin: 4px 0 10px 0; white-space: nowrap; }}
  .tarjeta .cifra small {{ font-size: 18px; font-weight: 600; letter-spacing: 0; color: {TINTA_2}; }}
  .tarjeta .pie {{ font-family: {SERIF}; font-size: 18px; line-height: 1.25; color: {TINTA_2}; }}

  /* contenedores de Streamlit convertidos en tarjeta (gráficos) */
  [class*="st-key-tarjeta"] {{ background: {TARJETA}; border-radius: 18px;
                               padding: 18px 20px 10px 20px; border: none !important; }}

  /* ---------- filas del semáforo (lista numerada) ---------- */
  .fila {{ display: flex; align-items: center; gap: 16px; background: {TARJETA};
           border-radius: 16px; padding: 13px 18px; margin: 0 0 10px 0; }}
  .fila .n {{ flex: 0 0 34px; height: 34px; border-radius: 50%; background: {TINTA};
              color: {PAPEL}; display: inline-flex; align-items: center; justify-content: center;
              font-family: {MONO}; font-size: 12.5px; font-weight: 600; }}
  .fila .campo {{ font-family: {DISPLAY}; font-weight: 700; font-size: 17px; color: {TINTA};
                  flex: 1 1 auto; line-height: 1.2; }}
  .fila .campo small {{ display: block; font-family: {MONO}; font-weight: 400; font-size: 11.5px;
                        color: {TINTA_3}; letter-spacing: 0.4px; margin-top: 3px; }}
  .fila .valor {{ font-family: {DISPLAY}; font-weight: 800; font-size: 21px; letter-spacing: -0.02em;
                  color: {TINTA}; white-space: nowrap; font-variant-numeric: tabular-nums; }}
  .ficha {{ display: inline-block; font-family: {MONO}; font-size: 11px; font-weight: 600;
            letter-spacing: 1.2px; padding: 5px 11px; border-radius: 999px; white-space: nowrap; }}
  .fila .ficha {{ flex: 0 0 112px; text-align: center; }}
  .fila .valor {{ min-width: 92px; text-align: right; }}
  .fila .campo small.texto {{ font-family: {SERIF}; font-size: 17px; letter-spacing: 0;
                             color: {TINTA_2}; line-height: 1.25; margin-top: 4px; }}

  /* ---------- panel lateral de lectura ---------- */
  .lectura {{ background: {TARJETA}; border-radius: 18px; padding: 22px 22px 18px 22px; }}
  .lectura .regla {{ display: flex; gap: 12px; align-items: flex-start; padding: 12px 0;
                     border-top: 1px solid {REJILLA}; }}
  .lectura .regla:first-of-type {{ border-top: none; }}
  .lectura .regla p {{ font-family: {SERIF}; font-size: 18px; line-height: 1.22;
                       color: {TINTA}; margin: 0; }}
  .lectura .conteo {{ font-family: {DISPLAY}; font-weight: 800; font-size: 30px;
                      letter-spacing: -0.03em; line-height: 1; margin: 2px 0 6px 0; }}
  .pastilla {{ display: inline-block; font-family: {DISPLAY}; font-weight: 700; font-size: 14px;
               border: 1.5px solid {TINTA}; border-radius: 999px; padding: 4px 13px; margin: 2px 0 12px 0; }}

  /* ---------- notas ---------- */
  .nota {{ font-family: {SERIF}; font-size: 19px; line-height: 1.3; color: {TINTA_2};
           max-width: 62ch; margin: 18px 0 8px 0; }}
  .nota b {{ font-family: {DISPLAY}; font-weight: 700; font-size: 15px; color: {TINTA}; }}

  /* ---------- barra lateral: índice de secciones ---------- */
  section[data-testid="stSidebar"] {{ background: {PAPEL}; border-right: none; }}
  section[data-testid="stSidebar"] > div {{ background: {PAPEL}; }}
  section[data-testid="stSidebar"] .block-container {{ padding-top: 2rem; }}
  .grupo {{ font-family: {MONO}; font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
            color: {TINTA_2}; margin: 16px 0 6px 4px; }}
  a.pildora, a.pildora:visited {{ display: block; text-decoration: none !important;
            font-family: {DISPLAY}; font-weight: 700; font-size: 15px; color: {TINTA} !important;
            padding: 8px 15px; border-radius: 999px; margin: 0 0 6px 0;
            border: 2px solid transparent; transition: border-color .15s, transform .15s; }}
  a.pildora:hover {{ border-color: {TINTA}; transform: translateX(2px); }}
  [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ font-weight: 700; }}
  [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
      font-family: {SERIF}; font-size: 16px; line-height: 1.25; color: {TINTA_2}; }}

  /* ---------- expansores ("ver como tabla") ---------- */
  [data-testid="stExpander"] details {{ background: {TARJETA}; border: none; border-radius: 14px; }}
  [data-testid="stExpander"] summary p {{ font-family: {MONO} !important; font-size: 12px;
      letter-spacing: 1.4px; text-transform: uppercase; }}
</style>
""")

celda, programa, calidad = cargar()

# ---- barra lateral: índice de secciones y filtros ----
cohortes = sorted(celda.cohorte.unique())
campos = sorted(celda.area.unique())

with st.sidebar:
    html(f"""
    <div class="grupo">Diagnóstico</div>
    <a class="pildora" target="_self" href="#cifras" style="background:{INDICE['diagnostico']}">Las cifras clave</a>
    <div class="grupo">Resultados</div>
    <a class="pildora" target="_self" href="#semaforo" style="background:{INDICE['resultados']}">El semáforo</a>
    <a class="pildora" target="_self" href="#evolucion" style="background:{INDICE['resultados']}">Evolución</a>
    <div class="grupo">Política</div>
    <a class="pildora" target="_self" href="#cobertura" style="background:{INDICE['politica']}">La acreditación</a>
    <a class="pildora" target="_self" href="#incertidumbre" style="background:{INDICE['incertidumbre']}">Lo que no se sabe</a>
    <div class="grupo">Propuesta</div>
    <a class="pildora" target="_self" href="#propuesta" style="background:{INDICE['propuesta']}">Qué se propone</a>
    <div class="grupo">Fuentes</div>
    <a class="pildora" target="_self" href="#fuentes" style="background:{INDICE['fuentes']}">Fuentes</a>
    <div class="grupo" style="margin-top:28px">Filtros</div>
    """)

    desde, hasta = st.select_slider(
        'Cohorte de graduación', options=cohortes,
        value=(cohortes[0], cohortes[-1]),
        help='Año de grado. El seguimiento laboral ocurre un año después.')
    sel_cohortes = [c for c in cohortes if desde <= c <= hasta]

    sel_mod = st.pills('Modalidad', ['Presencial', 'Virtual'],
                       selection_mode='multi', default=['Presencial', 'Virtual'])

    n_marcados = sum(1 for a in campos if st.session_state.get(f'campo_{a}', True))
    with st.expander(f'Campos · {n_marcados} de {len(campos)}', expanded=False):
        marcados = []
        for a in campos:
            if st.checkbox(corto(a), value=True, key=f'campo_{a}'):
                marcados.append(a)
        sel_campos = marcados
    st.caption('Los filtros cambian las vistas descriptivas. Los coeficientes vienen de '
               'los anexos 1 y 4 y no se reestiman: filtrar muestra un subconjunto de '
               'los mismos resultados, nunca una nueva estimación.')

# ---- portada ----
html(f"""
<div class="portada">
  <div class="ceja">Policy paper · Maestría en Economía y Política de la Educación · Universidad Externado de Colombia</div>
  <h1>El semáforo de<br>la virtualidad</h1>
  <p class="entrada">Cómo se insertan en el empleo formal los egresados de pregrado virtual
     frente a los presenciales, campo por campo, y hasta dónde llega la acreditación
     de alta calidad.</p>
  <p class="titulo-doc">Tablero del policy paper «{TITULO_PAPER}»</p>
  <span class="sello">{VERSION_PANEL}</span>
</div>
""")

if not sel_cohortes or not sel_mod or not sel_campos:
    st.info('Seleccione al menos una cohorte, una modalidad y un campo de conocimiento '
            'en la barra lateral.')
    st.stop()

f = celda[celda.cohorte.isin(sel_cohortes) & celda.modalidad.isin(sel_mod)
          & celda.area.isin(sel_campos)]

vistos = [a for a in sel_campos if a in SEMAFORO]
conteo = {c: sum(1 for a in vistos if SEMAFORO[a][3] == c)
          for c in ('Verde', 'Amarillo', 'Rojo')}
bm = COEFICIENTES['brecha_media']
cb = COEFICIENTES['cobertura']
graduados = int(f.graduados.sum())

# ==========================================================================
# 1 — Lo que muestran los datos
# ==========================================================================
seccion('cifras', 'Lo que muestran los datos',
        'Cuatro cifras resumen el diagnóstico. Las tres primeras son fijas y vienen '
        'del documento; la cuarta responde a los filtros.')

k1, k2, k3, k4 = st.columns(4, gap='small')
with k1:
    html(f"""<div class="tarjeta">
      <div class="rotulo-mono">Brecha media</div>
      <div class="cifra">{num(bm['coef'], 1, signo=True)}<small> pp</small></div>
      <div class="pie">A favor de la modalidad virtual, descontando campo y cohorte.
        IC 95&nbsp;%: {num(bm['ic'][0], 1)} a {num(bm['ic'][1], 1)}.</div></div>""")
with k2:
    html(f"""<div class="tarjeta">
      <div class="rotulo-mono">Semáforo</div>
      <div class="cifra"><span style="color:{ESTADO['Verde']}">{conteo['Verde']}</span><small> · </small><span
        style="color:#c98a00">{conteo['Amarillo']}</span><small> · </small><span
        style="color:{ESTADO['Rojo']}">{conteo['Rojo']}</span></div>
      <div class="pie">Campos en verde, amarillo y rojo. El único rezago verificado está en TIC.</div></div>""")
with k3:
    html(f"""<div class="tarjeta">
      <div class="rotulo-mono">Acreditación virtual</div>
      <div class="cifra">{num(cb['virtual'])}<small> %</small></div>
      <div class="pie">De los programas virtuales con graduados, frente a
        {num(cb['presencial'])}&nbsp;% de los presenciales.</div></div>""")
with k4:
    html(f"""<div class="tarjeta">
      <div class="rotulo-mono">Egresados en el filtro</div>
      <div class="cifra" style="font-size:clamp(24px, 2.3vw, 38px)">{num(graduados, 0)}</div>
      <div class="pie">En {len(sel_cohortes)} cohorte{'s' if len(sel_cohortes) != 1 else ''}
        y {len(sel_campos)} campo{'s' if len(sel_campos) != 1 else ''}.</div></div>""")

# ==========================================================================
# 2 — El semáforo por campo
# ==========================================================================
seccion('semaforo', 'El semáforo por campo',
        'La inserción laboral no es homogénea: el promedio nacional esconde campos con '
        'ventaja virtual amplia, campos sin diferencia y un campo con rezago. El color '
        'resume lo que dice el intervalo de confianza.')

filas = sorted([(a, *SEMAFORO[a]) for a in vistos], key=lambda x: -x[1])
izq, der = st.columns([1.75, 1], gap='large')
with izq:
    html(''.join(
        f'<div class="fila"><span class="n">{i:02d}</span>'
        f'<span class="campo">{corto(a)}<small>IC 95 % {num(lo, 1)} a {num(hi, 1)}</small></span>'
        f'<span class="valor">{num(b, 1, signo=True)} pp</span>{ficha(cat)}</div>'
        for i, (a, b, lo, hi, cat) in enumerate(filas, start=1)))
with der:
    reglas = ''.join(
        f'<div class="regla"><div>{ficha(cat)}'
        f'<div class="conteo" style="color:{ESTADO[cat] if cat != "Amarillo" else "#c98a00"}">'
        f'{conteo[cat]}</div></div><p>{texto}</p></div>'
        for cat, texto in (
            ('Rojo', 'El intervalo queda entero por debajo de cero: rezago '
                     'estadísticamente distinguible de la modalidad virtual.'),
            ('Amarillo', 'El intervalo cruza el cero o la ventaja es menor de cinco '
                         'puntos: no hay diferencia que se pueda afirmar.'),
            ('Verde', 'El intervalo queda entero por encima de cero y la ventaja '
                      'alcanza al menos cinco puntos.')))
    html(f"""<div class="lectura">
      <div class="rotulo-mono">Cómo se lee</div>
      <span class="pastilla">Regla de clasificación</span>
      {reglas}
    </div>""")

with st.container(key='tarjeta_bosque'):
    html('<div class="rotulo-mono">Brecha estimada e intervalo de confianza del 95 %</div>')
    filas_g = sorted(filas, key=lambda x: x[1])
    fig = go.Figure()
    for cat in ('Rojo', 'Amarillo', 'Verde'):
        sub = [x for x in filas_g if x[4] == cat]
        if not sub:
            continue
        fig.add_trace(go.Scatter(
            x=[x[1] for x in sub], y=[corto(x[0]) for x in sub],
            error_x=dict(type='data', symmetric=False,
                         array=[x[3] - x[1] for x in sub],
                         arrayminus=[x[1] - x[2] for x in sub],
                         color=ESTADO[cat], thickness=2.2, width=7),
            mode='markers',
            marker=dict(size=14, color=ESTADO[cat], symbol=FORMA[cat],
                        line=dict(width=2, color=TARJETA)),
            name=cat,
            customdata=[[x[2], x[3]] for x in sub],
            hovertemplate='<b>%{y}</b><br>Brecha %{x:.2f} pp<br>'
                          'IC 95 %: %{customdata[0]:.2f} a %{customdata[1]:.2f}'
                          '<extra></extra>'))
    # rótulos directos del valor, fuera del intervalo para no cruzar la línea del cero
    lado_der = [x for x in filas_g if x[3] >= 0]
    lado_izq = [x for x in filas_g if x[3] < 0]
    for grupo, pos, dx, k in ((lado_der, 'middle right', 1.2, 3), (lado_izq, 'middle left', -1.2, 2)):
        if grupo:
            fig.add_trace(go.Scatter(
                x=[x[k] + dx for x in grupo], y=[corto(x[0]) for x in grupo],
                mode='text', text=[f'<b>{num(x[1], 1, signo=True)}</b>' for x in grupo],
                textposition=pos, textfont=dict(family=DISPLAY, size=13, color=TINTA),
                showlegend=False, hoverinfo='skip'))
    fig.add_vline(x=0, line_dash='dot', line_color=TINTA_3, line_width=1.5)
    lienzo(fig, 'Diferencia en la tasa de cotización dependiente (pp)',
           alto=max(360, 52 * len(filas_g)))
    fig.update_xaxes(range=[-15, 40])
    fig.update_yaxes(gridcolor='rgba(0,0,0,0)', linecolor='rgba(0,0,0,0)', ticks='',
                     tickfont=dict(family=DISPLAY, size=13, color=TINTA))
    st.plotly_chart(fig, width='stretch', config=PLOTLY_CONF)

with st.expander('Ver como tabla'):
    st.dataframe(
        pd.DataFrame([(corto(a), b, lo, hi, c) for a, b, lo, hi, c in filas],
                     columns=['Campo', 'Brecha (pp)', 'IC 95 % inferior',
                              'IC 95 % superior', 'Semáforo']),
        hide_index=True, width='stretch',
        column_config={
            'Brecha (pp)': st.column_config.NumberColumn(format='%.2f'),
            'IC 95 % inferior': st.column_config.NumberColumn(format='%.2f'),
            'IC 95 % superior': st.column_config.NumberColumn(format='%.2f')})

# ==========================================================================
# 3 — Evolución por cohorte
# ==========================================================================
seccion('evolucion', 'Evolución por cohorte',
        'La ventaja de los egresados virtuales aparece en las cinco cohortes y no se '
        'invierte en ningún año, ni siquiera antes de la pandemia.')

ev = (f.groupby(['cohorte', 'modalidad'])[['graduados', 'cotizantes']].sum()
      .assign(tasa=lambda d: 100 * d.cotizantes / d.graduados).reset_index())
series = {m: ev[ev.modalidad == m].sort_values('cohorte')
          for m in ('Presencial', 'Virtual') if not ev[ev.modalidad == m].empty}

c_lineas, c_barras = st.columns([1.55, 1], gap='medium')
with c_lineas:
    with st.container(key='tarjeta_lineas'):
        html('<div class="rotulo-mono">Tasa de cotización dependiente (%)</div>')
        fig = go.Figure()
        if len(series) == 2:
            p, v = series['Presencial'], series['Virtual']
            fig.add_trace(go.Scatter(x=p.cohorte, y=p.tasa, mode='lines',
                                     line=dict(width=0), showlegend=False, hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=v.cohorte, y=v.tasa, mode='lines', fill='tonexty',
                                     fillcolor='rgba(20,20,19,0.06)', line=dict(width=0),
                                     showlegend=False, hoverinfo='skip'))
        for mod, color in (('Presencial', AZUL), ('Virtual', NARANJA)):
            if mod not in series:
                continue
            s = series[mod]
            fig.add_trace(go.Scatter(
                x=s.cohorte, y=s.tasa, name=mod, mode='lines+markers',
                line=dict(color=color, width=3),
                marker=dict(size=10, color=color, line=dict(width=2, color=TARJETA)),
                hovertemplate='Cohorte %{x}<br>' + mod + ': %{y:.1f} %<extra></extra>'))
            fig.add_trace(go.Scatter(
                x=[s.cohorte.iloc[-1]], y=[s.tasa.iloc[-1]], mode='text',
                text=[f'  <b>{mod}</b> {num(s.tasa.iloc[-1])} %'], textposition='middle right',
                textfont=dict(family=DISPLAY, size=13, color=color),
                showlegend=False, hoverinfo='skip'))
        lienzo(fig, 'Cohorte de graduación', '', alto=380, leyenda=False)
        fig.update_xaxes(tickmode='array', tickvals=sel_cohortes,
                         range=[min(sel_cohortes) - 0.25, max(sel_cohortes) + 1.35])
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONF)

with c_barras:
    with st.container(key='tarjeta_barras'):
        html('<div class="rotulo-mono">Brecha observada (pp)</div>')
        br = ev.pivot(index='cohorte', columns='modalidad', values='tasa')
        if {'Virtual', 'Presencial'} <= set(br.columns):
            br['brecha'] = br['Virtual'] - br['Presencial']
            fb = go.Figure()
            fb.add_trace(go.Bar(
                x=br.index.astype(str), y=br.brecha, width=0.56,
                marker=dict(color=NARANJA, cornerradius=6, line=dict(width=0)),
                text=[f'<b>{num(x, 1, signo=True)}</b>' for x in br.brecha],
                textposition='outside', textfont=dict(family=DISPLAY, size=13, color=TINTA),
                cliponaxis=False,
                hovertemplate='Cohorte %{x}<br>Brecha %{y:.2f} pp<extra></extra>'))
            lienzo(fb, 'Cohorte de graduación', '', alto=380, leyenda=False)
            fb.update_yaxes(range=[0, max(br.brecha.max() * 1.3, 1)])
            st.plotly_chart(fb, width='stretch', config=PLOTLY_CONF)
        else:
            html('<p class="nota">Seleccione las dos modalidades para ver la brecha.</p>')

nota('Brecha observada, antes de cualquier control por composición. El máximo de la '
     'cohorte 2019 coincide con un seguimiento hecho en 2020: el confinamiento golpeó de '
     'forma desigual a los sectores donde trabaja cada grupo. Por eso el Anexo 1 repite la '
     'estimación sin esas cohortes.')

with st.expander('Ver como tabla'):
    t = ev.copy()
    t['tasa'] = t['tasa'].round(2)
    st.dataframe(t.rename(columns={'cohorte': 'Cohorte', 'modalidad': 'Modalidad',
                                   'graduados': 'Graduados', 'cotizantes': 'Cotizantes',
                                   'tasa': 'Tasa (%)'}),
                 hide_index=True, width='stretch')

# ==========================================================================
# 4 — Dónde llega la acreditación
# ==========================================================================
seccion('cobertura', 'Dónde llega la acreditación',
        'El instrumento con que el Estado certifica la calidad casi no toca la oferta '
        'virtual. Ningún campo supera el trece por ciento.')

cob = cobertura_virtual(programa)
puntos = [(a, SEMAFORO[a][0],
           float(cob.loc[a, 'cobertura']) if a in cob.index else 0.0,
           int(cob.loc[a, 'programas']) if a in cob.index else 0,
           SEMAFORO[a][3]) for a in vistos]

DESPLAZ = {'Salud Y Bienestar': 9, 'Ciencias Naturales, Matematicas Y Estadistica': -9,
           'Arte Y Humanidades': -13, 'Ingenieria, Industria Y Construccion': 2}


def radio(n_programas):
    return max(13, min(34, 11 + n_programas / 7))


with st.container(key='tarjeta_cobertura'):
    html('<div class="rotulo-mono">Brecha frente a programas virtuales acreditados · '
         'tamaño = número de programas virtuales</div>')
    fig = go.Figure()
    fig.add_hrect(y0=-9, y1=0, fillcolor='rgba(208,59,59,0.06)', line_width=0, layer='below')
    for cat in ('Rojo', 'Amarillo', 'Verde'):
        sub = [p for p in puntos if p[4] == cat]
        if not sub:
            continue
        fig.add_trace(go.Scatter(
            x=[p[2] for p in sub], y=[p[1] for p in sub], mode='markers',
            marker=dict(size=[radio(p[3]) for p in sub], color=ESTADO[cat],
                        symbol=FORMA[cat], opacity=0.92, line=dict(width=2, color=TARJETA)),
            name=cat,
            customdata=[[corto(p[0]), p[3]] for p in sub],
            hovertemplate='<b>%{customdata[0]}</b><br>Cobertura %{x:.1f} %<br>'
                          'Brecha %{y:.2f} pp<br>%{customdata[1]} programas virtuales'
                          '<extra></extra>'))
    for a, b, cv, npro, cat in puntos:
        fig.add_annotation(x=cv, y=b, text=corto(a), showarrow=False,
                           xanchor='left', yanchor='middle',
                           xshift=radio(npro) / 2 + 7, yshift=DESPLAZ.get(a, 0),
                           font=dict(family=DISPLAY, size=12, color=TINTA_2))
    fig.add_hline(y=0, line_dash='dot', line_color=TINTA_3, line_width=1.5)
    fig.add_annotation(x=0.35, y=-8.2, text='rezago verificado con cobertura casi nula',
                       showarrow=False, xanchor='left',
                       font=dict(family=MONO, size=11, color='#a02e2e'))
    lienzo(fig, 'Programas virtuales acreditados en el campo (%)',
           'Brecha de vinculación formal (pp)', alto=480)
    fig.update_xaxes(range=[-0.6, 13])
    fig.update_yaxes(range=[-10, 31])
    st.plotly_chart(fig, width='stretch', config=PLOTLY_CONF)

nota('<b>Lectura de política.</b> La franja inferior —rezago verificado y cobertura casi '
     'nula— concentra la prioridad, y en ella solo aparece TIC. La acreditación no ha '
     'llegado a la modalidad cuya calidad se discute.')

with st.expander('Ver como tabla'):
    st.dataframe(
        pd.DataFrame([(corto(p[0]), p[1], p[2], p[3], p[4]) for p in puntos],
                     columns=['Campo', 'Brecha (pp)', 'Cobertura (%)',
                              'Programas virtuales', 'Semáforo']),
        hide_index=True, width='stretch',
        column_config={
            'Brecha (pp)': st.column_config.NumberColumn(format='%.2f'),
            'Cobertura (%)': st.column_config.NumberColumn(format='%.1f')})

# ==========================================================================
# 5 — Lo que no se puede saber (incertidumbre, no simulación)
# ==========================================================================
ident = COEFICIENTES['interaccion']['programas_identificantes']
seccion('incertidumbre', 'Lo que los datos no permiten saber',
        f'Si la acreditación cerraría o abriría la brecha no se puede estimar: solo {ident} '
        'programas virtuales acreditados sostienen el cálculo. Esta vista muestra '
        'incertidumbre, no escenarios.')

inf, sup = COEFICIENTES['interaccion']['ic']
coef = COEFICIENTES['interaccion']['coef']
obs_min, obs_max = COEFICIENTES['rango_observado_acreditacion']
xs = [i / 2 for i in range(0, 101)]

c1, c2, c3 = st.columns(3, gap='small')
for col, rot, cif, pie in (
    (c1, 'Coeficiente de interacción', f'{num(coef, 2, signo=True)}<small> pp</small>',
     'Estimación puntual, sin significancia estadística.'),
    (c2, 'Intervalo de confianza 95 %', f'{num(inf, 1)} a {num(sup, 1)}',
     'Incluye el cero y ambos signos: el efecto no está identificado.'),
    (c3, 'Programas que lo identifican', f'{ident}',
     'Virtuales acreditados en todo el país, cohortes 2021 y 2022.'),
):
    with col:
        html(f'<div class="tarjeta"><div class="rotulo-mono">{rot}</div>'
             f'<div class="cifra" style="font-size:36px">{cif}</div>'
             f'<div class="pie">{pie}</div></div>')

st.write('')
with st.container(key='tarjeta_incertidumbre'):
    html('<div class="rotulo-mono">Cambio implicado en la brecha según la cobertura de la '
         'acreditación (pp)</div>')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs + xs[::-1],
        y=[sup * x / 100 for x in xs] + [inf * x / 100 for x in xs[::-1]],
        fill='toself', fillcolor='rgba(235,104,52,0.16)', line=dict(width=0),
        name='Intervalo de confianza del 95 %', hoverinfo='skip'))
    fig.add_trace(go.Scatter(
        x=xs, y=[coef * x / 100 for x in xs], mode='lines',
        line=dict(color=NARANJA, width=2.5, dash='dot'),
        name='Estimación puntual (no significativa)',
        hovertemplate='Cobertura %{x:.0f} %<br>Cambio implicado %{y:.2f} pp<extra></extra>'))
    fig.add_vrect(x0=obs_min, x1=obs_max, fillcolor='rgba(42,120,214,0.12)', line_width=0,
                  layer='below')
    fig.add_annotation(x=(obs_min + obs_max) / 2, y=0.965, yref='paper', yanchor='top',
                       text='rango<br>observado', showarrow=False, align='center',
                       font=dict(family=MONO, size=11, color='#1c5cab'))
    fig.add_hline(y=0, line_color=BASE, line_width=1.5)
    lienzo(fig, 'Cobertura de la acreditación en la oferta virtual (%)', '', alto=420)
    fig.update_xaxes(range=[0, 50])
    st.plotly_chart(fig, width='stretch', config=PLOTLY_CONF)

nota('La franja azul es la cobertura que existe hoy. A su derecha todo es extrapolación, '
     'y la franja naranja se ensancha porque la incertidumbre crece con la distancia a lo '
     'observado. Mientras la cobertura siga donde está, la pregunta no tiene respuesta.')

# ==========================================================================
# 6 — Qué se propone
# ==========================================================================
seccion('propuesta', 'Qué se propone',
        'Una estrategia dual que no depende del coeficiente que no se pudo estimar y que '
        'puede ejecutarse con los instrumentos que la normativa vigente ya contiene.')

PROPUESTA = (
    ('Conectar la información de resultados laborales', 'Primero',
     'Alternativa B. Publicar los resultados del Observatorio Laboral por programa, '
     'modalidad y campo, y llevarlos al aspirante en el momento en que elige. Puede '
     'desplegarse en uno o dos años.'),
    ('Adecuar los estándares a la modalidad', 'En paralelo',
     'Alternativa A. Criterios propios de la formación virtual en la acreditación, '
     'empezando por TIC, único campo en rojo, y por los campos sin oferta virtual '
     'acreditada.'),
    ('Fortalecer la inserción desde la normativa vigente', 'Sin ley nueva',
     'Evidenciar el programa de egresados y el factor de egresados con datos del '
     'Observatorio; ofrecer prácticas y contratos de aprendizaje compatibles con la '
     'modalidad, y pilotear la formación virtual-dual en TIC.'),
    ('Umbral con consecuencia regulatoria', 'Mediano plazo',
     'Alternativa C. Solo cuando las dos primeras medidas hayan producido información '
     'suficiente, por su costo en equidad y en viabilidad.'),
)
html(''.join(
    f'<div class="fila"><span class="n">{i:02d}</span>'
    f'<span class="campo">{titulo}<small class="texto">{texto}</small></span>'
    f'<span class="ficha" style="background:{TINTA};color:{PAPEL}">{plazo.upper()}</span></div>'
    for i, (titulo, plazo, texto) in enumerate(PROPUESTA, start=1)))

nota('La recomendación es la misma en los tres escenarios que el documento previó antes de '
     'estimar: conectar la información no opera a través de la acreditación, sino en '
     'paralelo a ella.')

# ==========================================================================
# 7 — Fuentes y calidad del panel
# ==========================================================================
seccion('fuentes', 'Fuentes y calidad del panel',
        'De dónde salen las cifras y qué se verificó antes de usarlas.')

f_cel, n_cel = calidad['celdas']
f_pro, n_pro = calidad['programas']
a1, a2 = st.columns(2, gap='medium')
with a1:
    html(f"""<div class="tarjeta">
      <div class="rotulo-mono">Fuentes</div>
      <span class="pastilla">Registros administrativos públicos</span>
      <div class="pie">Sistema Nacional de Información de la Educación Superior (SNIES),
        archivos de graduados. Observatorio Laboral para la Educación, indicador de ingreso
        base de cotización de dependientes. {VERSION_PANEL}. Los coeficientes y la
        clasificación vienen de los anexos 1 y 4 del policy paper y no se reestiman al
        ejecutar el tablero.</div></div>""")
with a2:
    html(f"""<div class="tarjeta">
      <div class="rotulo-mono">Control de calidad</div>
      <span class="pastilla">{num(n_cel, 0)} celdas · {num(n_pro, 0)} programas</span>
      <div class="pie">Celdas con tasa fuera de [0, 1]: {f_cel}. Programas: {f_pro}
        ({num(100 * f_pro / n_pro, 2)} %), todos con muy pocos graduados y registros de
        cotizantes que incluyen promociones anteriores. Están documentados en el Anexo 2 y
        no afectan las estimaciones, que se hacen por celda y ponderadas por graduados.</div></div>""")

html('<p class="ceja" style="margin-top:64px">Duvan Fernando Caleño Henao · '
     'Economista · Administrador público · Bogotá, 2026</p>')
