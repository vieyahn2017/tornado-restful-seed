from tornado import gen
from tornado import process


@gen.coroutine
def rm(file_path):
    """删除文件"""
    cmd = ['rm', file_path]
    ps = process.Subprocess(cmd)
    result = yield ps.wait_for_exit(raise_error=False)
    raise gen.Return(result == 0)


@gen.coroutine
def mv(from_path, to_path):
    """移动文件"""
    cmd = ['mv', from_path, to_path]
    ps = process.Subprocess(cmd)
    result = yield ps.wait_for_exit(raise_error=False)
    raise gen.Return(result == 0)
