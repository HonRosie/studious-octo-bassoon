import unittest
from FileSystem import FileSystem
from FileSystemExceptions import (
    ActionNotAllowed,
    DirectoryNotEmpty,
    InvalidMove,
    PathDoesNotExistError,
    PathNotFile
)

class TestDirectoryFunctions(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()

    def test_add_directory(self):
        fs = self.fs
        fs.mkdir('/foo')
        contents = fs.ls()
        self.assertEqual(contents, ['foo'])

        fs.mkdir('/foo/bar/baz', recursive=True)
        contents = fs.ls('/foo')
        self.assertEqual(contents, ['bar'])
        contents = fs.ls('/foo/bar')
        self.assertEqual(contents, ['baz'])

    def test_rm(self):
        fs = self.fs
        with self.assertRaises(ActionNotAllowed):
            fs.rm('/')

        fs.mkdir('/foo/bar/baz/bat', recursive=True)
        fs.mkfile('fileA')

        with self.assertRaises(PathDoesNotExistError):
            fs.rm('/bar')

        with self.assertRaises(DirectoryNotEmpty):
            fs.rm('/foo/bar')

        fs.rm('/foo/bar/baz', recursive=True)
        contents = fs.ls('/foo/bar')
        self.assertEqual(contents, [])

        fs.rm('/foo/bar')
        contents = fs.ls('foo')
        self.assertEqual(contents, [])

        fs.rm('fileA')
        contents = fs.ls()
        self.assertEqual(contents, ['foo'])


    def test_touch(self):
        fs = self.fs
        fs.mkdir('/foo')
        fs.mkfile('fileA')

        contents = fs.ls('/')
        self.assertEqual(contents, ['foo', 'fileA'])

        fs.mkfile('/bar/fileB', recursive=True)

        contents = fs.ls('/bar')
        self.assertEqual(contents, ['fileB'])

        with self.assertRaises(Exception):
            fs.mkfile('/baz/fileC')

        with self.assertRaises(Exception):
            fs.mkfile('fileA')

    def test_read_write(self):
        fs = self.fs

        with self.assertRaises(PathDoesNotExistError):
            fs.write('/fileC', 'hello world')

        fs.mkdir('/foo')
        with self.assertRaises(PathNotFile):
            fs.write('/foo', 'hello world')

        with self.assertRaises(PathDoesNotExistError):
            fs.read('/fileC')

        with self.assertRaises(PathNotFile):
            fs.read('/foo')

        fs.mkfile('fileC')
        fs.write('fileC', 'hello world')
        self.assertEqual(fs.read('fileC'), 'hello world')

        fs.write('/bar/fileD', 'hello world 2', force=True)
        self.assertEqual(fs.read('/bar/fileD'), 'hello world 2')


    def test_get_cwd(self):
        fs = self.fs
        self.assertEqual(fs.cwd(), '/')

    def test_cd(self):
        fs = self.fs
        with self.assertRaises(Exception):
            fs.cd('/foo ')

        fs.mkdir('/foo/bar/baz', recursive=True)
        fs.mkdir('/foo/foobar', recursive=True)
        fs.cd('/foo/bar')
        curr_dir = fs.cwd()
        self.assertEqual(curr_dir, '/foo/bar')

        fs.cd('/')
        curr_dir = fs.cwd()
        self.assertEqual(curr_dir, '/')

        fs.cd('/foo/bar')
        fs.cd('../foobar')
        curr_dir = fs.cwd()
        self.assertEqual(curr_dir, '/foo/foobar')


    def test_ls(self):
        fs = self.fs
        fs.mkdir('/foo/bar', recursive=True)
        fs.mkdir('/foo/foobar', recursive=True)

        contents = fs.ls()
        self.assertEqual(contents, ['foo'])
        
        contents = fs.ls('foo')
        self.assertEqual(contents, ['bar', 'foobar'])

        contents = fs.ls('/foo/bar')
        self.assertEqual(contents, [])

    def test_find(self):
        fs = self.fs
        fs.mkdir('/foo', recursive=True)
        contents = fs.find('foo')
        self.assertEqual(contents, ['/foo'])

        fs.mkfile('/bar.txt')
        fs.mkfile('/foo/bar.txt')

        contents = fs.find('bar.txt')
        self.assertEqual(contents, ['/bar.txt'])

        contents = fs.find('bar.txt', recursive=True)
        self.assertEqual(contents, ['/foo/bar.txt', '/bar.txt'])
        # TODO change assertEqal to assertCountEqual

    def test_mv(self):
        fs = self.fs

        # Rename file
        fs.mkfile('/bar.txt')
        fs.mv('/bar.txt', '/baz.txt')

        self.assertCountEqual(fs.ls('/'), ['baz.txt'])

        # Rename dir
        fs.mkdir('/foo')
        fs.mkfile('/foo/hello.txt')
        fs.mv('/foo', '/foobar')
        self.assertCountEqual(fs.ls('/'), ['baz.txt', 'foobar'])
        self.assertCountEqual(fs.ls('/foobar'), ['hello.txt'])

        # Overwrite file
        fs.write('/baz.txt', 'hello baz')
        fs.mkfile('/bar.txt')
        fs.write('/bar.txt', 'hello bar')
        with self.assertRaises(InvalidMove):
            fs.mv('/bar.txt', '/baz.txt')
        fs.mv('/bar.txt', '/baz.txt', force=True)
        self.assertCountEqual(fs.ls('/'), ['foobar', 'baz.txt'])
        self.assertEqual(fs.read('/baz.txt'), 'hello bar')

        # Move directory into directory
        fs.mkdir('/bar')
        fs.mkfile('/bar/bar.txt')
        fs.mv('/bar', '/foobar')
        self.assertCountEqual(fs.ls('/'), ['baz.txt', 'foobar'])
        self.assertCountEqual(fs.ls('/foobar'), ['bar', 'hello.txt'])
        self.assertCountEqual(fs.ls('/foobar/bar'), ['bar.txt'])

    def test_merge(self):
        fs = self.fs

        fs.mkdir('/foo')
        fs.mkdir('/foo/bar')
        fs.mkfile('/foo/bar/foo_bar.txt')
        fs.mkfile('/foo/foo.txt')
        fs.mkfile('/foo/same.txt')
        fs.write('/foo/same.txt', 'foo_same')

        fs.mkdir('/hello')
        fs.mkdir('/hello/bar')
        fs.mkfile('/hello/bar/hello_bar.txt')
        fs.mkfile('/hello/hello.txt')
        fs.mkfile('/hello/same.txt')
        fs.write('/hello/same.txt', 'hello_same')

        fs.merge_dir('/foo', '/hello')
        self.assertCountEqual(fs.ls('/'), ['hello'])
        self.assertCountEqual(fs.ls('/hello'), ['bar', 'hello.txt', 'foo.txt', 'same.txt'])
        self.assertCountEqual(fs.ls('/hello/bar'), ['foo_bar.txt', 'hello_bar.txt'])
        self.assertEqual(fs.read('/hello/same.txt'), 'foo_same')

if __name__ == '__main__':
    unittest.main()
