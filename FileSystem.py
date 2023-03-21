import time
from typing import List, Union

from FileSystemExceptions import (
    ActionNotAllowed,
    DirectoryNotEmpty,
    InvalidMove,
    PathAlreadyExistsError,
    PathDoesNotExistError,
    PathNotDirectory,
    PathNotFile,
)

##############################
# File System Objects
##############################
class FSObject:
    def __init__(self, path: 'Path') -> 'FSObject':
        self.path = path
        self.created_ts = time.time()
        self.modified_ts = time.time()

    def __str__(self) -> str:
        return self.path
    

class File(FSObject):
    def __init__(self, path: 'Path', content: str):
        super().__init__(path)
        self.content = content

    def size(self) -> int:
        return len(self.content)
    
    def read(self) -> str:
        return self.content
    
    def write(self, new_content: str):
        self.content = new_content


class Directory(FSObject):
    def __init__(self, path: 'Path', items: List['FSObject']=None):
        super().__init__(path)
        if items is None:
            self.items: List['FSObject'] = []
        else:
            self.items = items

    def size(self) -> int:
        return sum([item.size for item in self.items])
    
    def add_item(self, item: 'FSObject'):
        self.items.append(item)
    
    def remove_item(self, item: 'FSObject'):
        self.items.remove(item)


##############################
# Utilities
##############################
class Path:
    def __init__(self, path: str, fs: 'FileSystem'):
        if path == '':
            raise Exception(f'Empty path is invalid')
        self.parts: List[str] = self._split_path(path)
        if len(path) > 1000:
            raise Exception('Path is too deep')
        self.path_str = path
        self.fs = fs

    def _split_path(self, path: str) -> List[str]:
        """
        Split a path string into it's components and mark if a path is absolute
        """
        parts = path.split('/')
        if parts[0] == '':
            parts[0] = '/'
        return parts

    def _parts_to_str(self, parts: List[str]) -> str:
        """ Convert path parts into a string """
        if self.is_absolute():
            parts = parts[1:]
        return "/" + "/".join(parts)

    def is_absolute(self) -> bool:
        return self.parts[0] == '/'

    def resolve(self, new_path: 'Path') -> 'Path':
        """
        Resolves new_path against self.
        Args:
        new_path -- relative or absolute path to resolve.
            '..' and '.' syntax is supported
        Return:
        Path object representing resolved, absolute path
        """
        path_levels = new_path.parts
        if not new_path.is_absolute():
            path_levels = self.parts + new_path.parts

        final_path = []
        for item in path_levels:
            if item == ".." and len(final_path) > 1:
                final_path.pop()
            elif item != '' and item != "." and item != "..":
                final_path.append(item)

        return Path(self._parts_to_str(final_path), self.fs)

    def parent(self) -> 'Path':
        """ Returns immediate parent directory for self """
        parent_path = self._parts_to_str(self.parts[:-1])
        return Path(parent_path, self.fs)
    
    def name(self) -> str:
        """ ie. name for '/foo/bar/baz.txt' is 'baz.txt' """
        return self.parts[-1]

    def extend(self, sub_path: str) -> 'Path':
        """ Extends self with the given sub_path """
        if sub_path[0] == '/':
            raise Exception('Expect sub_path to be a relative path')
        return Path(self.path_str + "/" + sub_path, self.fs)
    
    def exists(self) -> bool:
        if self in self.fs.fs:
            return True
        return False
    
    def must_exist(self):
        """ Raises an error if the item does not exist in the filesystem """
        if not self.exists():
            raise PathDoesNotExistError(self)
        
    def must_not_exist(self):
        """ Raises an error if the item exists in the filesystem """
        if self.exists():
            raise PathAlreadyExistsError(self)
    
    def must_be_file(self):
        """ Raises an error if the item is not of type File """
        self.must_exist()
        if not isinstance(self.fs[self], File):
            raise PathNotFile(self)

    def must_be_dir(self):
        """ Raises an error if the item is not of type Directory """
        self.must_exist()
        if not isinstance(self.fs[self], Directory):
            raise PathNotDirectory(self)
 
    def __hash__(self):
        return hash(self.path_str)

    def __eq__(self, other):
        return self.path_str == other.path_str


