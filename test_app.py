import unittest
from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def test_both_structures_and_validation(self):
        app = AppTest.from_file("app.py", default_timeout=20).run()
        self.assertEqual(len(app.exception), 0)
        for index in (0, 1):
            app.selectbox[0].select_index(index)
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.metric), 4)
            self.assertTrue(any("<svg" in block.value for block in app.markdown))
        app.number_input[3].set_value(1.0)
        app.button[0].click().run()
        self.assertEqual(len(app.error), 1)
        self.assertEqual(len(app.metric), 0)


if __name__ == "__main__":
    unittest.main()
