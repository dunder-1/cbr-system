import csv
import streamlit as st
from model import *
from similarity import *

st.title("CBR System")

case_base = CaseBase.from_csv(
    "data/used_cars_flat.csv",
    problem_fields = ("Price", "Body", "Color"),
    solution_fields = ("Manufacturer", "Model"),
    encoding = "utf-8",
    delimiter = ";",
    set_int = True
)
with open("data/symbolic_sims.csv") as file:
    case_base.add_symbolic_sim(
        field = "Body",
        similarity_matrix = {
            line["Body"]: {k:float(v) for k, v in line.items() if k != "Body"}
            for line in csv.DictReader(file, skipinitialspace=True)
        }
    )




query = Query.from_problems(
    Price = st.number_input("Enter price:", 0, step = 1000),
    Body = st.selectbox("Choose car body:", case_base.get_values_by_field("Body"))
)
# sim_funcs: manhattan_sim, euclid_sim

retrieved = case_base.retrieve(
    query,
    Price = euclid_sim,
    Body = symbolic_sim
)

st.write(retrieved)