##############################
# Commands
##############################
class FileSystem():
    def __init__(self) -> 'FileSystem':
        self.curr_dir = Path('/', self)
        self.fs = {self.curr_dir: Directory(self.curr_dir)}

    def pathify(self, path: Union[str, 'Path']) -> 'Path':
        """
        Resolves the given path against the current working directory.
        Returns: Path object representing resolved, absolute path
        """
        if isinstance(path, str):
            path = Path(path, self)
        return self.curr_dir.resolve(path)
    
    def _insert(self, item: 'FSObject'):
        self.fs[item.path] = item
        self.fs[item.path.parent()].add_item(item)

    def _remove(self, item: 'FSObject'):
        del self.fs[item.path]
        self[item.path.parent()].remove_item(item)

    def _add_item(self, item: 'FSObject', recursive: bool=False):
        """
        Adds the given item to the file system. If the item already exists, an
        exception is raised

        Keyword args:
        recursive -- if True, create any intermediate missing directories
        """
        item.path.must_not_exist()
        parent = item.path.parent()
        if recursive and not parent.exists():
            self._add_item(Directory(parent), recursive)
        parent.must_be_dir()
        self._insert(item)

    def _mv(self, from_path:' Path', to_path: 'Path'):
        """
        Move the object at from_path to the to_path location. If from_path
        refers to a directory, all descendants are moved to the to_path
        as well. If any descendants run into a name conflict, they will
        overwrite what was previously at that location
        """

        # Change path of from_path object to be to_path
        old = from_path.path_str
        item = self[from_path]
        self._remove(item)
        item.path = to_path
        self._insert(item)

        def move_children(item: 'FSObject'):
            cur = item.path
            moved = item.path.path_str.replace(old, to_path.path_str)
            item.path = self.pathify(moved)
            # if something is already in this location, remove it
            if self.fs.get(item.path):
                self._remove(self.fs[item.path])
            # remove me from the previous location
            del self.fs[cur]
            # set new location to me
            self.fs[item.path] = item
            return True

        # Recursively move any children to to_path as well
        if isinstance(item, Directory):
            self.walk(to_path, move_children, recursive=True)

    def walk(self, path: 'Path', action, recursive: bool=False):
        """
        Invoke the provided 'action' on the children of path. The provided
        'action' function should return True/False to determine if the
        action should continue to be applied to other children.

        Keyword args:
        recursive -- if True, apply 'action' to all descendants of path
        """
        path.must_be_dir()
        for item in self.fs[path].items[:]:
            should_continue = action(item)
            if not should_continue:
                break
            if recursive and isinstance(item, Directory):
                self.walk(item.path, action, recursive)

    def mkdir(self, path_str: str, recursive: bool=False):
        """ 
        Add directory

        Keyword args:
        recursive -- if True, create any missing subdirectories
        """
        path = self.pathify(path_str)
        self._add_item(Directory(path), recursive)

    def mkfile(self, path_str: str, recursive: bool=False):
        """
        Add file

        Keyword args:
        recursive -- if True, create any missing subdirectories
        """
        path = self.pathify(path_str)
        self._add_item(File(path, None), recursive)

    def read(self, path_str: str):
        """ Read contents of a file """
        path = self.pathify(path_str)
        path.must_be_file()
        return self[path].read()

    def write(self, path_str: str, content: str, force=False):
        """
        Write contents to a file

        Keyword args:
        force -- if True, creates the file if it doesn't already exist
        """
        path = self.pathify(path_str)
        if force and not path.exists():
            self.mkfile(path_str, recursive=True)
        path.must_be_file()
        self[path].write(content)

    def rm(self, path_str: Union[str, 'Path'], recursive: bool=False):
        """
        Removes the item at the given path_str if it exists. Removing root is
        not allowed. By default, deleting a non-empty directory will raise an error.

        Keyword args:
        recursive -- if True, allows for deleting of non-empty directories. All items
        in the directory will be deleted first.
        """
        path = self.pathify(path_str)
        path.must_exist()
        item = self[path]

        # Don't allow removal of root directory
        if path.path_str == '/':
            raise ActionNotAllowed(path)

        if isinstance(item, Directory):
            if item.items and recursive:
                for child in item.items:
                    self.rm(child.path, recursive)
            elif item.items:
                raise DirectoryNotEmpty(path)

        self._remove(item)

    def cwd(self):
        """ Returns the current working directory """
        return self.curr_dir.path_str
    
    def cd(self, path_str: str):
        """ Change the current working directory to the provided path """
        path = self.pathify(path_str)
        path.must_be_dir()
        self.curr_dir = path

    def ls(self, path_str: str=None):
        """ List out the contents of the directory at the provided path_str """
        path = self.pathify(path_str or self.curr_dir)
        path.must_be_dir()

        return [item.path.name() for item in self[path].items]

    def find(self, match_name: str, path_str: str=None, recursive: bool=False):
        """
        Return any files/directories in the directory at path_str that are an exact
        match of the provided match_name

        Keyword args:
        recursive -- if True, returns any descendants of the provieded directory that are
        an exact match of the provided match_name
        """
        found = []

        def finder(item: 'FSObject'):
            if item.path.name() == match_name:
                found.append(item.path.path_str)
            return True

        path = self.curr_dir
        if path_str:
            path = self.pathify(path_str)
            path.must_be_dir()
        self.walk(path, finder, recursive)
        return found

    def mv(self, from_path_str: str, to_path_str: str, force: bool=False):
        """
        Move item at from_path_str to to_path_str. If from_path_str refers to a directory,
        all descendants of the directory will also be moved. If to_path_str is a directory
        the object at from_path_str will be moved into to_path_str.

        Keyword args:
        force -- if True and there is a name conflict at the to_path location,
        overwrite whatever is at to_path with the from_path object
        """
        from_path = self.pathify(from_path_str)
        to_path = self.pathify(to_path_str)
        from_path.must_exist()
        to_obj = self.fs.get(to_path)

        # Cannot move the root dir
        if from_path_str == '/':
            raise ActionNotAllowed(from_path)

        # Nothing exists at the to_path location so okay to move from_obj there
        if not to_obj:
            self._mv(from_path, to_path)
            return

        # If to_obj is a directory and there is no name conflict between from_obj
        # and to's children, okay to move from_obj into the to directory
        if isinstance(to_obj, Directory):
            to_path_children = [item.path.name() for item in to_obj.items]
            if not from_path.name() in to_path_children or force:
                self._mv(from_path, to_path.extend(from_path.name()))
                return

        # At this point, if force flag is not set, raise an error because the
        # to_obj already exists and there is a name conflict
        if not force:
            raise InvalidMove(from_path, to_path)

        # Force flag is set. Recursively remove everything in to_path and recursively
        # rename everythign in from_path
        self.rm(to_path, recursive=True)
        self._mv(from_path, to_path)

    def merge_dir(self, from_path_str: Union[str,'Path'], to_path_str: Union[str,'Path']):
        """
        Merge directory at from_path_str into directory at to_path_str. All descendants are also merged.
        If any descendant directory of from_path_str has a name conflict with a descendant of to_path_str,
        the descentant of from_path_str is merged into the descendant of to_path_str.
        """
        from_path = self.pathify(from_path_str)
        to_path = self.pathify(to_path_str)
        from_path.must_be_dir()
        to_path.must_be_dir()

        def merge_children(item: 'FSObject'):
            new_path = to_path.extend(item.path.name())
            # If there is a name conflict and both objects are directories, merge them together
            # If there is a name conflict but if both objects are not directories, the
            # from_path object takes precedence
            if isinstance(item, Directory) and new_path.exists() and isinstance(self[new_path], Directory):
                self.merge_dir(item.path, new_path)
            else:
                if new_path.exists():
                    self.rm(new_path)
                self._mv(item.path, new_path)
            return True

        self.walk(from_path, merge_children)
        self.rm(from_path)

    def __getitem__(self, path:'Path') -> 'FSObject':
        return self.fs[path]