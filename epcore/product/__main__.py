from .product import EPLab


if __name__ == "__main__":

    eplab = EPLab()
    for name, parameter in eplab.get_parameters().items():
        print("ParameterName: " + str(name) + ", Parameter: " + str(parameter))
