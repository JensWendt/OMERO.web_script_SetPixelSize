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
    for image in images:
        unit = get_unit(script_params)
        sizeX = script_params["Pixel_Size_[X]"]
        sizeY = script_params["Pixel_Size_[Y]"]
        sizeZ = script_params["Pixel_Size_[Z]"]
        pixelSizeX = omero.model.LengthI(sizeX, unit)
        pixelSizeY = omero.model.LengthI(sizeY, unit)
        pixelSizeZ = omero.model.LengthI(sizeZ, unit)
        
        # check if pixel size already exists
        pixels = image.getPrimaryPixels()._obj
        existingSizeX = pixels.getPhysicalSizeX()
        existingSizeY = pixels.getPhysicalSizeY()
        existingSizeZ = pixels.getPhysicalSizeZ()

        # Logic to set the new values
        # checks size of Z dimension as indicator if Z pixel size should be set
        if overwrite:
            if existingSizeX:
                print(f"Overwriting existing Pixel Size X for Image ID {image.getId()}: "
                      f"{existingSizeX.getValue()} {existingSizeX.getUnit()}")
                pixels.setPhysicalSizeX(pixelSizeX)
            else:
                pixels.setPhysicalSizeX(pixelSizeX)
            if existingSizeY:
                print(f"Overwriting existing Pixel Size Y for Image ID {image.getId()}: "
                      f"{existingSizeY.getValue()} {existingSizeY.getUnit()}")
                pixels.setPhysicalSizeY(pixelSizeY)
            else:
                pixels.setPhysicalSizeY(pixelSizeY)
            if pixels.getSizeZ()>1:
                if existingSizeZ:
                    print(f"Overwriting existing Pixel Size Z for Image ID {image.getId()}: "
                          f"{existingSizeZ.getValue()} {existingSizeZ.getUnit()}")
                    pixels.setPhysicalSizeZ(pixelSizeZ)
                else:
                    pixels.setPhysicalSizeZ(pixelSizeZ)
        else:
            if not existingSizeX:
                pixels.setPhysicalSizeX(pixelSizeX)
            if not existingSizeY:
                pixels.setPhysicalSizeY(pixelSizeY)
            if pixels.getSizeZ()>1 and not existingSizeZ:
                pixels.setPhysicalSizeZ(pixelSizeZ)

        # we are gonna save regardless if we set new values or not to make it easier
        conn.getUpdateService().saveObject(pixels)
        counter += 1

    
    return numberOfImages, counter


def run_script():

    data_types = [rstring('Dataset'), rstring('Plate'), rstring('Screen'), rstring('Project'), rstring('Image')]
    units = [rstring('MICROMETER'), rstring('NANOMETER'), rstring('ANGSTROM'), rstring('MILLIMETER')]
    client = scripts.client(
        'Set_Pixelsize',
        """
    This script sets the pixel size for one/multiple Images.
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
            "Pixel_Size_[X]", optional=False, grouping="3",
            description="Size of the pixels, e.g. 0.0025"),

        scripts.Float(
            "Pixel_Size_[Y]_(Only_set_if_different_from_X)", optional=True, grouping="4",
            description="If left empty the value for Pixel Size [X] is used. "
            "Size of the pixels, e.g. 0.0025"),

        scripts.Float(
            "Pixel_Size_[Z]_(Only_set_if_Z_Dimension_exists)", optional=True, grouping="5",
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
            # for the two optional pixel size inputs we need to check if they are empty 
            # and if yes use the value from Pixel_Size_[X] and shorten the name
            if key == "Pixel_Size_[Y]_(Only_set_if_different_from_X)":
                if client.getInput(key):
                    script_params["Pixel_Size_[Y]"] = client.getInput(key, unwrap=True)
                else:
                    script_params["Pixel_Size_[Y]"] = client.getInput("Pixel_Size_[X]", unwrap=True)
            elif key == "Pixel_Size_[Z]_(Only_set_if_Z_Dimension_exists)":
                if client.getInput(key):
                    script_params["Pixel_Size_[Z]"] = client.getInput(key, unwrap=True)
                else:
                    script_params["Pixel_Size_[Z]"] = client.getInput("Pixel_Size_[X]", unwrap=True)
            else: 
                if client.getInput(key):
                    script_params[key] = client.getInput(key, unwrap=True)

        # wrap client to use the Blitz Gateway
        conn = BlitzGateway(client_obj=client)
        print("script params")
        for k, v in script_params.items():
            print(k, v)
        numberOfImages, counter = set_pixel_value(conn, script_params)
        message = f"Set the pixel size to {script_params['Pixel_Size_[X]']} {script_params['Unit']} for {counter} of {numberOfImages} Images."
        client.setOutput("Message", rstring(message))

    finally:
        client.closeSession()

if __name__ == "__main__":
    run_script()