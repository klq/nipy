#!/usr/bin/env python

def configuration(parent_package='',top_path=None):
    
    from numpy.distutils.misc_util import Configuration

    # We need this because lapack fffpy.a is linked to lapack, which can be a 
    # fortran library, and the linker needs this information.
    from numpy.distutils.system_info import get_info
    lapack_info = get_info('lapack_opt',0)
    
    config = Configuration('glm', parent_package, top_path)
    config.add_data_dir('tests')
    config.add_extension(
                'kalman',
                sources=['kalman.c'],
                libraries=['fffpy'],
                extra_info=lapack_info,
                )

    return config


if __name__ == '__main__':
    print 'This is the wrong setup.py file to run'

