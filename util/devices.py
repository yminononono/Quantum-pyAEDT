import pprint

def set_parameters(hfss, config):
    
    for var in config["parameter"]:
        hfss[var] = config["parameter"][var]

def device_CoaxCavity( hfss, config ):

    set_parameters(hfss, config)

    ############################################
    ### Make objects ###########################
    ############################################

    # Make cavity box 
    box_config = dict(
        origin   = ["-$box_length/2", "-$box_length/2", "$outer_height - $box_height"],
        sizes    = ["$box_length", "$box_length", "$box_height"],
        name     = "cavity",
        material = "copper"
    )
    if config["solution"]["options"]["use_antenna"]:
        box_config.update( sizes = ["$box_length", "$box_length", "$box_height + $antenna_outer_height"] )

    box_object = hfss.modeler.create_box( **box_config )

    ## Make Vacuum object
    #_, vacuum_name = hfss.modeler.duplicate_around_axis(box_object, "Z", angle = 0)
    vacuum_object = box_object.clone()
    vacuum_object.name = "boundary"
    vacuum_object = hfss.modeler.get_object_from_name("boundary")
    hfss.assign_material("boundary", "vacuum")
    if config["solution"]["type"] == "Eigenmode":
        # hfss.modeler.move_face([vacuum_object.top_face_z], offset=20) # offset in mm
        hfss.assign_finite_conductivity([vacuum_object.top_face_z],is_infinite_ground=True)

    ## Make cylinder
    cylinder_config = dict(
        orientation = "Z",
        origin      = [0, 0, 0],
        radius      = "$outer_radius",
        height      = "$outer_height",
        name        = "outer",
        material    = "vacuum"
    )
    cylinder_object = hfss.modeler.create_cylinder( **cylinder_config )

    box_object.subtract(cylinder_object, keep_originals=False)

    coax_config = dict(
        orientation = "Z",
        origin      = [0, 0, 0],
        radius      = "$coax_radius",
        height      = "$coax_height",
        name        = "coax",
        material    = "copper"
    )

    coax_object = hfss.modeler.create_cylinder( **coax_config )

    box_object.unite(coax_object)

    if config["solution"]["options"]["use_antenna"]:
        antenna_config = dict(
            orientation = "Z",
            origin      = [0, 0, "$outer_height"],
            radius      = "$antenna_outer_radius",
            height      = "$antenna_outer_height",
            name        = "antenna",
            material    = "vacuum"
        )

        antenna_object = hfss.modeler.create_cylinder( **antenna_config )
        box_object.subtract(antenna_object, keep_originals=False)

        core_config = dict(
            orientation = "Z",
            origin      = [0, 0, "$outer_height + $antenna_outer_height - $antenna_height"],
            radius      = "$antenna_radius",
            height      = "$antenna_height",
            name        = "core",
            material    = "copper"
        )

        core_object = hfss.modeler.create_cylinder( **core_config )

    wafer_coord = hfss.modeler.create_coordinate_system(origin = [0, "$chip_pos_y","$chip_pos_z"], name = "wafer_coord")
    wafer_coord.set_as_working_cs()
    wafer_config = dict(
        origin   = ["-$wafer_width/2", "-$wafer_height/2", 0],
        sizes    = ["$wafer_width", "$wafer_height", "$wafer_thickness"],
        name     = "wafer",
        material = "silicon"
    )
    wafer_object = hfss.modeler.create_box( **wafer_config )

    chip_coord = hfss.modeler.create_coordinate_system(origin = [0, 0,"$wafer_thickness"], reference_cs="wafer_coord", name = "chip_coord")
    chip_coord.set_as_working_cs()
    cap1 = hfss.modeler.create_rectangle(origin = ["-0.5*$chip_width", "0.5*$chip_gap", 0], sizes = ["$chip_width", "$chip_height"], name = "cap1", orientation="XY")
    cap2 = hfss.modeler.create_rectangle(origin = ["-0.5*$chip_width", "-0.5*$chip_gap - $chip_height", 0], sizes =  ["$chip_width", "$chip_height"], name = "cap2", orientation="XY")

    ############################################
    ### Assign perfect E #######################
    ############################################
    
    ## Only for newer pyaedt versions ?
    hfss.assign_perfect_e("box")
    hfss.assign_perfect_e("cap1")
    hfss.assign_perfect_e("cap2")
    if config["solution"]["options"]["use_antenna"]:
        hfss.assign_perfect_e("core")

    ############################################
    ### Create ports ###########################
    ############################################

    # faces = vacuum_object.faces
    # top_face = max(faces, key=lambda f: f.center[2])

    hfss.modeler.set_working_coordinate_system("Global")
    if config["solution"]["type"]=="Modal":
        if config["solution"]["options"]["use_antenna"]:
            port_in = hfss.modeler.create_circle(origin = [0, 0, "$outer_height + $antenna_outer_height"], radius = "$antenna_outer_radius", name = "port_in", orientation="XY")
            hfss.lumped_port(assignment="port_in", integration_line = hfss.AxisDir.YNeg, name="Port_in")
        else:
            port_in = hfss.modeler.create_circle(origin = [0, 0, "$outer_height"], radius = "$outer_radius", name = "port_in", orientation="XY")
            hfss.wave_port(assignment="port_in", name = "Port_in", modes = config["solution"]["options"]["n_waveport_mode"])

    hfss.modeler.set_working_coordinate_system("chip_coord")
    port_out = hfss.modeler.create_rectangle(origin = ["-10um","-0.5*$chip_gap" ], sizes=["20um","$chip_gap"], name = "port_out", orientation="XY")
    if config["solution"]["type"]=="Eigenmode":
        sheet = hfss.assign_lumped_rlc_to_sheet(assignment="port_out", 
                                        start_direction=hfss.AxisDir.YNeg, 
                                        inductance=9e-9, name="Port_out")
        sheet.update_property(
            prop_name = "Inductance",
            prop_value = "$chip_inductance"
        )
    else:
        # hfss.assign_lumped_rlc_to_sheet(assignment="port_out", start_direction=hfss.AxisDir.YNeg, inductance=chip_inductance, name="Port_out")
        hfss.lumped_port(assignment="port_out", integration_line = hfss.AxisDir.YNeg, name="Port_out")


    ############################################
    ### Rotate chip ############################
    ############################################

    # rotate_coord = hfss.modeler.create_coordinate_system(origin = [0, "-0.5*$chip_gap - $chip_height", 0], reference_cs="chip_coord", name = "rotate_coord")
    # rotate_coord.set_as_working_cs()
    hfss.modeler.set_working_coordinate_system("chip_coord")
    hfss.modeler.rotate(assignment=["wafer","cap1","cap2","port_out"], axis="X", angle="$chip_theta")

    if config["solution"]["options"]["use_second_chip"]:
        hfss.modeler.set_working_coordinate_system("Global")
        duplicate_object = ["wafer","cap1","cap2","port_out"]
        _, object_name = hfss.modeler.duplicate_around_axis(duplicate_object, "Z", angle = 90)
        for i, obj_name in enumerate(duplicate_object):
            obj = hfss.modeler.get_object_from_name(object_name[i])
            obj.name = f"chip2_{obj_name}"

    ############################################
    ### Assign mesh ############################
    ############################################
    hfss.mesh.assign_length_mesh(["cap1", "cap2"], inside_selection=False, maximum_length="20um", name="mesh_cap")
    hfss.mesh.assign_length_mesh(["port_out"], inside_selection=False, maximum_length="5um", name="mesh_JJ") # maximum 7um for JJ in qiskit-metal
    if config["solution"]["options"]["use_second_chip"]:
        hfss.mesh.assign_length_mesh(["chip2_cap1","chip2_cap2"], inside_selection=False, maximum_length="20um", name="mesh_cap2")
        hfss.mesh.assign_length_mesh(["chip2_port_out"], inside_selection=False, maximum_length="5um", name="mesh_JJ")

