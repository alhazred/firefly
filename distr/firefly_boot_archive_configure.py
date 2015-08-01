#!/usr/bin/python
#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#

#
# Copyright (c) 2010, 2011, Oracle and/or its affiliates. All rights reserved.
# Copyright 2015 Nexenta Systems, Inc. All rights reserved.

""" boot_archive_configure - configure a populated boot archive area into a
usable boot archive.
"""
import os
import os.path
import shutil
import datetime

from osol_install.install_utils import dir_size
from solaris_install import DC_LABEL, run
from solaris_install.data_object.data_dict import DataObjectDict
from solaris_install.transfer.info import Software, Source, Destination, \
    CPIOSpec, Dir
from solaris_install.transfer.media_transfer import TRANSFER_ROOT, \
    INSTALL_TARGET_VAR
from solaris_install.engine import InstallEngine
from solaris_install.engine.checkpoint import AbstractCheckpoint as Checkpoint

# load a table of common unix cli calls
import solaris_install.distro_const.cli as cli
cli = cli.CLI()


class BootArchiveConfigure(Checkpoint):
    """ class to configure the boot archive
    """

    DEFAULT_ARG = {"image_type": None}

    def __init__(self, name, arg=DEFAULT_ARG):
        super(BootArchiveConfigure, self).__init__(name)
        self.image_type = arg.get("image_type",
                                  self.DEFAULT_ARG.get("image_type"))

        # instance attributes
        self.doc = None
        self.dc_dict = {}
        self.pkg_img_path = None
        self.ba_build = None

        # set the file_defaults to the path of this checkpoint/defaultfiles
        self.file_defaults = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "defaultfiles")

    def get_progress_estimate(self):
        """Returns an estimate of the time this checkpoint will take
        """
        return 20

    def configure_system(self):
        """ class method for the execution of various, isolated shell commands
        needed to configure the boot archive.
        """
        self.logger.info("preparing boot archive")

        # configure devices
        cmd = [cli.DEVFSADM, "-r", self.ba_build]
        run(cmd)

        # etc/dev/.devfsadm_dev.lock gets created every time
        # devfsadm is run. remove it since there's no point
        # in carrying it forward through to the image
        lockfile = os.path.join(self.ba_build, "etc/dev/.devfsadm_dev.lock")
        if os.path.exists(lockfile):
            self.logger.debug("removing devfsadm lock file")
            os.remove(lockfile)

        # Set a marker so that every boot is a reconfiguration boot
        cmd = [cli.TOUCH, os.path.join(self.ba_build, "reconfigure")]
        run(cmd)

	# go to the ba_build
        self.logger.debug("creating symlinks and mountpoints")
        os.chdir(self.ba_build)

        # create ./tmp.  mkdir and chmod have to be done seperately
        self.logger.debug("creating tmp dir and setting it to 01777")
        os.mkdir("tmp")
        os.chmod("tmp", 01777)

        # create ./proc
        self.logger.debug("creating proc directory")
        os.mkdir("proc")

        # create ./mnt
        self.logger.debug("creating mnt directory")
        os.mkdir("mnt")

        # create bin symlink to /usr/bin if needed
        self.logger.debug("checking for symlink of bin -> usr/bin")
        if not os.path.islink("bin"):
            os.symlink("usr/bin", "bin")

        # create mountpoints for misc and pkg zlibs
        self.logger.debug("creating mnt/misc and mnt/pkg mountpoints")
        #os.mkdir("mnt/misc", 0755)
        #os.mkdir("mnt/pkg", 0755)

        # create volume set id file, use system name + date for uniqueness
        with open(".volsetid", "w") as v:
            volsetid = os.uname()[1] + '-' + \
                       datetime.datetime.now().isoformat()
            self.logger.debug("setting .volsetid to %s" % volsetid)
            v.write(volsetid)

        # chmod it to 444 and set the ownership to root:root (0:0)
        os.chmod(".volsetid", 0444)
        os.chown(".volsetid", 0, 0)

        # create the file marking the image type (e.g. .autoinstall or
        # .livecd)
        self.logger.debug("creating image_type file")
        with open(self.image_type, "w"):
            pass

        # create .cdrom directory
        self.logger.debug("creating .cdrom directory")
        os.mkdir(".cdrom", 0755)

        # create opt symlink to mnt/misc/opt if needed
        #self.logger.debug("checking for symlink of opt -> mnt/misc/opt")
        #if not os.path.islink("opt"):
        #    os.symlink("mnt/misc/opt", "opt")

        tr_uninstall = CPIOSpec()
        tr_uninstall.action = CPIOSpec.UNINSTALL
        tr_uninstall.contents = ["opt"]

        root_tr_software_node = self.doc.persistent.get_descendants(
            name=TRANSFER_ROOT, class_type=Software, not_found_is_err=True)[0]
        root_tr_software_node.insert_children(tr_uninstall)

        # copy the SMF repository from pkg_image_path to ba_build
        #pkg_img_path_repo = os.path.join(self.pkg_img_path,
        #                                 "lib/svc/seed/nonglobal.db")
        #ba_build_repo = os.path.join(self.ba_build,
        #                             "etc/svc/repository.db")
        #shutil.copy2(pkg_img_path_repo, ba_build_repo)

	shutil.copy2("/opt/firefly/iso/nonglobal.db", self.ba_build + "/etc/svc/repository.db")	
	shutil.copy2("/opt/firefly/iso/nodename", self.ba_build + "/etc/")	
	shutil.copy2("/opt/firefly/iso/checkrpool", self.ba_build + "/usr/sbin/")
	shutil.copy2("/opt/firefly/iso/smf/console-login", self.ba_build + "/lib/svc/method/")
	shutil.copy2("/opt/firefly/iso/smf/fs-root", self.ba_build + "/lib/svc/method/")
	shutil.copy2("/opt/firefly/iso/smf/manifest-import", self.ba_build + "/lib/svc/method/")
	shutil.copy2("/opt/firefly/iso/rootpool", self.ba_build + "/usr/sbin/")	
	shutil.copy2("/opt/firefly/iso/sulogin", self.ba_build + "/etc/default/")
	shutil.copy2(self.pkg_img_path + "/usr/xpg4/bin/vi", self.ba_build + "/usr/bin/")
	shutil.copytree(self.pkg_img_path + "/usr/share/lib/keytables", self.ba_build + "/usr/share/lib/keytables")
	shutil.copytree(self.pkg_img_path + "/usr/share/lib/terminfo", self.ba_build + "/usr/share/lib/terminfo")	
	os.chdir(self.ba_build + "/sbin")		
 	os.unlink("sh")	
	os.symlink("../usr/bin/bash", "sh") 
	os.chdir(self.ba_build)


    def configure_symlinks(self):
        """ class method for the configuration of symlinks needed in the boot
        archive.
        """
        self.logger.debug("Creating additional symlinks in ramdisk")

        self.logger.debug("creating set of files in pkg_img_path:  %s" % \
                          self.pkg_img_path)

        # change to the pkg_img_path directory
        os.chdir(self.pkg_img_path)

        # walk /etc and /var in pkg_img_path and create a list of
        # directories
        pkg_img_dirs = []
        for rootdir in ["etc", "var"]:
            for root, dirs, files in os.walk(rootdir):
                for d in dirs:
                    pkg_img_dirs.append(os.path.join(root, d))

        # change to the boot_archive directory
        os.chdir(self.ba_build)

        # walk the pkg_img_dirs list and create each directory that doesn't
        # already exist.  Also, copy the directory permissions and metadata
        # to the new directory
        for d in pkg_img_dirs:
            ba_path = os.path.join(self.ba_build, d)
            pkg_path = os.path.join(self.pkg_img_path, d)

            # split the directory on / to verify parent directories exist
            dir_list = d.split("/")

            # keep a 'path' string for verification
            path = ""
            for subdir in dir_list:
                # extend path
                path = os.path.join(path, subdir)
                full_path = os.path.join(self.ba_build, path)

                # check to see if it exists and is not already a symlink
                if not os.path.exists(full_path) and \
                    not os.path.islink(full_path):

                    # create the directory
                    os.mkdir(os.path.join(self.ba_build, path))

                    # copy the metadata from pkg_image to boot_archive
                    shutil.copystat(os.path.join(self.pkg_img_path, path),
                                    os.path.join(self.ba_build, path))

                    # copy the uid/gid as well
                    pkg_statinfo = os.stat(os.path.join(self.pkg_img_path,
                                                        path))

                    os.chown(os.path.join(self.ba_build, path),
                             pkg_statinfo.st_uid, pkg_statinfo.st_gid)

        # now that the directory structure is created, create symlinks for
        # all the missing files in the boot_archive

        # change to the pkg_img_path directory
        os.chdir(self.pkg_img_path)

        # keep track of all the symlinks created
        misc_symlinks = []
        for rootdir in ["etc", "var"]:
            for root, dirs, files in os.walk(rootdir):
                for f in files:
                    pkg_path = os.path.join(self.pkg_img_path, root, f)

                    # skip symlinks
                    if os.path.islink(pkg_path):
                        continue

                    ba_path = os.path.join(self.ba_build, root, f)
                    if not os.path.exists(ba_path):
                        # the file is missing from the boot_archive so
                        # create a symlink to /mnt/misc/file/path
                        misc_path = os.path.join("/mnt/misc", root, f)

                        # save the cwd
                        cwd = os.getcwd()

                        # changedir to the dirname of the file
                        os.chdir(os.path.dirname(ba_path))

                        # create the symlink
                        os.symlink(misc_path, f)

                        os.chdir(cwd)

                        misc_symlinks.append(os.path.join(root, f))

        # We don't want readonly ttymon log in misc
        os.remove(os.path.join(self.ba_build,"var/saf/zsmon/log"))

        tr_uninstall = CPIOSpec()
        tr_uninstall.action = CPIOSpec.UNINSTALL
        tr_uninstall.contents = misc_symlinks

        # Add that into the software transfer list.  The list of files to
        # uninstall MUST go before the contents to be installed from /mnt/misc
        root_tr_software_node = self.doc.persistent.get_descendants(
            name=TRANSFER_ROOT, class_type=Software, not_found_is_err=True)[0]

        root_tr_software_node.insert_children(tr_uninstall)

        self.logger.debug(str(self.doc.persistent))

    def parse_doc(self):
        """ class method for parsing data object cache (DOC) objects for use by
        the checkpoint.
        """
        self.doc = InstallEngine.get_instance().data_object_cache
        self.dc_dict = self.doc.volatile.get_children(name=DC_LABEL,
            class_type=DataObjectDict)[0].data_dict

        try:
            self.pkg_img_path = self.dc_dict["pkg_img_path"]
            self.ba_build = self.dc_dict["ba_build"]
        except KeyError:
            raise RuntimeError("Error retrieving a value from the DOC")

    def add_root_transfer_to_doc(self):
        """ Adds the list of files of directories to be transferred
            to the DOC
        """
        if self.doc is None:
            self.doc = InstallEngine.get_instance().data_object_cache

        src_path = Dir("/")
        src = Source()
        src.insert_children(src_path)

        dst_path = Dir(INSTALL_TARGET_VAR)
        dst = Destination()
        dst.insert_children(dst_path)

        dot_node = CPIOSpec()
        dot_node.action = CPIOSpec.INSTALL
        dot_node.size = str(dir_size(os.path.join(self.ba_build, "")))
        dot_node.contents = ["."]

        usr_node = CPIOSpec()
        usr_node.action = CPIOSpec.INSTALL
        usr_node.size = str(dir_size(os.path.join(self.pkg_img_path, "usr")))
        usr_node.contents = ["usr"]

        dev_node = CPIOSpec()
        dev_node.action = CPIOSpec.INSTALL
        dev_node.size = str(dir_size(os.path.join(self.pkg_img_path, "dev")))
        dev_node.contents = ["dev"]

        software_node = Software(TRANSFER_ROOT, type="CPIO")
        software_node.insert_children([src, dst, dot_node, usr_node, dev_node])

        self.doc.persistent.insert_children(software_node)

        self.logger.debug(str(self.doc.persistent))

    def execute(self, dry_run=False):
        """ Primary execution method used by the Checkpoint parent class.
        dry_run is not used in DC
        """
        self.logger.info("=== Executing Boot Archive Configuration" + \
            " Checkpoint ===")

        self.parse_doc()

        self.add_root_transfer_to_doc()

        # configure various boot archive files
        self.configure_system()

        # configure various symlinks
        self.configure_symlinks()


class TextBootArchiveConfigure(BootArchiveConfigure, Checkpoint):
    """ TextBootArchiveConfigure - class to configure the boot archive
    directory specific to the text install media
    """

    DEFAULT_ARG = {"image_type": ".textinstall"}

    def __init__(self, name, arg=DEFAULT_ARG):
        """ constructor for class.
        image_type - string containing the image_type (.autoinstall, .livecd)
        """
        super(TextBootArchiveConfigure, self).__init__(name, arg)
        self.image_type = arg.get("image_type",
                                  self.DEFAULT_ARG.get("image_type"))
