import unittest
import pandas as pd
import numpy as np

from pages import Matriz_de_sincronía as matriz_module


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


if __name__ == '__main__':
    unittest.main()
