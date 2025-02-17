from epd_handler import reduce_data
import pandas as pd
import unittest

class TestEPD(unittest.TestCase):

    def test_wrong_date(self):
        # Datapoint from next Day in Dataset
        df = pd.read_pickle("./Code/tests/data/fix-2021-05-22.pkl")
        reduce_data(df, "step")
    
    def test_nans(self):
        df = pd.read_pickle("./Code/tests/data/fix-2021-04-19.pkl")
        df1 = reduce_data(df, "ept")
        # There should be no NaN's -> Off by one error
        nans = df1[df1.isna().sum(axis=1) > 5]
        self.assertEqual(len(nans), 0)


if __name__ == "__main__":
    unittest.main()