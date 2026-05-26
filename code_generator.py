class CodeGenerator:
    def __init__(self, commands):
        self.commands = commands

    def generate_code(self):
        imports = "import pandas as pd\n"
        code = "\n".join(self.commands)
        return f"{imports}\n{code}"
