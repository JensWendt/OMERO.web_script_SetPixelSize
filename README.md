## OMERO.web script for setting pixel sizes
Very simple OMERO.web script that is capable of setting pixel sizes for X, Y and Z dimensions of OMERO Images. It can iterate over all Images in an OMERO Project, Dataset, Screen or Plate.

The User can decide if existing values get overwritten. By default they will be. If no pixel size exists for a dimension, it will always be set to a new given value.

Values for X, Y and Z can be set independently. By default, if a value for X is set, it will be used for Y and Z as well.

If an Image does not have more than one Z-stack the pixel size for Z will not be set even if a value is given.
