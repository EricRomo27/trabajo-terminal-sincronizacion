import unittest
import pandas as pd
import numpy as np

from pages import Matriz_de_sincronía as matriz_module
from pages import Análisis_comparativo as comparativo_module
from utils.peak_matching import calcular_desfases_entre_picos, resumir_desfases
from utils.peak_matching_access import resumir_desfases_seguro


class MatrizVarianzaTests(unittest.TestCase):
    def test_varianza_para_picos_alineados_es_casi_nula(self):
        fechas = pd.date_range('2020-01-01', periods=180, freq='D')
        serie_base = np.zeros(len(fechas))
        for posicion in (30, 90, 150):
            serie_base[posicion] = 100

        df = pd.DataFrame({
            'PM10': serie_base,
            'PM2_5': serie_base,
        }, index=fechas)

        matriz = matriz_module.calcular_matriz.__wrapped__(df, 'varianza')
        valor_varianza = matriz.loc['PM10', 'PM2_5']

        self.assertAlmostEqual(valor_varianza, 0.0, places=6)

    def test_picos_desalineados_fuera_de_ventana_no_distorsionan(self):
        fechas = pd.date_range('2020-01-01', periods=365, freq='D')
        serie_maestro = np.zeros(len(fechas))
        serie_esclavo = np.zeros(len(fechas))

        serie_maestro[[30, 120, 210]] = 50
        serie_esclavo[[30, 120, 330]] = 50  # último pico muy separado

        df = pd.DataFrame({
            'MAESTRO': serie_maestro,
            'ESCLAVO': serie_esclavo,
        }, index=fechas)

        matriz = matriz_module.calcular_matriz.__wrapped__(df, 'varianza')
        valor_varianza = matriz.loc['MAESTRO', 'ESCLAVO']

        self.assertLess(valor_varianza, 1.0)


class AnalisisComparativoTests(unittest.TestCase):
    def test_varianza_cero_en_series_identicas(self):
        fechas = pd.date_range('2021-01-01', periods=120, freq='D')
        serie = pd.Series(np.sin(np.linspace(0, 6, len(fechas))), index=fechas, name='O3')

        resultados = comparativo_module.realizar_analisis_completo(serie, serie, serie.index)

        self.assertAlmostEqual(resultados['varianza_desfase'], 0.0, places=6)
        self.assertEqual(resultados['pares_descartados'], [])


class PeakMatchingTests(unittest.TestCase):
    def test_empareja_picos_mas_cercanos(self):
        fechas_maestro = pd.to_datetime(['2020-01-01', '2020-01-10', '2020-01-20'])
        fechas_esclavo = pd.to_datetime(['2020-01-02', '2020-01-11', '2020-04-01'])

        desfases = calcular_desfases_entre_picos(fechas_maestro, fechas_esclavo, ventana_maxima_dias=15)

        self.assertEqual(desfases, [1, 1])  # El último pico queda fuera de la ventana

    def test_return_pares_devuelve_detalle(self):
        fechas_maestro = pd.to_datetime(['2020-03-01', '2020-04-15'])
        fechas_esclavo = pd.to_datetime(['2020-03-03', '2020-05-10'])

        desfases, pares = calcular_desfases_entre_picos(
            fechas_maestro, fechas_esclavo, ventana_maxima_dias=40, return_pares=True
        )

        self.assertEqual(desfases, [2, 25])
        self.assertEqual(
            pares,
            [
                (pd.Timestamp('2020-03-01'), pd.Timestamp('2020-03-03'), 2),
                (pd.Timestamp('2020-04-15'), pd.Timestamp('2020-05-10'), 25),
            ],
        )

    def test_resumir_desfases_filtra_desviaciones_extremas(self):
        fechas_maestro = pd.to_datetime(['2020-01-01', '2020-03-01', '2020-06-01'])
        fechas_esclavo = pd.to_datetime(['2020-01-02', '2020-03-03', '2020-07-30'])

        resumen = resumir_desfases(
            fechas_maestro,
            fechas_esclavo,
            ventana_busqueda=120,
            ventana_confiable=45,
        )

        self.assertEqual(resumen['desfases_validos'], [1, 2])
        self.assertEqual([desfase for *_, desfase in resumen['pares_descartados']], [59])
        self.assertAlmostEqual(resumen['varianza'], 0.25, places=6)


class PeakMatchingAccessTests(unittest.TestCase):
    def test_resumen_seguro_retorna_metricas(self):
        fechas = pd.to_datetime(['2022-01-01', '2022-02-01', '2022-03-01'])

        resumen = resumir_desfases_seguro(
            fechas,
            fechas,
            ventana_busqueda=60,
            ventana_confiable=30,
        )

        self.assertIn('varianza', resumen)
        self.assertEqual(resumen['varianza'], 0.0)
        self.assertEqual(resumen['pares_descartados'], [])

if __name__ == '__main__':
    unittest.main()
