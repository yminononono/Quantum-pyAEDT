
import math

def rename_var(variation, var):

    label = ""
    if var == "$chip_theta":
        label = str(int(180 * float(variation[var].value/math.pi))) + " degree"
    elif var == "$chip_gap":
        label = "gap : " + "{:.2f}".format(variation[var]*1e+3) + " mm"
    elif var == "$chip_height":
        label = "height : " + "{:.2f}".format(variation[var]*1e+3) + " mm"
    elif var == "$chip_pos_z_ratio":
        label = "Z pos : " + "{:.2f}".format(variation[var])
    else:
        label = f"{var.replace('$','')} : {variation[var].value}"

    return label

def add_sweep(hfss, sweep, sweep_list, variable):

    for config in sweep_list[variable]:
        if not sweep:
            sweep_config = dict(
                variable       = variable,
                start_point    = str(config["start_point"]) + config["units"],
                end_point      = str(config["end_point"]) + config["units"],
                variation_type = config["variation_type"],
                name           = "Sweep",
            )
            if config["variation_type"] == "LinearStep":
                sweep_config["step"] = str(config["step"]) + config["units"]
            elif config["variation_type"] == "LinearCount":
                sweep_config["step"] = config["step"]

            sweep = hfss.parametrics.add(**sweep_config)
        else:
            config["sweep_variable"] = variable
            sweep.add_variation(**config)

    return sweep