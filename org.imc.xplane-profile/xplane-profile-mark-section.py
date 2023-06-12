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
import sys

import inkex
from inkex import Rectangle, FlowRoot, FlowPara, FlowRegion, TextElement, Tspan
from construction_layer_mgr import find_construction_layer, update_section_text_for_group, validate_section_structure


class XPlaneProfileMarkSection(inkex.EffectExtension):
    construction_layer: inkex.Layer

    def add_arguments(self, pars):
        pars.add_argument("--section_index", type=int, \
                          help="The index to generate for the first selected section, incremented for remainder")
        pars.add_argument("--section_z", type=float, \
                          help="The Z coordinate of the cross section, distance back in m, from the origin of the aircraft")

    def effect(self):
        # look for an existing construction layer or create a new one!
        self.construction_layer = find_construction_layer(self.svg)

        if len(self.svg.selection) > 1:
            inkex.utils.errormsg(
                "selection contains more than 1 element, marking them all with the same index and z coordinate is probably not what you intended!")

        for elem in self.svg.selection:
            # selected elements should be the group containing the profile path and center marker elements as descendants!
            if not isinstance(elem, inkex.Group):
                inkex.utils.errormsg(
                    "selection should contain only individual paths or shapes! The selected element with eid: {} is a {} skipping".format(elem.eid,
                                                                                                                                          elem.typename))
                break

            # add the section information tags
            elem.set("{uri://x-plane}profile-section", "true")
            elem.set("{uri://x-plane}profile-section-index", self.options.section_index)
            elem.set("{uri://x-plane}profile-section_z", self.options.section_z)

            # validate the element and update the construction layer texts
            validate_section_structure(self.svg, elem, True, self.construction_layer)


# standalone test command line paramenters: test\drawing.svg --output=test\drawing-out.svg --id=path249 --id=path287 --id=rect341 --id=path427
if __name__ == '__main__':
    # inkex.utils.errormsg("Args: {}".format(sys.argv))
    XPlaneProfileMarkSection().run()
