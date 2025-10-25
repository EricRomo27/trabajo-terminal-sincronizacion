import unittest

from utils import downloads, ui


class DownloadHelpersTest(unittest.TestCase):
    def test_helpers_expuestos_en_modulos(self):
        self.assertTrue(callable(downloads.boton_descarga_plotly))
        self.assertTrue(callable(downloads.boton_descarga_altair))
        self.assertTrue(callable(ui.boton_descarga_plotly))
        self.assertTrue(callable(ui.boton_descarga_altair))

    def test_invocacion_fuera_de_runtime_no_falla(self):
        # Al ejecutarse fuera del runtime de Streamlit, los helpers deben salir sin lanzar errores.
        downloads.boton_descarga_plotly(object(), "grafica.png")
        downloads.boton_descarga_altair(object(), "grafica.html")


if __name__ == "__main__":
    unittest.main()
