# hpc-scripts-lumi

The namespace package `hpc-scripts-santis` is meant to ease the configuration, build and run of
selected software on the Santis vCluster of the Alps infrastructure.

Some template dotfiles are also provided in `dotfiles/`, to be symlinked in your `$HOME` folder.

### Quick start guide

```bash
# clone the repository into home
~$ git clone -b namespaces git@github.com:stubbiali/hpc-scripts.git

# install the package in editable mode using `uv tool`
~$ uv tool install -e hpc-scripts/hpc-scripts-santis

# optional: set the env vars HPCS_APPS_ROOT_DIR and HPCS_SCRIPTS_ROOT_DIR, pointing to the directories
# containing the source code of the target software and all generated bash scripts, respectively
# we suggest exporting these env vars in your .bashrc file
~$ export HPCS_APPS_ROOT_DIR=$SCRATCH
~$ export HPCS_SCRIPTS_ROOT_DIR=$SCRATCH
```

### Supported software

* [PMAP](https://github.com/PMAP-Project/PMAP)
* [ecRad](https://github.com/ecmwf-ifs/ecrad)
* [ecRad-versions](https://github.com/PMAP-Project/ecRad-versions)

### Console scripts

The following executable commands are installed as part of this package:

* `make_build_spack_env_ecrad`
* `make_build_spack_env_pmap`
* `make_prepare_ecrad`
* `make_prepare_ecrad_versions`
* `make_prepare_mpi`
* `make_prepare_pmap`
* `pysalloc`
* `sbatch_ecrad_versions` (*)
* `sbatch_pmap` (*)

Pass the `-h` flag to any command to get its synopsis.

**Remark**: commands marked with an asterisk  do not accept command-line arguments. In order to alter the default parameters, the user should modify the corresponding Python module in `src/hpc-scripts/santis`. The customizable section is enclosed within `# >>>: config: start` and `# >>> config: end`.

### Example

Installing PMAP using the uenv `prgenv-gnu/26.3:v1`, and run a benchmark on one GPU.

```bash
# pull the uenv image (if not done yet)
~$ uenv image pull prgenv-gnu/26.3:v1

# start the uenv as an upstream spack instance
~$ uenv start prgenv-gnu/26.3:v1 --view=spack

# clone uenv-spack (if not done yet)
~$ git clone git@github.com:eth-cscs/uenv-spack.git

# add uenv-spack to the path (you might want to do this in your .bashrc file)
~$ export PATH=/users/$USER/uenv-spack:$PATH

# create a spack env for pmap
~$ make_build_spack_env_pmap
~$ . $HPCS_SCRIPTS_ROOT_DIR/build_spack_env_pmap.sh

# build and install the main branch of pmap in a dedicated virtual environment, jump into the project
#  directory and activate the environment
~$ make_prepare_pmap
~$ . $HPCS_SCRIPTS_ROOT_DIR/prepare_pmap.sh

# allocate one GPU node on the normal partition for an hour
(...) <HPCS_APPS_ROOT_DIR>/pmap/main$ pysalloc --partition=normal --time=01:00:00

# refresh the script prepare_pmap.sh, so to bypass the creation of a new virtual environment
<HPCS_APPS_ROOT_DIR>/pmap/main$ make_prepare_pmap
<HPCS_APPS_ROOT_DIR>/pmap/main$ . $HPCS_SCRIPTS_ROOT_DIR/prepare_pmap.sh

# run the moist baroclinic wave benchmark
(...) <HPCS_APPS_ROOT_DIR>/pmap/main$ OMP_NUM_THREADS=64 GT_BACKEND=dace:gpu srun --ntasks=1 --cpus-per-task=64 --gpus-per-task=1 pmap config/baroclinic_wave_sphere_moist.yml
```
