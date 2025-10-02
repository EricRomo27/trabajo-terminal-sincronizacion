import pandas as pd
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# --- 1. LECTURA Y SUAVIZADO (Sin cambios) ---
nombre_db = 'contaminantes.db'
conn = sqlite3.connect(nombre_db)
df = pd.read_sql_query("SELECT * FROM calidad_aire", conn, 
                         parse_dates=['Fecha'], index_col='Fecha')
conn.close()

df_suavizado = df.rolling(window=30, center=True, min_periods=1).mean()
serie1_suavizada = df_suavizado['NEPM10']
serie2_suavizada = df_suavizado['NEPM2']

# --- 2. ANÁLISIS BASADO EN PICOS (Sin cambios) ---
print("--- Método 1: Análisis Basado en Picos ---")
# (El código de esta sección no cambia)
distancia_entre_picos = 30
min_altura_pico1 = serie1_suavizada.mean()
min_altura_pico2 = serie2_suavizada.mean()
picos1, _ = find_peaks(serie1_suavizada, distance=distancia_entre_picos, height=min_altura_pico1)
picos2, _ = find_peaks(serie2_suavizada, distance=distancia_entre_picos, height=min_altura_pico2)
fechas_picos1 = serie1_suavizada.index[picos1]
fechas_picos2 = serie2_suavizada.index[picos2]
desfases = [] 
for fecha_pico1 in fechas_picos1:
    diferencias_temporales = np.abs((fechas_picos2 - fecha_pico1).days)
    if len(diferencias_temporales) > 0:
        indice_pico_cercano = np.argmin(diferencias_temporales)
        fecha_pico_cercano = fechas_picos2[indice_pico_cercano]
        desfase = (fecha_pico1 - fecha_pico_cercano).days
        desfases.append(desfase)
desfases = np.array(desfases)
if len(desfases) > 0:
    varianza_desfase = np.var(desfases)
    print(f"Varianza del desfase entre picos: {varianza_desfase:.2f}")

# --- 3. ANÁLISIS BASADO EN DERIVADAS (ACTUALIZADO) ---
print("\n--- Método 2: Análisis Basado en Derivadas Suavizadas ---")

# Calculamos la primera derivada
derivada1 = np.gradient(serie1_suavizada.values)
derivada2 = np.gradient(serie2_suavizada.values)

# --- NUEVO: Suavizamos la derivada ---
# Creamos Series de pandas para poder usar .rolling()
s_derivada1 = pd.Series(derivada1, index=df.index)
s_derivada2 = pd.Series(derivada2, index=df.index)

# Aplicamos una media móvil de 15 días a la derivada
derivada1_suavizada = s_derivada1.rolling(window=15, center=True, min_periods=1).mean()
derivada2_suavizada = s_derivada2.rolling(window=15, center=True, min_periods=1).mean()
print("Las derivadas han sido suavizadas con una media móvil de 15 días.")

# Comparamos los signos de las derivadas SUAVIZADAS
sincronia_tendencia = (np.sign(derivada1_suavizada) == np.sign(derivada2_suavizada))
porcentaje_sincronia = np.mean(sincronia_tendencia) * 100

print(f"Las series se mueven en la misma dirección el {porcentaje_sincronia:.2f}% del tiempo.")
if porcentaje_sincronia > 80:
    print("Resultado: Sincronización FUERTE detectada.")
elif porcentaje_sincronia > 60:
    print("Resultado: Sincronización DÉBIL detectada.")
else:
    print("Resultado: No se detecta sincronización significativa.")


# --- 4. VISUALIZACIÓN (Actualizada para mostrar derivadas suavizadas) ---
print("\nGenerando las gráficas de verificación...")
plt.style.use('seaborn-v0_8-whitegrid')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True)

# Gráfica 1: Picos (sin cambios)
ax1.plot(serie1_suavizada, label='PM10 (Suavizado)', color='dodgerblue')
ax1.plot(serie2_suavizada, label='PM2.5 (Suavizado)', color='darkorange')
ax1.plot(serie1_suavizada.iloc[picos1], "x", color='red', markersize=8, label='Picos PM10')
ax1.plot(serie2_suavizada.iloc[picos2], "o", markerfacecolor='none', markeredgecolor='purple', markersize=8, label='Picos PM2.5')
ax1.set_title('Método 1: Detección de Picos', fontsize=16)
ax1.set_ylabel('Índice IMECA (Suavizado)', fontsize=12)
ax1.legend()

# Gráfica 2: Derivadas Suavizadas
ax2.plot(derivada1_suavizada, label='Derivada PM10 (Suavizada)', color='dodgerblue', alpha=0.9)
ax2.plot(derivada2_suavizada, label='Derivada PM2.5 (Suavizada)', color='darkorange', alpha=0.9)
ax2.axhline(0, color='black', linestyle='--', linewidth=1)
ax2.set_title('Método 2: Derivadas Suavizadas de las Series', fontsize=16)
ax2.set_xlabel('Fecha', fontsize=12)
ax2.set_ylabel('Tasa de Cambio (Suavizada)', fontsize=12)
ax2.legend()

plt.tight_layout()
plt.show()