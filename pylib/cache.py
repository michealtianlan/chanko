# Copyright (c) 2010 Alon Swartz <alon@turnkeylinux.org> - all rights reserved

import os
import re
import commands


class Cache:
    """ class for controlling chanko container cache """
    
    def __init__(self, paths, options):
        self.paths = paths
        self.options = options

    def parse_uris(self, raw):
        uris = []
        for uri in raw.split("\n"):
            m = re.match("\'(.*)\' (.*) 0", uri)
            if m and not re.match("(.*)Translation(.*)", m.group(1)):
                uris.append([m.group(1), m.group(2)])
        return uris
    
    def download_uris(self, uris):
        #this whole thing will be re-written...
        for url, filename in uris:
            if os.path.basename(url) == "Release.gpg":
                #reminder: get release.gpg and check integrity
                url2 = re.sub(".gpg", "", url)
                filename2 = re.sub(".gpg", "", filename)
                out = self.paths["Dir::State::Lists"] + "/" + filename2
                os.system("curl -L -f %s -o %s" % (url2, out))

        for url, filename in uris:
            if os.path.basename(url) == "Packages.bz2":
                out = self.paths["Dir::State::Lists"] + "/" + filename
                if os.path.isfile(out + ".bz2"):
                    md5 = commands.getoutput("md5sum %s | awk '{print $1}'" % (out + ".bz2"))
                    m = re.match("(.*)_(.*)_(.*)_Packages", filename)
                    if m:
                        release = self.paths["Dir::State::Lists"] + "/" + m.group(1) + "_Release"
                        err, out = commands.getstatusoutput("grep -q %s %s" % (md5, release))
                        if not err:
                            continue

                #check integrity of download
                os.system("curl -L -f %s -o %s.bz2" % (url, out))
                os.system("bzcat %s.bz2 > %s" % (out, out))
    
    def generate(self):
        os.system("apt-cache %s gencaches" % self.options)
    
    def refresh(self):
        if re.match("(.*)remote", self.paths["Dir::Cache"]):
            raw = commands.getoutput("apt-get %s --print-uris update" % self.options)
            uris = self.parse_uris(raw)
            self.download_uris(uris)
            
        else:
            # reminder: arch
            pkgs_file = self.paths["Dir::State::Lists"] + "/_dists_local_debs_binary-i386_Packages"
            os.system("apt-ftparchive packages %s > %s" % (
                      self.paths["Dir::Cache::Archives"], pkgs_file))

        self.generate()


