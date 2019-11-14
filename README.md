# Meta Info Tools

Validates objects described with the MetaInfo format.
Meta info is a format initially developed in the [NOMAD Center of Excellence](https://nomad-coe.eu) to describe data.
See [https://kitabi.eu/nomad/metainfo/]() for more information.
Meta info describes hierarchical data for both humans and computer.
The main aim is to have a flexible ad extensible definition.
[nomad-meta-info](https://github.com/fawzi/nomad-meta-info) contains the definition of the meta info used in NOMAD to describe atomistic simulations, in particular ab-initio simulations.
The actual releases are avalible at [https://kitabi.eu/nomad/metainfo/releases/](https://kitabi.eu/nomad/metainfo/releases)

```bash
python -m metainfo.meta_tool --help
```
(or python3 if your python still refers to python 2.x)
describes the various option of the meta tools.
It can be used to generates an exploded or reformatted version of a dictionary, check a dictionary, or generate documentation for it.
The cascade command does all those things if the files are put in a standard directory format (does the exploded dictionaries first, reformats them, then moves to the single dictionaries, regenerating them from the exploded version, reformatting them otherwise, finally performs checks and generates documentation for all available dictionaries.
Python modules and json schemas are also generated.
