# File System

## Description
The underlying data structure representing the file system is a dictionary with key/value pairs for every desendant of the root directory. Each key is a Path object and maps to either a File or Directory object. Having every descendant of root as a key in the dictionary (vs mirroring the actual tree structure) enables very fast lookup for any item, regardless of where it is in the structure. This trades fast single object operations for slower recursive directory operations, since those require updating/removing the paths for every child.

The "Path" class was created to simplify working with paths. Since paths are a fundamental concept in file systems and many operations require manipulating them in some way, creating a dedicated class allows us to centralize path-related functionality and simplify working with them across our codebase. User-facing functions take path strings for convenience, which are then turned into Path objects internally.

The File/Directory objects allow us to encapsulate any metadata and helper functions for common actions. Specifically, directories contain a list of their children.

## Assumptions
* Single object operations are more common than recursive actions
* Mimicing the unix filesystem is less important than simplifying some of the semantics (i.e. splitting moving and merging directories)
* Directory trees won't be deep enough to blow the stack (currently limited to 1000 segments)


## Getting Started
### Installing

1. Clone this project locally
2. `cd` into the `material` directory

### Running the filesystem
1. `python -i main.py`. This brings up repl that already has a FileSystem object with the root directory created.
2. Run commands by calling the relevant FileSystem method. ie. `fs.mkdir('foobar')`


### Supported commands

* `cwd` - Returns the current working directory
* `cd(path_str)` - Change the current working directory. Supports absolute and relative paths. Relative paths support .. and . semantics
* `ls(path)` - Returns the contents of the directory at the provided path
* `mkdir(path_str, recursive=False)` - Add a directory, recursive adds missing subdirectories
* `mkfile(path_str, recursive=False)` - Add a file, recursive adds missing subdirectories
* `read(path_str)` - Read the contents of the file at path
* `write(path_str, content, force=False)` - Write the passed in content to the file at path. 'force' will create the file if it doesn't already exist
* `rm(path_str, recursive)` - Removes the item at the given path_str if it exists. Deleting a non-empty directory will raise an error unless 'recursive=True'
* `find(match_name, path, recursive=False)` - Return any files/directories in the directory at path_str that are an exact match of the provided match_name. 'recursive' expands find to search across all descendants of the provided directory
* `mv(from_path_str, to_path_str, force=False)` - Move an item at from_path_str to to_path_str. If from_path_str refers to a directory, all descendants of the directory will also be moved. By default, an error will be raised if there is a name conflict unless 'force=True'
* `merge(from_path_str, to_path_str)` - Merge the directory at from_path_str into the directory at to_path_str. All descendants of from_path_str are also merged into to_path_str.
* `walk(path_str, action, recursive=False)` - Invoke the provided 'action' on the children of path
 
 ### Extras that were implemented
* Operations on paths, all functions take absolute and relative paths
* Walk a subtree
* Move and merge directories

## Future work
* Symlinks and hardlinks. This would be done by implementing new FSObjects for them and `Path.resolve()` would need to be modified to check if any path segment is a symlink or hardlink so that the "true" location is resolved.
* Move all the FSOBject classes and Path class out to their own files as more functionality is added
* Move tests into their own test directory
* Currently, there is one unit test that tests several cases for each file system command. Ideally, each of these cases should be broken out into their own test.
