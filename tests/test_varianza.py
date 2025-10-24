import unittest
import pandas as pd
import numpy as np

from pages import Matriz_de_sincronía as matriz_module
from pages import Análisis_comparativo as comparativo_module
from utils.peak_matching import calcular_desfases_entre_picos


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


if __name__ == '__main__':
    unittest.main()
