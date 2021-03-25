from ruamel.yaml import YAML

yaml = YAML()


def load_yaml(filename):
    with open(filename + '.yaml', 'rb') as f:
        data = yaml.load(f)
    return data


def save_yaml(filename, data):
    with open(filename + '.yaml', 'wb') as f:
        yaml.dump(data, f)