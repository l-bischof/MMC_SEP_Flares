from epd_handler import reduce_data
import pandas as pd
import unittest

class TestMisc(unittest.TestCase):

    def test_wrong_date(self):
        # Datapoint from next Day in Dataset
        df = pd.read_pickle("./Code/tests/data/fix-2021-05-22.pkl")
        reduce_data(df, "step")


if __name__ == "__main__":
    unittest.main()