def device_BoxCavity( hfss, config ):

    set_parameters(hfss, config)

    ############################################
    ### Make objects ###########################
    ############################################

    # Make cavity
    box_config = dict(
        origin   = ["-$cavity_width/2", "-$cavity_length/2", 0],
        sizes    = ["$cavity_width", "$cavity_length", "$cavity_height"],
        name     = "cavity",
        material = "vacuum"
    )
 
    box_object = hfss.modeler.create_box( **box_config )


    ## Make port
    port_coord = hfss.modeler.create_coordinate_system(
        origin = [0, "$cavity_length/2", "$cavity_height/2"], 
        x_pointing = [-1, 0, 0],
        y_pointing = [0, 0, 1],
        name = "port_coord"
    )
    port_coord.set_as_working_cs()

    cylinder_config = dict(
        orientation = "Z",
        origin      = [0, "$port_distance/2", 0],
        radius      = "$port_outer_radius",
        height      = "$port_height",
        name        = "port_in",
        material    = "vacuum"
    )
    port_in_object = hfss.modeler.create_cylinder( **cylinder_config )
    # faces = port_in_object.faces
    # port_in_face = max(faces, key=lambda f: f.center[2])
    port_in_face = port_in_object.top_face_y

    cylinder_config = dict(
        orientation = "Z",
        origin      = [0, "-$port_distance/2", 0],
        radius      = "$port_outer_radius",
        height      = "$port_height",
        name        = "port_out",
        material    = "vacuum"
    )
    port_out_object = hfss.modeler.create_cylinder( **cylinder_config )
    faces = port_out_object.faces
    # port_out_face = max(faces, key=lambda f: f.center[2])
    port_out_face = port_out_object.top_face_y

    box_object.unite(["port_in", "port_out"])

    port_in_coord = hfss.modeler.create_coordinate_system(
        origin = [0, "$port_distance/2", "$port_height"], 
        x_pointing = [-1, 0, 0],
        y_pointing = [0, 1, 0],
        reference_cs="port_coord",
        name = "port_in_coord"
    )
    port_in_coord.set_as_working_cs()

    antenna_config = dict(
        orientation = "Z",
        origin      = [0, 0, 0],
        radius      = "$port_inner_radius",
        height      = "$port_in_depth",
        name        = "antenna_in",
        material    = "copper"
    )

    antenna_in_object = hfss.modeler.create_cylinder( **antenna_config )

    port_out_coord = hfss.modeler.create_coordinate_system(
        origin = [0, "-$port_distance/2", "$port_height"], 
        x_pointing = [-1, 0, 0],
        y_pointing = [0, 1, 0],
        reference_cs="port_coord",
        name = "port_out_coord"
    )
    port_out_coord.set_as_working_cs()

    antenna_config = dict(
        orientation = "Z",
        origin      = [0, 0, 0],
        radius      = "$port_inner_radius",
        height      = "$port_out_depth",
        name        = "antenna_out",
        material    = "copper"
    )

    antenna_out_object = hfss.modeler.create_cylinder( **antenna_config )

    # wafer_coord = hfss.modeler.create_coordinate_system(origin = [0, "$chip_pos_y","$chip_pos_z"], name = "wafer_coord")
    # wafer_coord.set_as_working_cs()
    # wafer_config = dict(
    #     origin   = ["-$wafer_width/2", "-$wafer_height/2", 0],
    #     sizes    = ["$wafer_width", "$wafer_height", "$wafer_thickness"],
    #     name     = "wafer",
    #     material = "silicon"
    # )
    # wafer_object = hfss.modeler.create_box( **wafer_config )

    # chip_coord = hfss.modeler.create_coordinate_system(origin = [0, 0,"$wafer_thickness"], reference_cs="wafer_coord", name = "chip_coord")
    # chip_coord.set_as_working_cs()
    # cap1 = hfss.modeler.create_rectangle(origin = ["-0.5*$chip_width", "0.5*$chip_gap", 0], sizes = ["$chip_width", "$chip_height"], name = "cap1", orientation="XY")
    # cap2 = hfss.modeler.create_rectangle(origin = ["-0.5*$chip_width", "-0.5*$chip_gap - $chip_height", 0], sizes =  ["$chip_width", "$chip_height"], name = "cap2", orientation="XY")

    ############################################
    ### Assign perfect E #######################
    ############################################
    
    ## Only for newer pyaedt versions ?
    hfss.assign_perfect_e("cavity")
    # hfss.assign_perfect_e("antenna_in")
    # hfss.assign_perfect_e("antenna_out")

    ############################################
    ### Create ports ###########################
    ############################################

    # faces = vacuum_object.faces
    # top_face = max(faces, key=lambda f: f.center[2])

    hfss.modeler.set_working_coordinate_system("Global")
    if config["solution"]["type"]=="Modal":
        # port_in_coord.set_as_working_cs()
        # port_in = hfss.modeler.create_circle(origin = [0, 0, 0], radius = "$port_outer_radius", name = "input", orientation="XY")
        hfss.wave_port(assignment=port_in_face, name = "Port_in", modes = config["solution"]["options"]["n_waveport_mode"])
        # port_out_coord.set_as_working_cs()
        # port_out = hfss.modeler.create_circle(origin = [0, 0, 0], radius = "$port_outer_radius", name = "output", orientation="XY")
        hfss.wave_port(assignment=port_out_face, name = "Port_out", modes = config["solution"]["options"]["n_waveport_mode"])
    elif config["solution"]["type"]=="Eigenmode":
        pass
        # sheet = hfss.assign_lumped_rlc_to_sheet(assignment="port_out", 
        #                                 start_direction=hfss.AxisDir.YNeg, 
        #                                 inductance=9e-9, name="Port_out")
        # sheet.update_property(
        #     prop_name = "Inductance",
        #     prop_value = "$chip_inductance"
        # )
