#! /usr/bin/env python
import os
import rpm
import django
import sys
from kobo.rpmlib import parse_nvra
from optparse import OptionParser
import logging
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pdc.settings")
django.setup()

from pdc.apps.common.hacks import add_returning
from pdc.apps.package.models import Dependency, RPM
from django.db import transaction, connection

RPM_EXTENSION = ('.rpm', )
SRC_RPM_EXTENSION = ('.src.rpm', )
RPM_SOURCE_DIR = "/mnt/redhat/released"
BREW_ROOT_DIR = "/mnt/redhat/brewroot"
PROVIDES = 'provides'
REQUIRES = 'requires'
OBSOLETES = 'obsoletes'
CONFLICTS = 'conflicts'
RECOMMENDS = 'recommends'
SUGGESTS = 'suggests'
DEPENDENCY_TYPE_LIST = (PROVIDES, REQUIRES, OBSOLETES, CONFLICTS, RECOMMENDS, SUGGESTS)
BATCH_NUM = 1000
DEPENDENCY_TO_INT_DICT = {PROVIDES: Dependency.PROVIDES,
                          REQUIRES: Dependency.REQUIRES,
                          OBSOLETES: Dependency.OBSOLETES,
                          CONFLICTS: Dependency.CONFLICTS,
                          RECOMMENDS: Dependency.RECOMMENDS,
                          SUGGESTS: Dependency.SUGGESTS}

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
hdlr = logging.FileHandler(__file__ + '.log')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)


def is_qualified_file(filename):
    return filename.endswith(RPM_EXTENSION)


def collect_rpm_files_from_dir(dir_str):
    result = {}
    for root, sub_dirs, files in os.walk(dir_str):
        for filename in files:
            if is_qualified_file(filename):
                file_path = os.path.join(root, filename)
                result[filename] = file_path
    return result


def get_qualified_file_info(source_dir, brew_dir):
    source_dir_rpm_info = collect_rpm_files_from_dir(source_dir)
    brew_dir_rpm_info = collect_rpm_files_from_dir(brew_dir)
    unqualified_rpm = set(source_dir_rpm_info.keys()) - set(brew_dir_rpm_info.keys())
    for key in unqualified_rpm:
        source_dir_rpm_info.pop(key)
    return source_dir_rpm_info


def rpm_is_src(hdr, file_path):
    # .src.rpm's hdr[rpm.RPMTAG_ARCH] may not be 'src'
    return file_path.endswith(SRC_RPM_EXTENSION) or hdr[rpm.RPMTAG_ARCH] == 'src'


def fill_rpm_basic_info(hdr, rpm_name, rpm_path, rpm_name_to_path_dict, is_src_rpm):
    # It will return like
    # {'src': False, 'name': 'patternfly1', 'epoch': '', 'version': '1.0.5', 'release': '4.el7eng', 'arch': 'noarch',
    # 'filename': gtk-vnc2-0.5.2-7.el7.x86_64.rpm}
    result = parse_nvra(hdr[rpm.RPMTAG_NEVRA])
    result['srpm_name'] = ''
    result['srpm_nevra'] = None
    result['filename'] = rpm_name
    if not result['epoch']:
        result['epoch'] = 0
    if rpm_is_src(hdr, rpm_path) or is_src_rpm:
        # srpm_nevra should be empty if and only if arch is src.
        result['srpm_name'] = result["name"]
        result['srpm_nevra'] = None
        result['src'] = True
        result['arch'] = 'src'
    else:
        # Get srpm information
        source_rpm = hdr[rpm.RPMTAG_SOURCERPM]
        if source_rpm in rpm_name_to_path_dict:
            # mark as src rpm to prevent dead loop
            srpm_info = parse_rpm(source_rpm, rpm_name_to_path_dict[source_rpm], rpm_name_to_path_dict, True)
            result['srpm_name'] = srpm_info["name"]
            result['srpm_nevra'] = "%s-%s:%s-%s.%s" % (srpm_info['name'], srpm_info['epoch'],
                                                       srpm_info['version'], srpm_info['release'], srpm_info['arch'])
    return result


def parse_rpm(rpm_name, rpm_path, rpm_name_to_path_dict, is_src_rpm=None):
    ts = rpm.ts()
    fdno = os.open(rpm_path, os.O_RDONLY)
    try:
        hdr = ts.hdrFromFdno(fdno)
    except rpm.error:
        fdno = os.open(rpm_path, os.O_RDONLY)
        ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
        hdr = ts.hdrFromFdno(fdno)
    os.close(fdno)
    # It will return like
    # {'src': False, 'name': 'patternfly1', 'epoch': 0, 'version': '1.0.5', 'release': '4.el7eng', 'arch': 'noarch'}
    result = fill_rpm_basic_info(hdr, rpm_name, rpm_path, rpm_name_to_path_dict, is_src_rpm)
    # Dependencies
    result[REQUIRES] = hdr[rpm.RPMTAG_REQUIRENEVRS]
    result[PROVIDES] = hdr[rpm.RPMTAG_PROVIDENEVRS]
    result[OBSOLETES] = hdr[rpm.RPMTAG_OBSOLETENEVRS]
    result[CONFLICTS] = hdr[rpm.RPMTAG_CONFLICTNEVRS]
    result[RECOMMENDS] = hdr[rpm.RPMTAG_RECOMMENDNEVRS]
    result[SUGGESTS] = hdr[rpm.RPMTAG_SUGGESTNEVRS]
    return result


