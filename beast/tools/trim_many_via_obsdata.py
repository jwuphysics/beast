#!/usr/bin/env python
"""
Code to create many trimmed model grids for batch runs
  Saves time by only reading the potentially huge modelsed grid once
  and only reads in the noisemodel if it has changed
"""

# system imports
import os
import argparse
import time
import warnings

# BEAST imports
import beast.observationmodel.noisemodel.generic_noisemodel as noisemodel
from beast.fitting import trim_grid
from beast.physicsmodel.grid import SEDGrid
from beast.observationmodel.observations import Observations

# needed only for the obs_colnames to define the observed filternames
from . import datamodel

if __name__ == "__main__":
    # commandline parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "trimfile", help="file with modelgrid, obsfiles, filebase to use"
    )
    args = parser.parse_args()

    start_time = time.clock()

    # read in trim file
    f = open(args.trimfile, "r")
    file_lines = list(f)

    # physics model grid name
    modelfile = file_lines[0].rstrip()

    # get the modesedgrid on which to generate the noisemodel
    print("Reading the model grid files = ", modelfile)
    modelsedgrid = SEDGrid(modelfile)

    new_time = time.clock()
    print("time to read: ", (new_time - start_time) / 60.0, " min")

    old_noisefile = ""
    for k in range(1, len(file_lines)):

        print("\n\n")

        # file names
        noisefile, obsfile, filebase = file_lines[k].split()

        # make sure the proper directories exist
        if not os.path.isdir(os.path.dirname(filebase)):
            os.makedirs(os.path.dirname(filebase))

        # construct trimmed file names
        sed_trimname = filebase + "_seds_trim.grid.hd5"
        noisemodel_trimname = filebase + "_noisemodel_trim.grid.hd5"

        # if these already exist, then continue to the next set of files to trim
        if os.path.isfile(sed_trimname) and os.path.isfile(noisemodel_trimname):
            warnings.warn(
                "trimming already complete for {0}, skipping".format(sed_trimname)
            )
            continue

        print("working on " + sed_trimname)

        start_time = time.clock()

        if noisefile == old_noisefile:
            print("not reading noisefile - same as last")
            # print(noisefile)
        else:
            print("reading noisefile")
            # read in the noise model
            noisemodel_vals = noisemodel.get_noisemodelcat(noisefile)
            old_noisefile = noisefile

        # read in the observed data
        print("getting the observed data")
        obsdata = Observations(
            obsfile, modelsedgrid.filters, obs_colnames=datamodel.obs_colnames
        )
        # trim the model sedgrid
        #   set n_detected = 0 to disable the trimming of models based on
        #      the ASTs (e.g. extrapolations are ok)
        #   this is needed as the ASTs in the NIR bands do not go faint enough
        trim_grid.trim_models(
            modelsedgrid,
            noisemodel_vals,
            obsdata,
            sed_trimname,
            noisemodel_trimname,
            sigma_fac=3.0,
        )

        new_time = time.clock()
        print("time to trim: ", (new_time - start_time) / 60.0, " min")
