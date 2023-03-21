class PathAlreadyExistsError(Exception):
    def __init__(self, path):
        self.path = path
        super().__init__(f"The path '{path.path_str}' already exists.")

class PathDoesNotExistError(Exception):
    def __init__(self, path):
        self.path = path
        super().__init__(f"The path '{path.path_str}' does not exist.")

class PathNotFile(Exception):
    def __init__(self, path):
        self.path = path
        super().__init__(f"The path '{path.path_str}' is not a file.")

class PathNotDirectory(Exception):
    def __init__(self, path):
        self.path = path
        super().__init__(f"The path '{path.path_str}' is not a directory.")

class DirectoryNotEmpty(Exception):
    def __init__(self, path):
        self.path = path
        super().__init__(f"The path '{path.path_str}' is not empty.")

class ActionNotAllowed(Exception):
    def __init__(self, path):
        self.path = path
        super().__init__(f"This action on '{path.path_str}' is not allowed.")

class InvalidMove(Exception):
    def __init__(self, from_path, to_path):
        self.from_path = from_path
        self.to_path = to_path
        super().__init__(f"Cannot move '{from_path.path_str}' to '{to_path.path_str}'.")