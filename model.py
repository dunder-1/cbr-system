from dataclasses import dataclass
import csv, json
from typing import Callable
import similarity as sim

@dataclass
class Entity:
    problem: dict[str]
    solution: dict[str]

    @classmethod
    def from_dict(cls, problem: dict, solution: dict = None):
        return cls(problem, solution) if solution else cls(problem, dict())


class Query(Entity):
    """
    A query is represented as an Entity with:
    - problem (e.g. {"attr_1": 123, "attr_2": 456})
    - soution = {}
    """
    @classmethod
    def from_problems(cls, **problem):
        """Returns a query object by providing problems as keyword arguments"""
        return cls(problem, solution=dict())


class Case(Entity):
    """
    A case is represented as an Entity with:
    - problem (e.g. {"attr_1": 123, "attr_2": 456})
    - solution (e.g. see problem)
    """
    pass

@dataclass
class RetrievedCase(Case):
    similarity: float
    sim_per_field: list[tuple]

    def __str__(self) -> str:
        return " ".join(self.solution.values()).capitalize()

###############################################################################



@dataclass
class CaseBase:
    """A CaseBase object represents a collection of all known cases"""
    cases: list[Case]
    config: dict[str]
    fields: tuple[str]
    __field_infos: dict[str] = None

    def __repr__(self) -> str:
        key_vals = f"cases={len(self.cases)}, fields={list(self.fields.values())}"
        return f"{self.__class__.__name__}({key_vals})"

    def __getitem__(self, key: int) -> Case:
        return self.cases[key]

    def _default_cfg(new_cfg: dict) -> dict:
        """apply default configuration if not overwritten"""
        default_config = {
            "encoding": "utf-8",
            "delimiter": ",",
            "set_int": False
        }.items()

        return {k: v if k not in new_cfg else new_cfg[k] for k, v in default_config}

    def _loader(reader_obj: list[dict], set_int: bool, **kwargs):
        """helper function for reading. Only use internally!"""
        _cases = list()
        for elem in reader_obj:
            _problem, _solution = dict(), dict()
            for key, value in elem.items():
                if key in kwargs["problem_fields"]:
                    _problem[key] = int(value) if set_int and value.isdecimal() else value
                elif key in kwargs["solution_fields"]:
                    _solution[key] = int(value) if set_int and value.isdecimal() else value

            _cases.append(
                Case.from_dict(_problem, _solution)
            )
        
        return _cases

    @classmethod
    def from_csv(cls, path: str, problem_fields: list, solution_fields: list, **cfg):
        """
        read a csv file and load every column by `problem_fields` and `solution_fields`

        Args:
            path: path to a valid .csv file
            problem_fields: list with columns to be considered as problem
            solution_fields: list with columns to be considered as solution
            **cfg: overwrite default configuration (see CaseBase._default_cfg())

        Returns:
            A CaseBase object with:
            - a list of cases
            - the used configuration
            - a tuple with 
              [0] -> problem_fields
              [1] -> solution_fields 
        
        Raises:
            ValueError: if the passed path isnt a .csv file
        """

        if not path.endswith(".csv"):
            raise ValueError("invalid file format:", path)

        cfg = cls._default_cfg(cfg)

        with open(path, encoding=cfg["encoding"]) as file:
            cases = cls._loader(
                reader_obj = csv.DictReader(file, delimiter = cfg["delimiter"]),
                set_int = cfg["set_int"],
                problem_fields = problem_fields,
                solution_fields = solution_fields
            )
        
        return cls(
            cases = cases,
            config = cfg,
            fields = {
                "problem": problem_fields,
                "solution": solution_fields
            }
        )

    @classmethod
    def from_json(cls, path: str, problem_fields: list, solution_fields: list, **cfg):
        """
        read a json file and load every column by `problem_fields` and `solution_fields`

        Args:
            path: path to a valid .json file (array of json-objects)
            problem_fields: list with columns to be considered as problem
            solution_fields: list with columns to be considered as solution
            **cfg: overwrite default configuration (see CaseBase._default_cfg())

        Returns:
            A CaseBase object with:
            - a list of cases
            - the used configuration
            - a tuple with 
              [0] -> problem_fields
              [1] -> solution_fields 
        
        Raises:
            ValueError: if the passed path isnt a .csv file
        """

        if not path.endswith(".json"):
            raise ValueError("invalid file format:", path)

        cfg = cls._default_cfg(cfg)

        with open(path, encoding=cfg["encoding"]) as file:
            cases = cls._loader(
                reader_obj = json.load(file),
                set_int = cfg["set_int"],
                problem_fields = problem_fields,
                solution_fields = solution_fields
            )
        
        return cls(
            cases = cases,
            config = cfg
        )

    def retrieve(self, query: Query, **fields_and_sim_funcs: dict[str, Callable]) -> RetrievedCase:
        """Search for case most similar to query"""
        
        
        r = {"case": None, "sim": -1.0, "sim_per_field": dict()}
        for case in self.cases:

            _sim = 0.0
            _sim_per_field = dict()
            for field, sim_func in fields_and_sim_funcs.items():

                if sim_func in sim.SYMBOLIC_SIMS:
                    field_sim = (
                        field, 
                        sim_func(
                            query.problem[field],
                            case.problem[field],
                            self.get_symbolic_sim(field)
                        )
                    )
                    
                elif sim_func in sim.METRIC_SIMS:
                    field_sim = (
                        field, 
                        sim_func(
                            query.problem[field], 
                            case.problem[field]
                        )
                    )

                _sim_per_field[field_sim[0]] = field_sim[1]
                _sim += field_sim[1]

            if _sim > r["sim"]:
                r = {
                    "case": case,
                    "sim": _sim,
                    "sim_per_field": _sim_per_field
                }
        


        return RetrievedCase(
            r["case"].problem, 
            r["case"].solution,
            r["sim"],
            r["sim_per_field"]
        )

    def get_values_by_field(self, field: str) -> set[str]:
        
        if field not in list(self.fields["problem"]) + list(self.fields["solution"]):
            raise ValueError(f"unknown field {field}")

        distinct_values = set()
        for elem in self.cases:

            if field in elem.problem:
                distinct_values.add(elem.problem[field])

            elif field in elem.solution:
                distinct_values.add(elem.solution[field])

        return distinct_values
            

    def add_symbolic_sim(self, field: str, similarity_matrix: dict):
        """Add hardcoded similarities for symbolic values of `field`
        
        structure of similarity_matrix:
        {
            "Audi": {"Audi": 1.0, "Citroen": 0.4, "Porsche": 0.9},
            "Citroen": {"Audi": 0.4, "Citroen: 1.0, "Porsche": 0.2},
            "Porsche": {"Audi": 0.7, "Citroen": 0.1, "Porsche": 1.0}
        }
        """

        if field not in list(self.fields["problem"]) + list(self.fields["solution"]):
            raise ValueError(f"unknown field {field}")

        self.__field_infos = {
            field: {
                "symbolic_sims": similarity_matrix
            }
        }
        
    def get_symbolic_sim(self, field: str) -> dict[str]:
        return self.__field_infos[field]["symbolic_sims"]