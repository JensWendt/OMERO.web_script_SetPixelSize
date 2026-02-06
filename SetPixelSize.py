# coding=utf-8
"""
-----------------------------------------------------------------------------
  Copyright (C) 2018
  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
------------------------------------------------------------------------------
@author Jens Wendt
<a href="mailto:jens.wendt@uni-muenster.de">jens.wendt@uni-muenster.de</a>
@version 2
"""

import omero
from omero.gateway import BlitzGateway
from omero.rtypes import rstring, rlong
import omero.scripts as scripts
from omero.model.enums import UnitsLength

PARAM_PIXEL_SIZE_X = "Pixel_Size_[X]"
PARAM_PIXEL_SIZE_Y = "Pixel_Size_[Y]_(Only_set_if_different_from_X)"
PARAM_PIXEL_SIZE_Z = "Pixel_Size_[Z]_(Only_set_if_Z_Dimension_exists)"


def get_images(conn, script_params):
    # returns a list of images
    data_type = script_params["Data_Type"]
    ids = script_params["IDs"]
    images = []

    if data_type=="Project":
        projects = conn.getObjects("Project",ids)
        for project in projects:
            for dataset in project.listChildren():
                for image in dataset.listChildren():
                    images.append(image)

    if data_type=="Dataset":
        datasets = conn.getObjects("Dataset",ids)
        for dataset in datasets:
            for image in dataset.listChildren():
                images.append(image)

    if data_type=="Screen":
        screens = conn.getObjects("Screen",ids)
        for screen in screens:
            for plate in screen.listChildren():
                    for well in plate.listChildren():
                        for ws in well.listChildren():
                            image = ws.getImage()
                            images.append(image)

    if data_type=="Plate":
        plates = conn.getObjects("Plate",ids)
        for plate in plates:
            for well in plate.listChildren():
                for ws in well.listChildren():
                    image = ws.getImage()
                    images.append(image)

    if data_type=="Image":
        images = conn.getObjects("Image",ids)

    return images

def get_unit(script_params):
    # creates the correct Unit from a string
    if script_params["Unit"]=="MICROMETER":
        unit = UnitsLength.MICROMETER

    if script_params["Unit"]=="NANOMETER":
        unit = UnitsLength.NANOMETER

    if script_params["Unit"]=="ANGSTROM":
        unit = UnitsLength.ANGSTROM

    if script_params["Unit"]=="MILLIMETER":
        unit = UnitsLength.MILLIMETER

    return unit


def set_pixel_value(conn, script_params):
    images = list(get_images(conn, script_params))
    numberOfImages = len(images)
    counter = 0
    overwrite = script_params["Overwrite_existing_values?"]
    pixelSizeX = None
    pixelSizeY = None
    pixelSizeZ = None
    for image in images:
        unit = get_unit(script_params)
        if PARAM_PIXEL_SIZE_X in script_params:
            sizeX = script_params[PARAM_PIXEL_SIZE_X]
            pixelSizeX = omero.model.LengthI(sizeX, unit)
        if PARAM_PIXEL_SIZE_Y in script_params:
            sizeY = script_params[PARAM_PIXEL_SIZE_Y]
            pixelSizeY = omero.model.LengthI(sizeY, unit)
        if PARAM_PIXEL_SIZE_Z in script_params:
            sizeZ = script_params[PARAM_PIXEL_SIZE_Z]
            pixelSizeZ = omero.model.LengthI(sizeZ, unit)
        
        # check if pixel size already exists
        pixels = image.getPrimaryPixels()._obj
        existingSizeX = pixels.getPhysicalSizeX()
        existingSizeY = pixels.getPhysicalSizeY()
        existingSizeZ = pixels.getPhysicalSizeZ()

        # Logic to set the new values
        # checks size of Z dimension as indicator if Z pixel size should be set
        internal_counter = 0
        if overwrite:

            if existingSizeX and pixelSizeX:
                print(f"Overwriting existing Pixel Size X for Image ID {image.getId()}: "
                      f"{existingSizeX.getValue()} {existingSizeX.getUnit()} ==> "
                      f"{pixelSizeX.getValue()} {pixelSizeX.getUnit()}")
                pixels.setPhysicalSizeX(pixelSizeX)
                internal_counter += 1
            elif pixelSizeX:
                pixels.setPhysicalSizeX(pixelSizeX)
                internal_counter += 1

            if existingSizeY and pixelSizeY:
                print(f"Overwriting existing Pixel Size Y for Image ID {image.getId()}: "
                      f"{existingSizeY.getValue()} {existingSizeY.getUnit()} ==> "
                      f"{pixelSizeY.getValue()} {pixelSizeY.getUnit()}")
                pixels.setPhysicalSizeY(pixelSizeY)
                internal_counter += 1
            elif pixelSizeY:
                pixels.setPhysicalSizeY(pixelSizeY)
                internal_counter += 1

            if pixels.getSizeZ().getValue()>1:
                if existingSizeZ and pixelSizeZ:
                    print(f"Overwriting existing Pixel Size Z for Image ID {image.getId()}: "
                          f"{existingSizeZ.getValue()} {existingSizeZ.getUnit()} ==> "
                          f"{pixelSizeZ.getValue()} {pixelSizeZ.getUnit()}")
                    pixels.setPhysicalSizeZ(pixelSizeZ)
                    internal_counter += 1
                elif pixelSizeZ:
                    pixels.setPhysicalSizeZ(pixelSizeZ)
                    internal_counter += 1
        else:
            if not existingSizeX and pixelSizeX:
                pixels.setPhysicalSizeX(pixelSizeX)
                internal_counter += 1
            elif existingSizeX and pixelSizeX:
                print(f"Image ID {image.getId()} already has Pixel Size X: "
                      f"{existingSizeX.getValue()} {existingSizeX.getUnit()}. Skipping setting new value.")
                
            if not existingSizeY and pixelSizeY:
                pixels.setPhysicalSizeY(pixelSizeY)
                internal_counter += 1
            elif existingSizeY and pixelSizeY:
                print(f"Image ID {image.getId()} already has Pixel Size Y: "
                      f"{existingSizeY.getValue()} {existingSizeY.getUnit()}. Skipping setting new value.")
                
            if pixels.getSizeZ().getValue()>1 and not existingSizeZ and pixelSizeZ:
                pixels.setPhysicalSizeZ(pixelSizeZ)
                internal_counter += 1
            elif pixels.getSizeZ().getValue()>1 and existingSizeZ and pixelSizeZ: 
                print(f"Image ID {image.getId()} already has Pixel Size Z: "
                      f"{existingSizeZ.getValue()} {existingSizeZ.getUnit()}. Skipping setting new value.")
        
        # if any new pixel value was set we count this image as updated
        # and save the changes to the database
        if internal_counter > 0: 
            conn.getUpdateService().saveObject(pixels)
            counter += 1
    
    return numberOfImages, counter


