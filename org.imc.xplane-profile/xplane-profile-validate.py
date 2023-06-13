#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) [YEAR] [YOUR NAME], [YOUR EMAIL]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
Description of this extension
"""

import inkex
from inkex.utils import errormsg
from construction_layer_mgr import find_construction_layer, find_sections_in_group


class XPlaneProfileValidate(inkex.EffectExtension):
    construction_layer: inkex.Layer

    """Please rename this class, don't keep it unnamed"""

    def add_arguments(self, pars):
        pars.add_argument("--scale-factor", type=float, help="Scale factor")
        pars.add_argument("--num-radii-per-side", type=int, help="The number of sample points to take per side")
        pars.add_argument("--acf-output-file", type=str, help="The number of sample points to take per side")

    def effect(self):
        # inkex.utils.errormsg("File:" + inkex.__file__)
        # inkex.utils.errormsg("Exe:" + sys.executable)
        # inkex.utils.errormsg("Path:" + str(sys.path))

        for elem in self.svg.selection:
            # look for an existing construction layer or create a new one!
            self.construction_layer = find_construction_layer(self.svg)

            style = {'fill': 'none', 'stroke': 'blue', 'stroke-width': '.1'}

            # selected element should be a group!
            if not isinstance(elem, inkex.Group):
                errormsg("selection should contain only groups! The selected element with eid: {} is a {} skipping".format(elem.eid, elem.typename))
                break

            # the group should be marked up as an x-plane:section or contain descendants marked up as such
            sections = find_sections_in_group(self.svg, elem, True, self.construction_layer)

            if len(sections) == 0:
                errormsg(
                    "The selected element with eid: {} is not marked as an x-plane section, nor does it contain any".format(elem.eid, elem.typename))
                break

            # iterate through each section element
            indx = 0
            for section in sections:
                (valid, section_indx, section_z, profile_el, center_el) = section

                if not valid:
                    errormsg(
                        "The selected element, with eid: {}, is not a validly marked up section check the index, z, center and profile markup!".format(
                            elem.eid))
                    break


# standalone test command line paramenters: test\drawing.svg --output=test\drawing-out.svg --id=path249 --id=path287 --id=rect341 --id=path427
if __name__ == '__main__':
    XPlaneProfileValidate().run()
