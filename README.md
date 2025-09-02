

## Install

### Conda environment

Use the conda environment to install the pyAEDT package and other useful packages.  

```bash
$ conda create -n pyaedt python=3.11 
$ conda activate pyaedt
$ conda install -c conda-forge pyaedt
$ conda install tqdm ipykernel pyyaml
```

or just call

```bash
$ conda env create -f environment.yml  
```

## How to make your own design?

### Configuration

Parameters to configure the Ansys HFSS are organized as yaml files under the ```config``` directory.
Read the config file in your jupyter notebook using the command below.

```python
from functions import *
config = load_config( "config/CoaxCavity.yaml" )
```

If you add ```eval:``` to the beginning of the string, the string will be converted to values using variables defined in the same layer.
In the example below, ```eval:0.5*(start_frequency + stop_frequency)``` will use ```start_frequency: 10.0``` and ```stop_frequency : 20.0``` to calculate the medium frequency, which will result in ```medium_frequency: 15.0``` in this case.


```yaml
solution:
  name: "CoaxCavity"
  type: "Modal" # "Eigenmode" or "Modal"
  options:
    # Common options
    max_passes     : 20
    max_delta_s    : 0.02
    SaveFields     : True
    # User options
    use_antenna    : False
    use_second_chip: False
    # Eigen mode
    min_frequency: "500MHz" # "2GHz"
    n_mode       : 14
    copy_mesh    : True
    # Driven modal mode
    adaptive_solution_type  : "single" # single, broadband
    start_frequency         : 10.0
    stop_frequency          : 20.0
    medium_frequency        : "eval:0.5*(start_frequency + stop_frequency)"
    adaptive_setup_frequency: "eval:medium_frequency"
    num_of_freq_points      : 201
    n_waveport_mode         : 2
```