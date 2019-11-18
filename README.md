# Meta Info Tools

Validates objects described with the MetaInfo format.
Meta info is a format initially developed in the [NOMAD Center of Excellence](https://nomad-coe.eu) to describe data.
See [NOMAD Archive](https://metainfo.nomad-coe.eu/nomadmetainfo_public/archive.html) and [https://kitabi.eu/nomad/metainfo/](https://kitabi.eu/nomad/metainfo/) for more information.
Meta info describes hierarchical data for both humans and computer.
The main aim is to have a flexible ad extensible definition.
[nomad-meta-info](https://github.com/fawzi/nomad-meta-info) contains the definition of the meta info used in NOMAD to describe atomistic simulations, in particular ab-initio simulations.

Install latest release:
```bash
pip install meta-info-tools
```

Run the command line utility
```bash
python -m meta_info_tools.meta_tool --help
```
(or python3 if your python still refers to python 2.x). It describes the various option of the meta tools.
It can be used to generates an exploded or reformatted version of a dictionary, check a dictionary, or generate documentation for it.
The cascade command does all those things if the files are put in a standard directory format (does the exploded dictionaries first, reformats them, then moves to the single dictionaries, regenerating them from the exploded version, reformatting them otherwise, finally performs checks and generates documentation for all available dictionaries.

## Develop

files are formatted with [python black](https://pypi.org/project/black/)/
Install a local development version from this repository:
```bash
cd <repositoryDir>
pip install -e .
```