def check_or_save_rpm_basic_info(rpm_info, cursor):
    """If exists, return id, or insert and return id."""
    select_sql = """SELECT id FROM %s WHERE name=%%(name)s AND epoch=%%(epoch)s AND version=%%(version)s AND
                    release=%%(release)s AND arch=%%(arch)s""" % RPM._meta.db_table
    cursor.execute(select_sql, rpm_info)
    result = cursor.fetchone()
    if not result:
        insert_sql = """INSERT INTO %s (name, epoch, version, release, arch, srpm_name, srpm_nevra, filename) VALUES
                    (%%(name)s, %%(epoch)s, %%(version)s, %%(release)s, %%(arch)s, %%(srpm_name)s,
                    %%(srpm_nevra)s, %%(filename)s)""" % RPM._meta.db_table
        insert_sql = add_returning(insert_sql)
        cursor.execute(insert_sql, rpm_info)
        result = cursor.fetchone()
    return result[0]


def remove_rpm_dependency_info(rpm_id, cursor):
    remove_sql = """DELETE FROM %s WHERE rpm_id=%%s""" % Dependency._meta.db_table
    cursor.execute(remove_sql, (rpm_id,))


def save_dependency_of_one_type(rpm_info, dependency_type, rpm_id, cursor):
    if dependency_type not in rpm_info or not rpm_info[dependency_type]:
        return
    insert_sql = """INSERT INTO %s (type, name, version, comparison, rpm_id)
                    VALUES(%%(type)s, %%(name)s, %%(version)s, %%(op)s, %%(rpm_id)s)""" % Dependency._meta.db_table
    for dependency_value in rpm_info[dependency_type]:
        # dependency_value would be like 'rpmlib(FileDigests) <= 4.6.0-1' OR 'pkgconfig(libecpg)'
        m = Dependency.DEPENDENCY_PARSER.match(dependency_value)
        if m:
            param_dict = m.groupdict()
            param_dict.update({'rpm_id': rpm_id, 'type': DEPENDENCY_TO_INT_DICT[dependency_type]})
            cursor.execute(insert_sql, param_dict)
        else:
            logger.debug("RPM with id %d has invalid dependency value %s. Skipped this value",
                         rpm_id, dependency_value)


def save_rpm_dependency_info(rpm_id, rpm_info, cursor):
    remove_rpm_dependency_info(rpm_id, cursor)
    for dependency_type in DEPENDENCY_TYPE_LIST:
        save_dependency_of_one_type(rpm_info, dependency_type, rpm_id, cursor)


def parse_and_save_rpms(rpm_name_to_path_dict):
    cursor = connection.cursor()
    count = 0
    for rpm_name, rpm_path in rpm_name_to_path_dict.iteritems():
        rpm_info = parse_rpm(rpm_name, rpm_path, rpm_name_to_path_dict)
        rpm_id = check_or_save_rpm_basic_info(rpm_info, cursor)
        save_rpm_dependency_info(rpm_id, rpm_info, cursor)

        count += 1
        if count % BATCH_NUM == 0:
            transaction.commit()
            logger.info("Already saved %d RPMs' information.", count)

    transaction.commit()
    logger.info("Totally saved %d RPMs' information.", count)
    transaction.set_autocommit(True)
    logger.info("VACUUM ANALYZING...")
    cursor.execute('VACUUM ANALYZE')


def main(source_dir, brew_dir):
    rpm_name_to_path_dict = get_qualified_file_info(source_dir, brew_dir)
    parse_and_save_rpms(rpm_name_to_path_dict)


if __name__ == '__main__':
    usage = """%prog -d <source directory> -b <brew root directory>"""
    parser = OptionParser(usage)
    parser.add_option("-d", "--directory", help="the source directory", dest='source_dir',
                      default=RPM_SOURCE_DIR)
    parser.add_option("-b", "--brewroot", help="the brew root directory", dest='brew_dir',
                      default=BREW_ROOT_DIR)
    options, args = parser.parse_args()

    if not os.path.isdir(options.source_dir):
        parser.error("Source directory doesn't exist")
    if not os.path.isdir(options.brew_dir):
        parser.error("Brew root directory doesn't exist")

    autocommit = transaction.get_autocommit()
    transaction.set_autocommit(False)
    main(options.source_dir, options.brew_dir)
    transaction.set_autocommit(autocommit)