def run_script():

    data_types = [rstring('Dataset'), rstring('Plate'), rstring('Screen'), rstring('Project'), rstring('Image')]
    units = [rstring('MICROMETER'), rstring('NANOMETER'), rstring('ANGSTROM'), rstring('MILLIMETER')]
    client = scripts.client(
        'Set_Pixelsize',
        """
    This script sets the pixel size for one/multiple Images.\n
    Works for single Images or all Images in a Dataset, Plate, Screen or Project.\n
    Default behavior is to overwrite the existing pixel size values, but you can
    also choose to only set the pixel size for Images where this information is missing.
    If you provide a value for pixel size Z and the image does not have a Z dimension this will be ignored.
        """,
        scripts.String(
            "Data_Type", optional=False, grouping="1",
            description="Choose source of images",
            values=data_types, default="Dataset"),

        scripts.List(
            "IDs", optional=False, grouping="2",
            description="Screen/Plate/Project/Dataset/Image ID(s)."
            "\nYou can provide multiple IDs separated with a ','.").ofType(rlong(0)),

        scripts.Float(
            PARAM_PIXEL_SIZE_X, optional=True, grouping="3",
            description="Size of the pixels, e.g. 0.0025"),

        scripts.Float(
            PARAM_PIXEL_SIZE_Y, optional=True, grouping="4",
            description="If left empty the value for Pixel Size [X] is used. "
            "Size of the pixels, e.g. 0.0025"),

        scripts.Float(
            PARAM_PIXEL_SIZE_Z, optional=True, grouping="5",
            description="If left empty and the image has Z Dimension "
            "the value for Pixel Size [X] is used. Size of the pixels, e.g. 0.0025"),

        scripts.String(
            "Unit", optional=False, grouping="6",
            description="Unit for the pixel size",
            values=units, default="MICROMETER"),

        scripts.Bool(
            "Overwrite_existing_values?", grouping="7", default=True,
            description="If checked will overwrite existing pixel size values. "
            "If unchecked only images without pixel size information will be updated."),

        authors=["Jens Wendt"],
        institutions=["Muenster Imaging Network"],
        contact="jens.wendt@uni-muenster.de"
    )

    try:
        # process the list of args above.
        script_params = {}
        for key in client.getInputKeys():
            if client.getInput(key):
                script_params[key] = client.getInput(key, unwrap=True)

        # if the optional pixel size inputs are empty we set them to the value of Pixel_Size_[X]
        if PARAM_PIXEL_SIZE_Y not in script_params and PARAM_PIXEL_SIZE_X in script_params:
            script_params[PARAM_PIXEL_SIZE_Y] = script_params[PARAM_PIXEL_SIZE_X]
        if PARAM_PIXEL_SIZE_Z not in script_params and PARAM_PIXEL_SIZE_X in script_params:
            script_params[PARAM_PIXEL_SIZE_Z] = script_params[PARAM_PIXEL_SIZE_X]

        # wrap client to use the Blitz Gateway
        conn = BlitzGateway(client_obj=client)
        print("script params")
        for k, v in script_params.items():
            print(k, v)
        print("################################")
        # if none of the keys PARAM_PIXEL_SIZE_Z, PARAM_PIXEL_SIZE_Y or PARAM_PIXEL_SIZE_X are not
        # provided we can not set the pixel size and therefore stop the script with an error message
        if not any(k in script_params for k in [PARAM_PIXEL_SIZE_Z, PARAM_PIXEL_SIZE_Y, PARAM_PIXEL_SIZE_X]):
            client.setOutput("Message", rstring("No pixel size value provided. "
                                                "Please provide at least one pixel size value."))
        else:
            numberOfImages, counter = set_pixel_value(conn, script_params)
            if counter == 0:
                message = f"No new pixel size values were set. All {numberOfImages} Image(s) already had pixel size information."
            else:
                message = f"Set new pixel size(s) for {counter} of {numberOfImages} Image(s)."
            client.setOutput("Message", rstring(message))
        print("###############DONE#############")
        print("################################")
    finally:
        client.closeSession()

if __name__ == "__main__":
    run_script()