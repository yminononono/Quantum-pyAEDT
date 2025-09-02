
import math, pprint, yaml

def evaluate_config(config):
    """
    dict を再帰的に探索し、'eval:' 付きの値を評価して置き換える
    """
    if isinstance(config, dict):
        for k, v in config.items():
            if isinstance(v, str) and v.strip().startswith("eval:"):
                expr = v.split("eval:", 1)[1].strip()
                # 同じ階層の dict を評価環境として渡す
                config[k] = eval(expr, {}, config)
            else:
                config[k] = evaluate_config(v)
    elif isinstance(config, list):
        return [evaluate_config(x) for x in config]
    return config

def load_config(filename):

    with open(filename, 'r') as _file:
        config = yaml.safe_load(_file)
        config = evaluate_config(config)
        
    return config

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

def create_setup(hfss, config):

    options = config["solution"]["options"]
    if config["solution"]["type"]=="Modal":
        setup = hfss.create_setup(config["solution"]["name"])
        setup.create_frequency_sweep(
            unit               = "GHz",
            name               = "Sweep1",
            start_frequency    = options["start_frequency"],
            stop_frequency     = options["stop_frequency"],
            num_of_freq_points = options["num_of_freq_points"],
            sweep_type         = "Interpolating",
        )
        if options["adaptive_solution_type"] == "broadband":
            setup.enable_adaptive_setup_broadband(
                low_frequency = options["start_frequency"],
                high_frquency = options["stop_frequency"],
                max_passes    = options["max_passes"],
                max_delta_s   = options["max_delta_s"]
            ) 
        elif options["adaptive_solution_type"] == "single":
            setup.enable_adaptive_setup_single(
                freq        = options["adaptive_setup_frequency"],
                max_passes  = options["max_passes"],
                max_delta_s = options["max_delta_s"]
            )
            # setup.props["MaximumPasses"] = 20
            # setup.props["MaxDeltaS"] = 0.01
        pprint.pprint(setup.props)

    elif config["solution"]["type"]=="Eigenmode":
        setup = hfss.create_setup(config["solution"]["name"]) 
        setup.props["MinimumFrequency"] = options["min_frequency"]
        setup.props["NumModes"]         = options["n_mode"]
        setup.props["MaximumPasses"]    = options["max_passes"]
        pprint.pprint(setup.props)

    else:
        raise ValueError("Set solution type to 'Eigenmode' or 'Modal'")

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

def create_sweep(hfss, config):

    sweep = None
    for var in config["sweep"]["list"][config["solution"]["type"]]:
        sweep = add_sweep(hfss, sweep, config["sweep"]["config"], var)

    return sweep