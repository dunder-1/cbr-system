from dataclasses import dataclass
import csv, json
import similarity

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


###############################################################################



@dataclass
class CaseBase:
    """A CaseBase object represents a collection of all known cases"""
    cases: list[Case]
    config: dict[str]
    fields: tuple[str]

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


    def retrieve(self, query: Query, field: str|list, sim_func) -> Case:
        """Search for case most similar to query"""
        
        retrieved = {"case": None, "sim": -1.0}
        for case in self.cases:
            _sim = sim_func(query.problem[field], case.problem[field])
            if _sim > retrieved["sim"]:
                retrieved = {
                    "case": case,
                    "sim": _sim
                }
        
        return retrieved
