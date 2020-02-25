import os
import pandas as pd

basedir = os.path.abspath(os.path.dirname(__file__))

class Lexica():
    def __init__(self):
        age = pd.read_csv(os.path.join(basedir, "lexica/emnlp14age.csv"))
        self.age = {row["term"]: row["weight"] for index, row in age.iterrows()}
        gender = pd.read_csv(os.path.join(basedir, "lexica/emnlp14gender.csv"))
        self.gender = {row["term"]: row["weight"] for index, row in gender.iterrows()}
