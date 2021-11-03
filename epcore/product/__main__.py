from .product import EyePointProduct


if __name__ == "__main__":

    eyepoint = EyePointProduct()
    for name, parameter in eyepoint.get_parameters().items():
        print("ParameterName: " + str(name) + ", Parameter: " + str(parameter))
